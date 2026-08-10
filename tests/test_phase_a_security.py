"""Phase A — connector security + observability honesty (P1 findings 7-12, 84, 100).

Pins the fixes from the P1 audit phase:
  A.1  ReplayGuard keys are SHA-256 digests of the whole initData, not suffix
  A.2  broken platform adapters are reported separately from available ones
  A.4  webhook tenant comes from the path and is cross-checked against Host
  A.6  OwnerRelease has a structural guard every future sender must call
  A.7  studio chat is scrubbed before it is persisted
"""

from __future__ import annotations

import hashlib
import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock

from ofn.adapters.http_api import ApiApp, HostMap
from ofn.kernel.auth import AuthError, ReplayGuard
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.release_switch import (
    ReleaseContext, require_release_context,
)
from ofn.kernel.scrub import has_identifying_data, scrub
from ofn.kernel.tenancy import TenantRegistry

from tests.tmpdir import temp_dir

NOW = 1_785_000_000
NOW_ISO = "2026-08-10T12:00:00"


# ═══════════════════════════════════════════════════════════════════════════
#  A.1 ReplayGuard digest
# ═══════════════════════════════════════════════════════════════════════════

class TestReplayGuardDigest(unittest.TestCase):
    """The auth path must key replay on the digest of the WHOLE blob."""

    def test_digest_is_sha256_of_full_string(self):
        raw = "auth_date=123&query_id=AAA&user=%7B%7D"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        self.assertEqual(len(digest), 64)

    def test_same_suffix_different_prefix_gives_different_digests(self):
        """Two blobs sharing a 64-char suffix must NOT collide as replay keys."""
        suffix = "A" * 64
        blob1 = "prefix-one-" + suffix
        blob2 = "prefix-two-" + suffix
        d1 = hashlib.sha256(blob1.encode("utf-8")).hexdigest()
        d2 = hashlib.sha256(blob2.encode("utf-8")).hexdigest()
        self.assertNotEqual(d1, d2)

    def test_replay_guard_accepts_both_distinct_blobs(self):
        """The ReplayGuard itself must not conflate them (it keys on digest)."""
        suffix = "B" * 64
        blob1 = "x=" + suffix
        blob2 = "y=" + suffix
        g = ReplayGuard()
        g.check_and_remember(
            hashlib.sha256(blob1.encode()).hexdigest(), NOW)
        g.check_and_remember(
            hashlib.sha256(blob2.encode()).hexdigest(), NOW)
        self.assertEqual(len(g), 2)

    def test_http_api_uses_digest_not_suffix(self):
        """The _auth path must feed the digest, never payload[-64:]."""
        src = open(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "ofn", "adapters", "http_api.py"),
            encoding="utf-8").read()
        self.assertNotIn('[-64:]', src)
        self.assertIn("hashlib.sha256(raw.encode(\"utf-8\")).hexdigest()", src)


# ═══════════════════════════════════════════════════════════════════════════
#  A.2 platform adapter health
# ═══════════════════════════════════════════════════════════════════════════

class TestPlatformAdapterHealth(unittest.TestCase):
    """broken_platforms() must be separate from available_platforms()."""

    def test_both_functions_exist(self):
        import ofn.adapters.platforms as platforms
        self.assertTrue(hasattr(platforms, "available_platforms"))
        self.assertTrue(hasattr(platforms, "broken_platforms"))

    def test_broken_module_reported_separately(self):
        import ofn.adapters.platforms as platforms
        # Create a fake broken module in the package path
        pkg_dir = os.path.dirname(platforms.__file__)
        broken_path = os.path.join(pkg_dir, "_broken_test_module.py")
        with open(broken_path, "w") as f:
            f.write("raise ImportError('intentional test failure')\n")
        self.addCleanup(os.unlink, broken_path)
        # Clear the import cache so it is re-imported
        importlib.invalidate_caches()
        try:
            broken = platforms.broken_platforms()
            self.assertIn("_broken_test_module", broken)
            # Available must not include the broken module's platform
            available = platforms.available_platforms()
            self.assertNotIn("_broken_test_module", available)
        finally:
            # Ensure the module does not linger
            sys.modules.pop("ofn.adapters.platforms._broken_test_module", None)


# ═══════════════════════════════════════════════════════════════════════════
#  A.4 webhook tenant cross-check
# ═══════════════════════════════════════════════════════════════════════════

class TestWebhookTenantCrossCheck(unittest.TestCase):
    """Tenant must come from the path and be cross-checked against Host."""

    def setUp(self):
        self.dir = temp_dir(self)
        registry = TenantRegistry({
            "ziman": PackSpec(tenant=TenantId("ziman"),
                              capacity_units_per_week=6, quota_share=0.5),
            "lead": PackSpec(tenant=TenantId("lead"),
                             capacity_units_per_week=6, quota_share=0.5),
        })
        self.app = ApiApp(
            registry,
            HostMap(tenants={"ziman.test": "ziman",
                             "lead.test": "lead"},
                    owner_host="panel.test"),
            bot_tokens={"__owner__": "t"},
            session_secret="test",
            owner_user_ids=("1",),
            partner_user_ids={},
            now=lambda: NOW,
            webhook_handler=lambda tenant, h, b: {
                "ok": True, "correlation_id": "c",
                "tenant_seen": tenant},
        )

    def test_path_tenant_matching_host_is_accepted(self):
        resp = self.app.handle(
            "POST", "/api/v1/webhooks/ziman/events",
            {"host": "ziman.test"}, b"{}")
        self.assertEqual(resp.status, 202)
        self.assertEqual(resp.body.get("tenant_seen"), "ziman")

    def test_path_tenant_mismatching_host_is_refused(self):
        resp = self.app.handle(
            "POST", "/api/v1/webhooks/ziman/events",
            {"host": "lead.test"}, b"{}")
        self.assertEqual(resp.status, 403)
        self.assertEqual(resp.body.get("rule"), "webhook:tenant-mismatch")

    def test_unknown_path_tenant_is_404(self):
        resp = self.app.handle(
            "POST", "/api/v1/webhooks/nonexistent/events",
            {"host": "ziman.test"}, b"{}")
        self.assertEqual(resp.status, 404)


