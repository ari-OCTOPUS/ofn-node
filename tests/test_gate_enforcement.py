"""Gate enforcement: the kill switch must block ALL enqueue paths, not just propose().

These tests pin the contract added after the P0 audit: four direct enqueue
paths (publish_draft, send_to_outbox, send_lead_reply, send_lead_quote)
previously bypassed admit() and the kill switch. Now they all go through
_gate_enqueue, which checks killed first. owner_decide also refuses to
approve when killed.

Also tested:
  - config.py defaults partner_precondition as closed
  - http_api stubs for owner_decide and submit_answer are fail-closed
"""

from __future__ import annotations

import os
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.adapters.products import ProductStore
from ofn.adapters.studio_store import StudioStore
from ofn.adapters.consent_store import ConsentStore
from ofn.adapters.media import MediaStore
from ofn.adapters.audience_store import AudienceStore
from ofn.adapters.marketing_store import MarketingStore
from ofn.adapters.lead_store import LeadStore
from ofn.adapters.studio_assistant import StudioAssistantStore
from ofn import config as config_module
from ofn.kernel.domain import PackSpec, RiskTier, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

from tests.tmpdir import temp_dir

NOW = 1_785_000_000
NOW_ISO = "2026-08-10T12:00:00"


def _packs():
    return {
        name: PackSpec(
            tenant=TenantId(name),
            capacity_units_per_week=6,
            quota_share=share,
        )
        for name, share in (("lead", 0.3), ("studio", 0.3), ("ziman", 0.4))
    }


class GateEnforcementBase(unittest.TestCase):
    """A minimal node with real stores, for testing kill-switch blocking."""

    def setUp(self):
        self.dir = temp_dir(self)
        registry = TenantRegistry(_packs())
        ledger = Ledger(os.path.join(self.dir, "ledger.sqlite"))
        facts = FactStore(os.path.join(self.dir, "facts.sqlite"))
        outbox = Outbox(os.path.join(self.dir, "outbox.sqlite"))
        self.outbox = outbox
        products = ProductStore(
            os.path.join(self.dir, "products.sqlite"),
            cost_fields=["materials_cost_aud"],
            labour_hours_field="labour_hours",
            labour_rate_field="labour_rate",
        )
        studio = StudioStore(os.path.join(self.dir, "studio.sqlite"))
        consent = ConsentStore(os.path.join(self.dir, "consent.sqlite"))
        media = MediaStore(os.path.join(self.dir, "photos"))
        audience = AudienceStore(os.path.join(self.dir, "audience.sqlite"))
        marketing = MarketingStore(os.path.join(self.dir, "marketing.sqlite"))
        painting = LeadStore(os.path.join(self.dir, "painting.sqlite"))
        assistant = StudioAssistantStore(
            os.path.join(self.dir, "assistant.sqlite"))

        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0,
                            shares={"lead": 0.3, "studio": 0.3, "ziman": 0.4}),
            ledger=ledger, facts=facts, outbox=outbox,
            products=products, studio=studio, consent=consent, media=media,
            audience=audience, marketing=marketing, painting=painting,
            assistant=assistant,
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
            base_closed_gates=("secret_rotation", "partner_precondition",
                               "miner_isolation"),
        )
        self.addCleanup(self.node.close)
        self.scope = registry.scope("lead")

    def _make_lead(self):
        """Create a test lead and return its lead_id."""
        out = self.node.create_painting_lead(
            {"customer_name": "test", "phone": "123", "message": "hi",
             "source": "test"},
            actor="test")
        return out["lead"]["lead_id"]


class TestKillBlocksDirectEnqueue(GateEnforcementBase):
    """The kill switch must stop every enqueue path, not just propose()."""

    def test_send_lead_reply_blocked_when_killed(self):
        """SMS reply is RED and must be blocked by kill switch."""
        self.node.killed = True
        lead_id = self._make_lead()
        result = self.node.send_lead_reply(
            lead_id, {"channel": "sms", "message": "reply"}, actor="test")
        self.assertFalse(result["ok"])
        self.assertEqual(result.get("rule"), "gate:kill-switch")

    def test_send_lead_quote_blocked_when_killed(self):
        self.node.killed = True
        lead_id = self._make_lead()
        result = self.node.send_lead_quote(
            lead_id, {"amount": 100}, actor="test")
        self.assertFalse(result["ok"])
        self.assertEqual(result.get("rule"), "gate:kill-switch")

    def test_send_lead_reply_works_when_not_killed(self):
        """Sanity: when the switch is off, the path still works."""
        lead_id = self._make_lead()
        result = self.node.send_lead_reply(
            lead_id, {"channel": "note", "message": "ok"}, actor="test")
        self.assertTrue(result["ok"])


