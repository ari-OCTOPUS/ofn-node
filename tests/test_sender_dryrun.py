"""O11 — dry-run sender tests.

The sender must be structurally unable to publish: only dry_run_diff
exists, it mutates nothing, and without a green release context it
refuses even to propose.
"""

from __future__ import annotations

import ast
import os
import unittest

from ofn.adapters.sender_dryrun import PublishIntent, dry_run_diff
from ofn.kernel.release_switch import (
    ReleaseContext, require_release_context,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENDER = os.path.join(ROOT, "ofn", "adapters", "sender_dryrun.py")


def _green_release() -> dict:
    ctx = ReleaseContext(
        owner_confirmed_step1=True, owner_confirmed_step2=True,
        secret_rotation_open=True, partner_precondition_open=True,
        kill_switch_active=False, sensitivity="general",
        consent_ok=True, platform_ok=True, rate_limit_ok=True,
        idempotency_unused=True, ledger_ready=True)
    verdict = require_release_context(ctx)
    return {"ok": verdict.ok, "rule": verdict.rule,
            "risk": verdict.risk, "reason": verdict.rule}


class TestDryRunDiff(unittest.TestCase):
    def test_diff_builds_with_green_release(self):
        intent = PublishIntent("ziman", "bluesky", "k1", "کپشن تست")
        out = dry_run_diff(intent, _green_release())
        self.assertTrue(out["ok"])
        self.assertEqual(out["mode"], "dry-run")
        self.assertEqual(out["diff"]["caption"], "کپشن تست")
        self.assertEqual(out["diff"]["platform"], "bluesky")

    def test_refuses_without_release_context(self):
        intent = PublishIntent("ziman", "bluesky", "k1", "x")
        out = dry_run_diff(intent, None)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "release:context-missing")

    def test_refuses_when_release_blocked(self):
        intent = PublishIntent("ziman", "bluesky", "k1", "x")
        blocked = {"ok": False, "rule": "release:kill-switch-active",
                   "risk": "RED", "reason": "kill"}
        out = dry_run_diff(intent, blocked)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "release:kill-switch-active")

    def test_diff_is_deterministic(self):
        intent = PublishIntent("ziman", "bluesky", "k1", "کپشن")
        rel = _green_release()
        a = dry_run_diff(intent, rel)
        b = dry_run_diff(intent, rel)
        self.assertEqual(a["diff"]["payload_json"],
                         b["diff"]["payload_json"])


class TestNoRealSender(unittest.TestCase):
    def test_module_has_no_send_function(self):
        with open(SENDER, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src)
        funcs = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for name in funcs:
            self.assertNotIn("send", name.lower(),
                             f"module must not define {name}")

    def test_no_transport_imports(self):
        with open(SENDER, encoding="utf-8") as fh:
            src = fh.read()
        for token in ("urllib.request", "requests", "http.client",
                      "smtplib", "telebot"):
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
