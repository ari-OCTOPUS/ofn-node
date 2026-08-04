"""Authentication: forged signatures, stale blobs, replay, and cross-tenant tokens."""

from __future__ import annotations

import hashlib
import hmac
import unittest

from ofn.kernel.auth import (
    DEFAULT_MAX_AGE_S, AuthError, ReplayGuard, data_check_string, issue_session,
    parse_and_verify, verify_init_data, verify_session,
)

BOT_TOKEN = "123456:AAH-fake-bot-token-for-tests"
SECRET = "session-signing-secret"
NOW = 1_785_000_000


def sign(fields: dict[str, str], token: str = BOT_TOKEN) -> dict[str, str]:
    """Produce a correctly signed blob, the way the platform would."""
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, data_check_string(fields).encode(),
                      hashlib.sha256).hexdigest()
    return {**fields, "hash": digest}


def good_fields(auth_date: int = NOW, uid: int = 777) -> dict[str, str]:
    return {
        "auth_date": str(auth_date),
        "query_id": "AAxyz",
        "user": f'{{"id":{uid},"first_name":"P","username":"partner"}}',
    }


class TestInitDataVerification(unittest.TestCase):
    def test_valid_blob_passes(self):
        u = verify_init_data(sign(good_fields()), BOT_TOKEN, now_epoch_s=NOW)
        self.assertEqual(u.user_id, "777")
        self.assertEqual(u.username, "partner")

    def test_forged_hash_is_rejected(self):
        f = sign(good_fields())
        f["hash"] = "0" * 64
        with self.assertRaises(AuthError):
            verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW)

    def test_tampering_with_a_field_invalidates_it(self):
        f = sign(good_fields())
        f["user"] = '{"id":999,"username":"attacker"}'
        with self.assertRaises(AuthError):
            verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW)

    def test_signature_from_a_different_bot_token_fails(self):
        f = sign(good_fields(), token="999:different-token")
        with self.assertRaises(AuthError):
            verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW)

    def test_missing_hash_is_rejected(self):
        with self.assertRaises(AuthError):
            verify_init_data(good_fields(), BOT_TOKEN, now_epoch_s=NOW)

    def test_stale_blob_is_rejected(self):
        f = sign(good_fields(auth_date=NOW - DEFAULT_MAX_AGE_S - 1))
        with self.assertRaises(AuthError):
            verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW)

    def test_blob_inside_the_window_is_accepted(self):
        f = sign(good_fields(auth_date=NOW - DEFAULT_MAX_AGE_S + 5))
        self.assertEqual(verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW).user_id,
                         "777")

    def test_future_dated_blob_is_rejected(self):
        """A board with no battery clock makes this ambiguous; we still refuse."""
        f = sign(good_fields(auth_date=NOW + 3600))
        with self.assertRaises(AuthError):
            verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW)

    def test_small_clock_skew_is_tolerated(self):
        f = sign(good_fields(auth_date=NOW + 30))
        self.assertTrue(verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW))

    def test_missing_bot_token_fails_closed(self):
        with self.assertRaises(AuthError):
            verify_init_data(sign(good_fields()), "", now_epoch_s=NOW)

    def test_signature_field_is_excluded_from_the_check_string(self):
        """A third-party verification field must not change our computation."""
        base = good_fields()
        signed = sign(base)
        signed["signature"] = "unrelated-ed25519-value"
        self.assertTrue(verify_init_data(signed, BOT_TOKEN, now_epoch_s=NOW))

    def test_error_message_does_not_leak_which_check_failed(self):
        forged = sign(good_fields()); forged["hash"] = "0" * 64
        stale = sign(good_fields(auth_date=NOW - 99999))
        msgs = set()
        for f in (forged, stale):
            try:
                verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW)
            except AuthError as e:
                msgs.add(str(e))
        self.assertEqual(len(msgs), 1, "distinct messages give an oracle")

    def test_parse_and_verify_round_trip(self):
        f = sign(good_fields())
        raw = "&".join(f"{k}={v}" for k, v in f.items())
        self.assertEqual(parse_and_verify(raw, BOT_TOKEN, now_epoch_s=NOW).user_id,
                         "777")

    def test_malformed_raw_is_rejected(self):
        with self.assertRaises(AuthError):
            parse_and_verify("no-equals-sign", BOT_TOKEN, now_epoch_s=NOW)

    def test_user_without_id_is_rejected(self):
        f = sign({"auth_date": str(NOW), "user": '{"first_name":"P"}'})
        with self.assertRaises(AuthError):
            verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW)


