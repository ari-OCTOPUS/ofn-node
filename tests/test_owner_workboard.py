"""O4 — owner workboard: cross-business read-only projection.

The workboard must be owner-only, read-only (refresh creates no mutation),
and every count must come from the canonical stores — never a parallel DB.
"""

from __future__ import annotations

import json
import os
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.adapters.products import ProductStore
from ofn.adapters.studio_store import StudioStore
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import PackSpec, RiskTier, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

from tests.tmpdir import temp_dir

NOW = 1_785_000_000
NOW_ISO = "2026-08-10T12:00:00Z"
SECRET = "wb-test-secret"


def _packs():
    return {
        "ziman": PackSpec(tenant=TenantId("ziman"),
                          capacity_units_per_week=6, quota_share=0.34),
        "lead": PackSpec(tenant=TenantId("lead"),
                         capacity_units_per_week=6, quota_share=0.33),
        "studio": PackSpec(tenant=TenantId("studio"),
                           capacity_units_per_week=5, quota_share=0.33),
    }


class TestOwnerWorkboard(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        registry = TenantRegistry(_packs())
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0,
                            shares={"ziman": 0.34, "lead": 0.33,
                                    "studio": 0.33}),
            ledger=Ledger(os.path.join(self.dir, "ledger.sqlite")),
            facts=FactStore(os.path.join(self.dir, "facts.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "outbox.sqlite")),
            products=ProductStore(
                os.path.join(self.dir, "products.sqlite"),
                cost_fields=["materials_cost_aud"],
                labour_hours_field="labour_hours",
                labour_rate_field="labour_rate"),
            studio=StudioStore(os.path.join(self.dir, "studio.sqlite")),
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
        )
        self.addCleanup(self.node.close)
        self.app = ApiApp(
            registry,
            HostMap(tenants={"z.test": "ziman", "l.test": "lead",
                             "s.test": "studio"},
                    owner_host="panel.test"),
            bot_tokens={"__owner__": "t"},
            session_secret=SECRET,
            owner_user_ids=("1",),
            partner_user_ids={},
            now=lambda: NOW,
            owner_workboard=self.node.owner_workboard,
        )
        self.session = issue_session("owner", "1", SECRET,
                                     now_epoch_s=NOW)

    def test_workboard_owner_only(self):
        resp = self.app.handle("GET", "/api/v1/owner/workboard",
                               {"host": "panel.test"}, b"")
        self.assertEqual(resp.status, 401)

    def test_workboard_returns_sections(self):
        resp = self.app.handle(
            "GET", "/api/v1/owner/workboard",
            {"host": "panel.test",
             "authorization": "Bearer " + self.session}, b"")
        self.assertEqual(resp.status, 200)
        body = resp.body
        self.assertTrue(body["ok"])
        for section in ("today", "lead", "ziman", "studio", "gaps"):
            self.assertIn(section, body)

    def test_approvals_counted(self):
        scope = self.node.registry.scope("lead")
        self.node.outbox.enqueue(
            scope, "k1", "email", {"text": "x"}, RiskTier.YELLOW, NOW_ISO)
        self.node.outbox.enqueue(
            scope, "k2", "sms", {"text": "y"}, RiskTier.RED, NOW_ISO)
        board = self.node.owner_workboard()
        self.assertEqual(board["today"]["approvals"], 2)

    def test_manual_pending_counted(self):
        scope = self.node.registry.scope("lead")
        self.node.outbox.enqueue(
            scope, "k1", "email", {"text": "x"}, RiskTier.YELLOW, NOW_ISO)
        self.node.outbox.approve_manual(scope, "k1", NOW_ISO)
        board = self.node.owner_workboard()
        self.assertEqual(board["today"]["manual_pending"], 1)

    def test_refresh_is_read_only(self):
        """Two calls must not change state (no mutation on refresh)."""
        before = self.node.owner_workboard()
        self.node.owner_workboard()
        after = self.node.owner_workboard()
        self.assertEqual(before["today"], after["today"])

    def test_no_store_header(self):
        resp = self.app.handle(
            "GET", "/api/v1/owner/workboard",
            {"host": "panel.test",
             "authorization": "Bearer " + self.session}, b"")
        self.assertEqual(resp.headers.get("Cache-Control"),
                         "private, no-store")


if __name__ == "__main__":
    unittest.main()