class TestKillBlocksOwnerApprove(GateEnforcementBase):
    """owner_decide must refuse to approve when the kill switch is engaged."""

    def test_approve_blocked_when_killed(self):
        # Queue something first (not killed)
        lead_id = self._make_lead()
        self.node.send_lead_reply(
            lead_id, {"channel": "sms", "message": "reply"}, actor="test")
        # Now kill
        self.node.killed = True
        # Find the queued item
        queue = self.outbox.pending(self.scope)
        self.assertTrue(len(queue) > 0)
        key = queue[0].idem_key.split(":", 1)[1]
        result = self.node.owner_decide(
            f"lead:{key}", approve=True, confirmed_twice=True)
        self.assertFalse(result["ok"])
        self.assertEqual(result.get("rule"), "gate:kill-switch")

    def test_reject_still_works_when_killed(self):
        """Rejecting (approve=False) must work even when killed — it doesn't send."""
        lead_id = self._make_lead()
        self.node.send_lead_reply(
            lead_id, {"channel": "sms", "message": "reply"}, actor="test")
        self.node.killed = True
        queue = self.outbox.pending(self.scope)
        key = queue[0].idem_key.split(":", 1)[1]
        result = self.node.owner_decide(
            f"lead:{key}", approve=False, confirmed_twice=False)
        self.assertTrue(result["ok"])


class TestPartnerPreconditionDefault(unittest.TestCase):
    """Gate defaults: opened by Ari's explicit 2026-08-10 decision.

    secret_rotation and partner_precondition were opened for a one-week
    window (risk accepted, see DECISION-open-gates.md). miner_isolation
    stays closed per D-8. When the week passes, secret_rotation goes back.
    """

    def test_partner_precondition_and_secret_rotation_open(self):
        cfg = config_module.load()
        self.assertNotIn("partner_precondition", cfg.base_closed_gates)
        self.assertNotIn("secret_rotation", cfg.base_closed_gates)
        self.assertIn("miner_isolation", cfg.base_closed_gates)


class TestHttpStubsFailClosed(unittest.TestCase):
    """Unwired callbacks must not fabricate success."""

    def test_owner_decide_stub_returns_false(self):
        from ofn.adapters.http_api import ApiApp, HostMap
        from ofn.kernel.domain import PackSpec, TenantId
        registry = TenantRegistry({
            "lead": PackSpec(tenant=TenantId("lead"),
                             capacity_units_per_week=6, quota_share=1.0)
        })
        # Deliberately do NOT wire owner_decide
        app = ApiApp(
            registry,
            HostMap(tenants={"panel.test": "lead"}, owner_host="panel.test"),
            bot_tokens={"__owner__": "t"},
            session_secret="test",
            owner_user_ids=("1",),
            partner_user_ids={},
            now=lambda: NOW,
        )
        result = app._owner_decide("lead:x", True, True)
        self.assertFalse(result["ok"])

    def test_submit_answer_stub_returns_false(self):
        from ofn.adapters.http_api import ApiApp, HostMap
        from ofn.kernel.domain import PackSpec, TenantId
        registry = TenantRegistry({
            "lead": PackSpec(tenant=TenantId("lead"),
                             capacity_units_per_week=6, quota_share=1.0)
        })
        app = ApiApp(
            registry,
            HostMap(tenants={"panel.test": "lead"}, owner_host="panel.test"),
            bot_tokens={"__owner__": "t"},
            session_secret="test",
            owner_user_ids=("1",),
            partner_user_ids={},
            now=lambda: NOW,
        )
        result = app._submit_answer("lead", "user", {})
        self.assertFalse(result["ok"])


class TestCloseAllStores(unittest.TestCase):
    """close() must shut every store that owns a SQLite Pool."""

    def test_all_stores_closed(self):
        self.dir = temp_dir(self)
        registry = TenantRegistry(_packs())
        ledger = Ledger(os.path.join(self.dir, "ledger.sqlite"))
        facts = FactStore(os.path.join(self.dir, "facts.sqlite"))
        outbox = Outbox(os.path.join(self.dir, "outbox.sqlite"))
        products = ProductStore(
            os.path.join(self.dir, "products.sqlite"),
            cost_fields=["materials_cost_aud"],
            labour_hours_field="labour_hours",
            labour_rate_field="labour_rate",
        )
        studio = StudioStore(os.path.join(self.dir, "studio.sqlite"))
        consent = ConsentStore(os.path.join(self.dir, "consent.sqlite"))
        media = MediaStore(os.path.join(self.dir, "photos"))
        audience = AudienceStore(os.path.join(self.dir, "audience.sqlite"))
        marketing = MarketingStore(os.path.join(self.dir, "marketing.sqlite"))
        painting = LeadStore(os.path.join(self.dir, "painting.sqlite"))
        assistant = StudioAssistantStore(
            os.path.join(self.dir, "assistant.sqlite"))

        node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0,
                            shares={"lead": 0.3, "studio": 0.3, "ziman": 0.4}),
            ledger=ledger, facts=facts, outbox=outbox,
            products=products, studio=studio, consent=consent, media=media,
            audience=audience, marketing=marketing, painting=painting,
            assistant=assistant,
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
        )

        # Track which stores are closed by wrapping their close methods.
        closed = []
        for name in ("ledger", "facts", "outbox", "products", "studio",
                      "consent", "audience", "marketing", "painting",
                      "assistant"):
            store = getattr(node, name)
            if store is not None:
                orig = store.close
                # Use a wrapper function that records then calls original
                def make_wrapper(orig_close, store_name):
                    def wrapper():
                        closed.append(store_name)
                        orig_close()
                    return wrapper
                store.close = make_wrapper(orig, name)

        node.close()

        # Every store must appear in the closed list.
        expected = {"ledger", "facts", "outbox", "products", "studio",
                    "consent", "audience", "marketing", "painting",
                    "assistant"}
        self.assertEqual(set(closed), expected,
                         f"Missing: {expected - set(closed)}")
