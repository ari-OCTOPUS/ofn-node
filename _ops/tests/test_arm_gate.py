#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_arm_gate — P5 fresh-arm-token + two-key gate. Proves it is strictly
fail-closed and only ever TIGHTENS (never opens what the ACTIVATION flag alone
would). stdlib-only; paths injected, no live state touched."""
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
import arm_gate as ag  # noqa: E402


class ArmGate(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="armgate_")
        self.ops = os.path.join(self.root, "ops")
        self.arm = os.path.join(self.root, "arm")
        os.makedirs(self.ops)
        os.makedirs(self.arm)
        self.now = 1_000_000.0

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # helpers
    def _flag(self, cap):
        name = ag.DANGEROUS[cap][0]
        open(os.path.join(self.ops, name), "w").close()

    def _token(self, cap, which="arm", *, armed_at=None, capability=None, secret=None, key=""):
        armed_at = self.now if armed_at is None else armed_at
        capability = cap if capability is None else capability
        tok = {"capability": capability, "armed_at": armed_at, "key": key}
        if secret:
            body = f"{capability}|{armed_at}|{key}".encode()
            tok["hmac"] = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        p = os.path.join(self.arm, f"{cap}.{which}.json")
        open(p, "w", encoding="utf-8").write(json.dumps(tok))

    def _open(self, cap, **kw):
        kw.setdefault("now", self.now)
        return ag.arm_open(cap, ops_dir=self.ops, arm_dir=self.arm, **kw)

    # --- fail-closed basics ---
    def test_unknown_capability_denied(self):
        ok, why = self._open("not_a_cap")
        self.assertFalse(ok)
        self.assertIn("unknown", why)

    def test_flag_absent_denied(self):
        # single-key cap, token present but NO activation flag -> deny
        self._token("cortex_paid")
        ok, why = self._open("cortex_paid")
        self.assertFalse(ok)
        self.assertIn("activation-flag-absent", why)

    def test_flag_present_but_no_token_denied(self):
        self._flag("cortex_paid")
        ok, why = self._open("cortex_paid")
        self.assertFalse(ok)
        self.assertIn("arm-token-1", why)

    def test_single_key_fresh_token_opens(self):
        self._flag("cortex_paid")
        self._token("cortex_paid")
        ok, why = self._open("cortex_paid")
        self.assertTrue(ok, why)

    # --- staleness / clock ---
    def test_stale_token_denied(self):
        self._flag("cortex_paid")
        self._token("cortex_paid", armed_at=self.now - ag.DEFAULT_TTL_S - 1)
        self.assertFalse(self._open("cortex_paid")[0])

    def test_future_token_denied(self):
        self._flag("cortex_paid")
        self._token("cortex_paid", armed_at=self.now + 500)  # clock-skew / forged future
        self.assertFalse(self._open("cortex_paid")[0])

    def test_wrong_capability_token_denied(self):
        self._flag("cortex_paid")
        self._token("cortex_paid", capability="something_else")
        self.assertFalse(self._open("cortex_paid")[0])

    # --- two-key (self-modification caps) ---
    def test_two_key_one_token_denied(self):
        self._flag("code_autonomy")
        self._token("code_autonomy", "arm")  # only key 1
        ok, why = self._open("code_autonomy")
        self.assertFalse(ok)
        self.assertIn("arm-token-2", why)

    def test_two_key_both_tokens_open(self):
        self._flag("code_autonomy")
        self._token("code_autonomy", "arm")
        self._token("code_autonomy", "arm2")
        self.assertTrue(self._open("code_autonomy")[0])

    def test_two_key_second_stale_denied(self):
        self._flag("code_autonomy")
        self._token("code_autonomy", "arm")
        self._token("code_autonomy", "arm2", armed_at=self.now - ag.DEFAULT_TTL_S - 1)
        self.assertFalse(self._open("code_autonomy")[0])

    # --- HMAC (owner-only binding when secret configured) ---
    def test_hmac_required_when_secret_and_bad_denied(self):
        self._flag("cortex_paid")
        self._token("cortex_paid")  # no hmac
        ok, why = self._open("cortex_paid", secret="owner-secret")
        self.assertFalse(ok)  # secret configured but token unsigned -> deny

    def test_hmac_valid_opens(self):
        self._flag("cortex_paid")
        self._token("cortex_paid", secret="owner-secret")
        self.assertTrue(self._open("cortex_paid", secret="owner-secret")[0])

    def test_hmac_forged_denied(self):
        self._flag("cortex_paid")
        self._token("cortex_paid", secret="attacker-secret")
        self.assertFalse(self._open("cortex_paid", secret="owner-secret")[0])

    # --- guard() enforcement toggle: byte-identical when not enforced ---
    def test_guard_passthrough_when_not_enforced(self):
        os.environ.pop("OCTOPUS_REQUIRE_ARM", None)
        ok, why = ag.guard("code_autonomy", ops_dir=self.ops, arm_dir=self.arm, now=self.now)
        self.assertTrue(ok)
        self.assertIn("not-enforced", why)

    def test_guard_enforced_denies_without_token(self):
        os.environ["OCTOPUS_REQUIRE_ARM"] = "1"
        try:
            self._flag("code_autonomy")  # flag present but no arm tokens
            ok, _ = ag.guard("code_autonomy", ops_dir=self.ops, arm_dir=self.arm, now=self.now)
            self.assertFalse(ok)  # enforced + no token -> deny (tightened)
        finally:
            os.environ.pop("OCTOPUS_REQUIRE_ARM", None)

    def test_arm_status_reports_all_caps(self):
        st = ag.arm_status(ops_dir=self.ops, arm_dir=self.arm, now=self.now)
        self.assertIn("caps", st)
        self.assertEqual(set(st["caps"]), set(ag.DANGEROUS))
        self.assertFalse(any(v["armed"] for v in st["caps"].values()))  # nothing armed by default


if __name__ == "__main__":
    unittest.main(verbosity=2)