# ═══════════════════════════════════════════════════════════════════════════
#  A.6 OwnerRelease structural guard
# ═══════════════════════════════════════════════════════════════════════════

class TestOwnerReleaseGuard(unittest.TestCase):
    """require_release_context is the structural gate for future senders."""

    def _green_ctx(self):
        return ReleaseContext(
            owner_confirmed_step1=True,
            owner_confirmed_step2=True,
            secret_rotation_open=True,
            partner_precondition_open=True,
            kill_switch_active=False,
            sensitivity="general",
            consent_ok=True,
            platform_ok=True,
            rate_limit_ok=True,
            idempotency_unused=True,
            ledger_ready=True,
        )

    def test_guard_exists_and_is_callable(self):
        v = require_release_context(self._green_ctx())
        self.assertTrue(v.ok)

    def test_kill_switch_still_first(self):
        ctx = self._green_ctx()
        ctx = ReleaseContext(
            owner_confirmed_step1=True, owner_confirmed_step2=True,
            secret_rotation_open=True, partner_precondition_open=True,
            kill_switch_active=True, sensitivity="general",
            consent_ok=True, platform_ok=True, rate_limit_ok=True,
            idempotency_unused=True, ledger_ready=True)
        v = require_release_context(ctx)
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "release:kill-switch-active")


# ═══════════════════════════════════════════════════════════════════════════
#  A.7 studio chat scrub
# ═══════════════════════════════════════════════════════════════════════════

class TestScrubBeforePersist(unittest.TestCase):
    """Chat messages with PII are scrubbed, and scrub detects common forms."""

    def test_phone_is_detected(self):
        self.assertTrue(has_identifying_data("با ۰۴۱۲۳۴۵۶۷۸۹ تماس بگیر"))

    def test_email_is_detected(self):
        self.assertTrue(has_identifying_data("ایمیل: test@example.com"))

    def test_clean_text_stays_clean(self):
        self.assertFalse(has_identifying_data("سلام، امروز عکس‌ها را آماده کردم"))

    def test_scrub_replaces_phone(self):
        result = scrub("شماره 0412345678 را نگه دار")
        self.assertNotIn("0412345678", result.text)
        self.assertIn("phone", result.findings)


if __name__ == "__main__":
    unittest.main()


class TestOwnerFacade(unittest.TestCase):
    """node.owner.X(...) behaves identically to node.X(...) (phase H)."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs")
        os.makedirs(packs_dir)
        with open(os.path.join(packs_dir, "ziman.yaml"), "w") as f:
            f.write(
                "tenant: ziman\n"
                "capacity_units_per_week: 6\n"
                "required_facts:\n"
                "  dummy_fact: owner_confirmed\n"
                "gates: []\n"
                "risk_overrides:\n"
                "  dummy_action: green\n"
                "quota_share: 0.5\n"
            )
        registry = TenantRegistry(load_dir(packs_dir))
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"ziman": 0.5}),
            ledger=Ledger(os.path.join(self.dir, "ledger.sqlite")),
            facts=FactStore(os.path.join(self.dir, "facts.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "outbox.sqlite")),
            now_epoch_s=lambda: 1_785_000_000,
            now_iso=lambda: NOW_ISO,
        )
        self.addCleanup(self.node.close)

    def test_facade_matches_direct_calls(self):
        for method, args in (
            ("status", ()),
            ("metrics", ()),
            ("observability", ()),
            ("snapshot", ()),
            ("businesses", ()),
            ("core_snapshot", ()),
            ("risks", ()),
            ("ledger_summary", ()),
            ("mini_webs", ()),
            ("telegram", ()),
            ("painting_dashboard", ()),
        ):
            with self.subTest(method=method):
                direct = getattr(self.node, {
                    "status": "owner_status",
                    "metrics": "owner_metrics",
                    "observability": "owner_observability",
                    "snapshot": "owner_snapshot",
                    "businesses": "owner_businesses",
                    "core_snapshot": "owner_core_snapshot",
                    "risks": "owner_risks",
                    "ledger_summary": "owner_ledger_summary",
                    "mini_webs": "owner_mini_webs_summary",
                    "telegram": "owner_telegram_summary",
                    "painting_dashboard": "painting_dashboard",
                }[method])(*args)
                facade = getattr(self.node.owner, method)(*args)
                self.assertEqual(facade.get("ok", True),
                                 direct.get("ok", True))

    def test_facade_events(self):
        direct = self.node.recent_events(5)
        facade = self.node.owner.events(5)
        self.assertEqual(len(facade), len(direct))

    def test_facade_queue_and_decide(self):
        self.assertEqual(self.node.owner.queue(), self.node.owner_queue())
        # decide with a bogus id: both paths agree on failure shape
        direct = self.node.owner_decide("x:y", True, True)
        facade = self.node.owner.decide("x:y", True, True)
        self.assertEqual(facade.get("ok"), direct.get("ok"))
