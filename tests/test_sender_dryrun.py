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


class TestPublishToTelegram(unittest.TestCase):
    """O11 real-publish path: release-gated, dry-run default, cap enforced."""

    def _node(self, *, killed=False):
        import os
        from ofn.adapters.facts import FactStore
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.kernel.domain import PackSpec, TenantId
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node
        from tests.tmpdir import temp_dir
        d = temp_dir(self)
        registry = TenantRegistry({
            "studio": PackSpec(tenant=TenantId("studio"),
                               capacity_units_per_week=5, quota_share=1.0)})
        node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"studio": 1.0}),
            ledger=Ledger(os.path.join(d, "l.sqlite")),
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            now_epoch_s=lambda: 1_785_000_000,
            now_iso=lambda: "2026-08-10T12:00:00Z",
            killed=killed,
            _telegram_channel_id="@testchannel",
            _telegram_token="t:test",
        )
        return node, d, registry

    def test_dry_run_returns_diff_without_network(self):
        node, d, registry = self._node()
        scope = registry.scope("studio")
        out = node.publish_to_telegram(
            scope, idem_key="k1", caption="متن تست",
            dry_run=True, confirmed_twice=True)
        self.assertTrue(out["ok"])
        self.assertTrue(out["dry_run"])
        self.assertEqual(out["rule"], "adapter:dry-run")
        # No ledger mutation of a real send.
        events = node.ledger.read(scope, limit=5)
        self.assertEqual(len(events), 1)   # the dry-run ledger event

    def test_kill_switch_blocks(self):
        node, d, registry = self._node(killed=True)
        scope = registry.scope("studio")
        out = node.publish_to_telegram(
            scope, idem_key="k1", caption="x",
            dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "release:kill-switch-active")

    def test_second_confirmation_required_for_real(self):
        node, d, registry = self._node()
        scope = registry.scope("studio")
        out = node.publish_to_telegram(
            scope, idem_key="k1", caption="x",
            dry_run=False, confirmed_twice=False)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "release:owner-two-step-required")

    def test_caption_cap(self):
        node, d, registry = self._node()
        scope = registry.scope("studio")
        out = node.publish_to_telegram(
            scope, idem_key="k1", caption="x" * 5000,
            dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "publish:caption-too-long")

    def test_no_channel_configured(self):
        node, d, registry = self._node()
        node._telegram_channel_id = ""
        scope = registry.scope("studio")
        out = node.publish_to_telegram(
            scope, idem_key="k1", caption="x",
            dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "publish:no-channel")
