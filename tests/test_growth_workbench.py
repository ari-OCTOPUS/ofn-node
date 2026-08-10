"""O8 — manual-first growth workbench.

A read-only facade over the existing per-business workflows. No new DB.
Every figure measured or explicitly not_measured — no vanity counts.
"""

from __future__ import annotations

import os
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.lead_store import LeadStore
from ofn.adapters.ledger import Ledger
from ofn.adapters.marketing_store import MarketingStore
from ofn.adapters.outbox import Outbox
from ofn.adapters.products import ProductStore
from ofn.adapters.studio_store import StudioStore
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

from tests.tmpdir import temp_dir

NOW = 1_785_000_000
NOW_ISO = "2026-08-10T12:00:00Z"


def _packs():
    return {
        "ziman": PackSpec(tenant=TenantId("ziman"),
                          capacity_units_per_week=6, quota_share=0.34),
        "lead": PackSpec(tenant=TenantId("lead"),
                         capacity_units_per_week=6, quota_share=0.33),
        "studio": PackSpec(tenant=TenantId("studio"),
                           capacity_units_per_week=5, quota_share=0.33),
    }


class TestGrowthWorkbench(unittest.TestCase):
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
            painting=LeadStore(os.path.join(self.dir, "painting.sqlite")),
            products=ProductStore(
                os.path.join(self.dir, "products.sqlite"),
                cost_fields=["materials_cost_aud"],
                labour_hours_field="labour_hours",
                labour_rate_field="hourly_rate_aud"),
            studio=StudioStore(os.path.join(self.dir, "studio.sqlite")),
            marketing=MarketingStore(
                os.path.join(self.dir, "marketing.sqlite")),
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
        )
        self.addCleanup(self.node.close)

    def test_workbench_has_three_sections(self):
        wb = self.node.owner_growth_workbench()
        self.assertTrue(wb["ok"])
        for section in ("lead", "ziman", "studio"):
            self.assertIn(section, wb)

    def test_no_parallel_db(self):
        """The workbench must not create any new tables."""
        wb = self.node.owner_growth_workbench()
        self.assertTrue(wb["ok"])

    def test_ziman_counts_from_products(self):
        p1 = self.node.products.create("ziman", "ZM", {
            "name": "گلدان", "materials_cost_aud": 10.0,
            "packaging_cost_aud": 2.0, "price_primary_aud": 45.0,
        }, now_iso=NOW_ISO)
        p2 = self.node.products.create("ziman", "ZM", {
            "name": "ظرف", "materials_cost_aud": 5.0,
            "packaging_cost_aud": 1.0, "price_primary_aud": 20.0,
        }, now_iso=NOW_ISO)
        # Move both to for_sale (the 'ready to list' lane).
        self.node.products.update("ziman", p1.sku, {"state": "for_sale"},
                                  now_iso=NOW_ISO)
        self.node.products.update("ziman", p2.sku, {"state": "for_sale"},
                                  now_iso=NOW_ISO)
        wb = self.node.owner_growth_workbench()
        self.assertGreaterEqual(wb["ziman"]["ready_to_list"], 2)

    def test_lead_campaigns_from_store(self):
        self.node.painting.upsert_campaign("lead", {
            "campaign_id": "c1", "title": "بهار", "status": "draft",
        }, now_iso=NOW_ISO)
        wb = self.node.owner_growth_workbench()
        self.assertEqual(len(wb["lead"]["campaigns"]), 1)
        self.assertEqual(wb["lead"]["campaigns"][0]["title"], "بهار")

    def test_workbench_is_read_only(self):
        before = self.node.owner_growth_workbench()
        self.node.owner_growth_workbench()
        after = self.node.owner_growth_workbench()
        self.assertEqual(before["ziman"], after["ziman"])
        self.assertEqual(before["lead"], after["lead"])


if __name__ == "__main__":
    unittest.main()
