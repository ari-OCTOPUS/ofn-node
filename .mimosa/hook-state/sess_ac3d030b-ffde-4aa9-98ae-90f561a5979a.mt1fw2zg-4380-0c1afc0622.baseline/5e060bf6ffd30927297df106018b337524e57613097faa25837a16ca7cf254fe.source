#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_arm_renewal — Lane 1: تجدیدِ خودکارِ اَرم‌توکن. ثابت می‌کند این حلقه
STRICTLY additive است: هرگز چیزی را که arm_gate/ACTIVATION قبلاً رد کرده باز
نمی‌کند، و هر تمدید دقیقاً همان قراردادِ توکنِ arm_gate را برمی‌گرداند (round-trip
با arm_gate.arm_open واقعی، نه فقط شکلِ ظاهریِ JSON). stdlib-only؛ paths تزریقی،
هیچ حالتِ زنده لمس نمی‌شود."""
import os
import sys
import json
import time
import tempfile
import shutil
import hashlib
import hmac
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import arm_renewal as ar  # noqa: E402
import arm_gate as ag     # noqa: E402


class ArmRenewal(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="armrenewal_")
        self.ops = os.path.join(self.root, "ops")
        self.arm = os.path.join(self.root, "arm")
        os.makedirs(self.ops)
        os.makedirs(self.arm)
        self.now = 1_000_000.0
        # کولداونِ درون‌پروسه‌ای مشترکِ ماژول را برای هر تست صفر کن — وگرنه تستِ
        # قبلی روی تستِ بعدی اثر می‌گذارد (isolation).
        ar._last_check_ts = 0.0
        os.environ.pop(ar.FLAG, None)
        os.environ.pop("OCTOPUS_ARM_SECRET", None)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
        os.environ.pop(ar.FLAG, None)
        os.environ.pop("OCTOPUS_ARM_SECRET", None)

    # ── helpers ──────────────────────────────────────────────────────────
    def _on(self):
        os.environ[ar.FLAG] = "1"

    def _flag(self, cap):
        name = ag.DANGEROUS[cap][0]
        open(os.path.join(self.ops, name), "w").close()

    def _stop(self, cap):
        name = ar._stop_marker_name(ag.DANGEROUS[cap][0])
        open(os.path.join(self.ops, name), "w").close()

    def _token(self, cap, which="arm", *, armed_at=None, key="", secret=None):
        armed_at = self.now if armed_at is None else armed_at
        tok = {"capability": cap, "armed_at": armed_at, "key": key}
        if secret:
            body = f"{cap}|{armed_at}|{key}".encode()
            tok["hmac"] = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        p = os.path.join(self.arm, f"{cap}.{which}.json")
        open(p, "w", encoding="utf-8").write(json.dumps(tok))

    def _beat(self, **kw):
        kw.setdefault("ops_dir", self.ops)
        kw.setdefault("arm_dir", self.arm)
        kw.setdefault("now", self.now)
        return ar.beat(**kw)

    def _read_token(self, cap, which="arm"):
        p = os.path.join(self.arm, f"{cap}.{which}.json")
        return json.loads(open(p, encoding="utf-8").read())

    # ── flag-off ─────────────────────────────────────────────────────────
    def test_flag_off_is_noop(self):
        self._flag("code_autonomy")
        r = self._beat()
        self.assertFalse(r["ran"])
        self.assertEqual(r["reason"], "flag-off")
        self.assertFalse(os.path.exists(os.path.join(self.arm, "code_autonomy.arm.json")))

    # ── core invariant: additive only, never opens what ACTIVATION denies ──
    def test_no_activation_flag_no_mint(self):
        self._on()
        r = self._beat()
        self.assertTrue(r["ran"])
        self.assertEqual(r["minted"], [])
        self.assertTrue(any(s["capability"] == "code_autonomy" and s["reason"] == "not-active"
                             for s in r["skipped"]))
        self.assertFalse(os.path.exists(os.path.join(self.arm, "code_autonomy.arm.json")))

    def test_stop_marker_blocks_mint_even_with_activation(self):
        self._on()
        self._flag("code_autonomy")
        self._stop("code_autonomy")   # کیل‌مارکر — باید همه‌چیز را ببندد
        r = self._beat()
        self.assertEqual(r["minted"], [])
        self.assertFalse(os.path.exists(os.path.join(self.arm, "code_autonomy.arm.json")))

    def test_stop_marker_name_matches_code_autonomy_constant(self):
        # code_autonomy.py:533 دستی می‌نویسد KILL = opslib.OPS / "STOP-CODE-AUTONOMY".
        # این تست قفل می‌کند که مشتقِ عمومیِ ما هرگز از آن ثابت واگرا نشود.
        self.assertEqual(ar._stop_marker_name("ACTIVATION-CODE-AUTONOMY.flag"),
                          "STOP-CODE-AUTONOMY")

    # ── happy path: both keys minted for a two-key cap ──────────────────
    def test_activation_present_mints_both_keys(self):
        self._on()
        self._flag("code_autonomy")
        r = self._beat()
        self.assertEqual(len(r["minted"]), 2)   # arm + arm2 (two_key=True)
        which = {m["which"] for m in r["minted"]}
        self.assertEqual(which, {"arm", "arm2"})
        for w in ("arm", "arm2"):
            tok = self._read_token("code_autonomy", w)
            self.assertEqual(tok["capability"], "code_autonomy")
            self.assertEqual(tok["armed_at"], self.now)
            self.assertTrue(tok["key"])

    def test_minted_pair_actually_opens_via_arm_gate(self):
        # یکپارچگیِ واقعی: توکنِ ساخته‌شده باید دقیقاً همان چیزی باشد که
        # arm_gate.arm_open می‌پذیرد — نه فقط شکلِ JSON مشابه.
        self._on()
        self._flag("code_autonomy")
        self._beat()
        ok, why = ag.arm_open("code_autonomy", ops_dir=self.ops, arm_dir=self.arm, now=self.now)
        self.assertTrue(ok, why)

    def test_keys_are_random_hex_and_differ_per_slot(self):
        self._on()
        self._flag("code_autonomy")
        self._beat()
        k1 = self._read_token("code_autonomy", "arm")["key"]
        k2 = self._read_token("code_autonomy", "arm2")["key"]
        self.assertNotEqual(k1, k2)
        self.assertEqual(len(k1), 64)          # secrets.token_hex(32) -> 64 hex chars
        int(k1, 16)                            # می‌بایست معتبرِ hex باشد (raise می‌کند اگر نه)

    # ── freshness / renewal decision ────────────────────────────────────
    def test_fresh_token_not_reminted(self):
        self._on()
        self._flag("code_autonomy")
        self._token("code_autonomy", "arm", armed_at=self.now, key="orig-arm")
        self._token("code_autonomy", "arm2", armed_at=self.now, key="orig-arm2")
        r = self._beat()
        self.assertEqual(r["minted"], [])
        self.assertEqual(self._read_token("code_autonomy", "arm")["key"], "orig-arm")

    def test_near_expiry_token_is_reminted(self):
        self._on()
        self._flag("code_autonomy")
        # سنِ توکن = TTL - 1s -> داخلِ پنجرهٔ renew_before_s (۲h پیش‌فرض)
        stale_armed_at = self.now - (ag.DEFAULT_TTL_S - 1)
        self._token("code_autonomy", "arm", armed_at=stale_armed_at, key="old-arm")
        self._token("code_autonomy", "arm2", armed_at=stale_armed_at, key="old-arm2")
        r = self._beat()
        kinds = {m["which"]: m["reason"] for m in r["minted"]}
        self.assertEqual(kinds, {"arm": "near-expiry", "arm2": "near-expiry"})
        self.assertNotEqual(self._read_token("code_autonomy", "arm")["key"], "old-arm")

    def test_missing_token_reason_is_missing(self):
        self._on()
        self._flag("code_autonomy")
        r = self._beat()
        reasons = {m["which"]: m["reason"] for m in r["minted"]}
        self.assertEqual(reasons, {"arm": "missing", "arm2": "missing"})

    def test_corrupt_token_is_reminted(self):
        self._on()
        self._flag("code_autonomy")
        p = os.path.join(self.arm, "code_autonomy.arm.json")
        open(p, "w", encoding="utf-8").write("{not-json")
        open(os.path.join(self.arm, "code_autonomy.arm2.json"), "w",
             encoding="utf-8").write(json.dumps({"capability": "code_autonomy",
                                                  "armed_at": self.now, "key": "k"}))
        r = self._beat()
        minted_which = {m["which"] for m in r["minted"]}
        self.assertIn("arm", minted_which)
        self.assertNotIn("arm2", minted_which)   # arm2 بود و تازه بود -> دست‌نخورده

    def test_future_timestamp_token_is_reminted(self):
        self._on()
        self._flag("code_autonomy")
        self._token("code_autonomy", "arm", armed_at=self.now + 500, key="forged-future")
        self._token("code_autonomy", "arm2", armed_at=self.now, key="fine")
        r = self._beat()
        reasons = {m["which"]: m["reason"] for m in r["minted"]}
        self.assertEqual(reasons.get("arm"), "future-timestamp")
        self.assertNotIn("arm2", reasons)

    # ── HMAC round-trip (owner secret configured) ───────────────────────
    def test_hmac_signed_token_verifies_via_arm_gate(self):
        self._on()
        self._flag("code_autonomy")
        r = self._beat(secret="owner-secret")
        self.assertEqual(len(r["minted"]), 2)
        tok = self._read_token("code_autonomy", "arm")
        self.assertIn("hmac", tok)
        # هم مستقیم _hmac_ok، هم مسیرِ کاملِ arm_open — هر دو باید true بدهند.
        self.assertTrue(ag._hmac_ok(tok, "code_autonomy", "owner-secret"))
        ok, why = ag.arm_open("code_autonomy", ops_dir=self.ops, arm_dir=self.arm,
                               now=self.now, secret="owner-secret")
        self.assertTrue(ok, why)

    def test_wrong_secret_denied_by_arm_gate(self):
        self._on()
        self._flag("code_autonomy")
        self._beat(secret="owner-secret")
        ok, _ = ag.arm_open("code_autonomy", ops_dir=self.ops, arm_dir=self.arm,
                             now=self.now, secret="different-secret")
        self.assertFalse(ok)

    # ── second capability, symmetry ──────────────────────────────────────
    def test_self_improve_auto_symmetric_to_code_autonomy(self):
        self._on()
        self._flag("self_improve_auto")
        r = self._beat()
        minted_caps = {m["capability"] for m in r["minted"]}
        self.assertEqual(minted_caps, {"self_improve_auto"})
        self.assertEqual(len(r["minted"]), 2)  # هم دوکلیدی است (arm_gate.DANGEROUS)

    def test_two_capabilities_independent(self):
        self._on()
        self._flag("code_autonomy")
        # self_improve_auto عمداً بدونِ فلگ -> باید skip شود، نه اینکه کل beat بشکند
        r = self._beat()
        minted_caps = {m["capability"] for m in r["minted"]}
        self.assertEqual(minted_caps, {"code_autonomy"})
        self.assertTrue(any(s["capability"] == "self_improve_auto" and s["reason"] == "not-active"
                             for s in r["skipped"]))

    def test_only_the_two_wired_capabilities_are_touched(self):
        # cortex_paid هم در arm_gate.DANGEROUS است ولی خارجِ محدودهٔ Lane 1؛
        # حتی اگر فلگش حاضر باشد، arm_renewal نباید دست بزند.
        self._on()
        self._flag("cortex_paid")
        r = self._beat()
        self.assertEqual(r["minted"], [])
        caps_seen = {s["capability"] for s in r["skipped"]}
        self.assertNotIn("cortex_paid", caps_seen)   # اصلاً در RENEWAL_CAPS نیست

    # ── cooldown ─────────────────────────────────────────────────────────
    def test_cooldown_skips_immediate_second_call(self):
        self._on()
        self._flag("code_autonomy")
        r1 = self._beat()
        self.assertTrue(r1["ran"])
        r2 = self._beat(now=self.now + 1)   # فقط ۱ ثانیه بعد؛ کولداون ۶۰۰s
        self.assertFalse(r2["ran"])
        self.assertEqual(r2["reason"], "cooldown")

    def test_cooldown_elapsed_allows_recheck(self):
        self._on()
        self._flag("code_autonomy")
        self._beat()
        r2 = self._beat(now=self.now + ar.CHECK_COOLDOWN_S + 1)
        self.assertTrue(r2["ran"])

    # ── audit log ────────────────────────────────────────────────────────
    def test_renewal_log_records_each_mint(self):
        self._on()
        self._flag("code_autonomy")
        self._beat()
        log_path = os.path.join(self.arm, ar.RENEWAL_LOG_NAME)
        self.assertTrue(os.path.exists(log_path))
        rows = [json.loads(x) for x in open(log_path, encoding="utf-8").read().splitlines()
                if x.strip()]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row["capability"], "code_autonomy")
            self.assertIn(row["which"], ("arm", "arm2"))
            self.assertEqual(row["reason"], "missing")
            self.assertIn("ts", row)


if __name__ == "__main__":
    unittest.main(verbosity=2)
