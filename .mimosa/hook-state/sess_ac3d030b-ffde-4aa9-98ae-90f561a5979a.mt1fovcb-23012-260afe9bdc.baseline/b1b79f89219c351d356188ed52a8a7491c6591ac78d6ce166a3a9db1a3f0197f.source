"""The partner door.

Verifying a Telegram signature proves that *a* Telegram account opened the
app. It does not prove it is the account this business belongs to — the
platform signs for every user alive. Before this list existed, anyone who
found the bot could write to the business.

These tests exist to keep it that way round: the list is the door, an empty
list is a locked door, and revoking somebody takes effect on the next
request rather than whenever their session felt like expiring.
"""

import hashlib
import hmac
import json
import unittest
import urllib.parse

from ofn.adapters.http_api import ApiApp, HostMap
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.tenancy import TenantRegistry

NOW = 1_785_000_000
SECRET = "session-secret"
TOKEN_Z = "111:ziman-bot"
TOKEN_OWNER = "999:owner-bot"
MALIHEH = "424242"
STRANGER = "808080"
ARI = "5001"


def init_data(token: str, uid: str) -> str:
    fields = {"auth_date": str(NOW),
              "user": f'{{"id":{uid},"username":"u{uid}"}}'}
    check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(fields)


def app(partners):
    packs = {"ziman": PackSpec(tenant=TenantId("ziman"),
                              capacity_units_per_week=6)}
    return ApiApp(
        TenantRegistry(packs),
        HostMap(tenants={"z.test": "ziman"}, owner_host="panel.test"),
        bot_tokens={"ziman": TOKEN_Z, "__owner__": TOKEN_OWNER},
        session_secret=SECRET,
        owner_user_ids=[ARI],
        partner_user_ids=partners,
        now=lambda: NOW,
        questions_for=lambda s, u: [{"id": "q1", "text": "؟"}],
        status_for=lambda s: {"ok": True},
    )


def launch(a, uid, token=TOKEN_Z, host="z.test"):
    return a.handle("POST", "/api/v1/auth/session", {"host": host},
                    json.dumps({"init_data": init_data(token, uid)}).encode())


def call(a, session, path="/api/v1/questions", host="z.test"):
    return a.handle("GET", path,
                    {"host": host, "authorization": "Bearer " + session}, b"")


class TestTheDoor(unittest.TestCase):
    def test_the_listed_partner_gets_in(self):
        r = launch(app({"ziman": [MALIHEH]}), MALIHEH)
        self.assertEqual(r.status, 200)
        self.assertIn("session", r.body)

    def test_a_stranger_with_a_perfectly_valid_signature_is_refused(self):
        # The whole hole, in one test. This signature is genuine — Telegram
        # really did sign it — and it still must not get in.
        r = launch(app({"ziman": [MALIHEH]}), STRANGER)
        self.assertEqual(r.status, 403)

    def test_empty_allowlist_means_nobody_not_everybody(self):
        for partners in ({"ziman": []}, {}, None):
            with self.subTest(partners=partners):
                self.assertEqual(launch(app(partners), MALIHEH).status, 403)

    def test_owner_is_not_admitted_to_a_partner_shell_by_being_owner(self):
        # Owner-ness is a property of the owner host, not a master key.
        self.assertEqual(launch(app({"ziman": []}), ARI).status, 403)

    def test_a_forged_signature_is_401_before_the_list_is_consulted(self):
        # Order matters: an unsigned caller must not learn whether the id it
        # guessed happens to be on the list.
        a = app({"ziman": [MALIHEH]})
        blob = init_data("222:not-the-bot", MALIHEH)
        r = a.handle("POST", "/api/v1/auth/session", {"host": "z.test"},
                     json.dumps({"init_data": blob}).encode())
        self.assertEqual(r.status, 401)


class TestRevocationIsImmediate(unittest.TestCase):
    def test_a_live_session_stops_working_once_delisted(self):
        session = launch(app({"ziman": [MALIHEH]}), MALIHEH).body["session"]
        # Same signed session, presented to a node that no longer lists her.
        self.assertEqual(call(app({"ziman": []}), session).status, 401)

    def test_a_session_still_works_while_listed(self):
        a = app({"ziman": [MALIHEH]})
        session = launch(a, MALIHEH).body["session"]
        self.assertEqual(call(a, session).status, 200)

    def test_one_partners_session_is_not_anothers(self):
        a = app({"ziman": [MALIHEH, STRANGER]})
        session = launch(a, STRANGER).body["session"]
        # Both are admitted here, so this is only about the session binding.
        self.assertEqual(call(a, session).status, 200)


class TestRoles(unittest.TestCase):
    def test_partner_may_not_reach_the_owner_surface(self):
        a = app({"ziman": [MALIHEH]})
        session = launch(a, MALIHEH).body["session"]
        for path in ("/api/v1/owner/status", "/api/v1/owner/events",
                     "/api/v1/queue"):
            with self.subTest(path=path):
                r = call(a, session, path=path, host="panel.test")
                self.assertIn(r.status, (401, 403, 404))

    def test_principal_role_names_which_side_of_the_door(self):
        from ofn.adapters.http_api import Principal
        self.assertEqual(Principal(TenantId("ziman"), MALIHEH).role, "partner")
        self.assertEqual(Principal(TenantId("ziman"), ARI, is_owner=True).role, "owner")


if __name__ == "__main__":
    unittest.main()


class TestFailureReasonIsForTheOperatorOnly(unittest.TestCase):
    """"Login does not work" should be answerable from the journal.

    The uniform 401 body stays uniform — an attacker learning that the
    signature was fine but the clock was off is a free oracle. The operator
    gets a named reason, and it never rides along in the response.
    """

    def test_a_reason_is_attached_for_the_journal(self):
        a = app({"ziman": [MALIHEH]})
        r = a.handle("POST", "/api/v1/auth/session", {"host": "z.test"},
                     json.dumps({"init_data": init_data("222:other-bot",
                                                        MALIHEH)}).encode())
        self.assertEqual(r.status, 401)
        # The reason may carry a probe suffix naming which decode/exclude
        # combination the platform actually signed.
        self.assertTrue(r.headers.get("X-OFN-Auth-Reason", "")
                        .startswith("signature_mismatch"))

    def test_the_body_says_nothing_beyond_unauthorised(self):
        a = app({"ziman": [MALIHEH]})
        r = a.handle("POST", "/api/v1/auth/session", {"host": "z.test"},
                     json.dumps({"init_data": init_data("222:other-bot",
                                                        MALIHEH)}).encode())
        self.assertEqual(r.body, {"error": "unauthorised"})

    def test_reasons_carry_no_identity(self):
        from ofn.kernel.auth import AuthError, verify_init_data
        for fields in ({}, {"hash": "x", "auth_date": "0",
                            "user": '{"id":1}'}):
            try:
                verify_init_data(fields, "111:t", now_epoch_s=NOW)
            except AuthError as exc:
                self.assertNotIn(MALIHEH, exc.reason)
                self.assertRegex(exc.reason, r"^[a-z_]+$")