class TestSessionTokens(unittest.TestCase):
    def test_round_trip(self):
        t = issue_session("ziman", "777", SECRET, now_epoch_s=NOW)
        s = verify_session(t, SECRET, now_epoch_s=NOW + 10)
        self.assertEqual(s.tenant, "ziman")
        self.assertEqual(s.user_id, "777")

    def test_expired_token_rejected(self):
        t = issue_session("ziman", "777", SECRET, now_epoch_s=NOW, ttl_s=60)
        with self.assertRaises(AuthError):
            verify_session(t, SECRET, now_epoch_s=NOW + 61)

    def test_tampered_tenant_is_rejected(self):
        """A token minted for one leg must not work against a sibling."""
        t = issue_session("ziman", "777", SECRET, now_epoch_s=NOW)
        forged = t.replace("ziman", "lead", 1)
        with self.assertRaises(AuthError):
            verify_session(forged, SECRET, now_epoch_s=NOW)

    def test_tampered_user_is_rejected(self):
        t = issue_session("ziman", "777", SECRET, now_epoch_s=NOW)
        with self.assertRaises(AuthError):
            verify_session(t.replace("777", "888", 1), SECRET, now_epoch_s=NOW)

    def test_extended_expiry_is_rejected(self):
        t = issue_session("ziman", "777", SECRET, now_epoch_s=NOW, ttl_s=60)
        tenant, uid, iat, exp, sig = t.split(".")
        forged = f"{tenant}.{uid}.{iat}.{int(exp) + 999999}.{sig}"
        with self.assertRaises(AuthError):
            verify_session(forged, SECRET, now_epoch_s=NOW)

    def test_wrong_secret_is_rejected(self):
        t = issue_session("ziman", "777", SECRET, now_epoch_s=NOW)
        with self.assertRaises(AuthError):
            verify_session(t, "other-secret", now_epoch_s=NOW)

    def test_garbage_shapes_rejected(self):
        for bad in ["", "a.b.c", "a.b.c.d.e.f", "...."]:
            with self.subTest(token=bad), self.assertRaises(AuthError):
                verify_session(bad, SECRET, now_epoch_s=NOW)

    def test_subject_must_be_safe(self):
        for bad in ["../etc", "a b", "x" * 100, ""]:
            with self.subTest(tenant=bad), self.assertRaises(AuthError):
                issue_session(bad, "777", SECRET, now_epoch_s=NOW)

    def test_missing_secret_fails_closed(self):
        with self.assertRaises(AuthError):
            issue_session("ziman", "777", "", now_epoch_s=NOW)
        with self.assertRaises(AuthError):
            verify_session("a.b.1.2.c", "", now_epoch_s=NOW)


class TestReplayGuard(unittest.TestCase):
    def test_same_blob_twice_is_refused(self):
        g = ReplayGuard()
        g.check_and_remember("digest-1", NOW)
        with self.assertRaises(AuthError):
            g.check_and_remember("digest-1", NOW)

    def test_different_blobs_are_fine(self):
        g = ReplayGuard()
        g.check_and_remember("d1", NOW)
        g.check_and_remember("d2", NOW)
        self.assertEqual(len(g), 2)

    def test_entries_expire_and_the_guard_stays_small(self):
        g = ReplayGuard(window_s=100)
        for i in range(50):
            g.check_and_remember(f"d{i}", NOW)
        g.check_and_remember("later", NOW + 200)
        self.assertEqual(len(g), 1)

    def test_expired_digest_may_be_reused(self):
        """Not a weakness: the blob itself has already failed freshness by then."""
        g = ReplayGuard(window_s=100)
        g.check_and_remember("d", NOW)
        g.check_and_remember("d", NOW + 500)


if __name__ == "__main__":
    unittest.main()
