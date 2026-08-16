"""Hardened sale events and provenance for one-off products."""

from __future__ import annotations

import os
import sqlite3
import unittest

from ofn.adapters.products import ProductError, ProductStore
from tests.tmpdir import temp_dir

NOW = "2026-08-10T12:00:00Z"
LATER = "2026-08-11T12:00:00Z"
FORMULA = dict(cost_fields=["materials_cost_aud"],
               labour_hours_field="labour_hours",
               labour_rate_field="hourly_rate_aud")


class ZimanBase(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        self.path = os.path.join(self.dir, "products.sqlite")
        self.store = ProductStore(self.path, **FORMULA)
        self.addCleanup(self.store.close)
        self.sku = self.store.create(
            "ziman", "ZM", {"name": "گلدان", "materials_cost_aud": 10.0,
                            "price_primary_aud": 45.0}, now_iso=NOW).sku

    def sale(self, **over):
        args = dict(event_id="s1", sold_at=NOW, channel="instagram",
                    gross_cents=4500, fee_cents=500, now_iso=NOW)
        args.update(over)
        return self.store.record_sale("ziman", self.sku, **args)


class TestSaleEvents(ZimanBase):
    def test_sale_sets_canonical_channel_dates_and_state(self):
        out = self.sale()
        self.assertTrue(out["ok"])
        product = self.store.get("ziman", self.sku)
        self.assertEqual((product.state, product.channel), ("sold", "instagram"))
        self.assertEqual(product.sold_at, NOW)
        self.assertEqual(product.listed_at, NOW)
        self.assertEqual(product.updated_at, NOW)

    def test_existing_listing_date_is_preserved(self):
        self.store.update("ziman", self.sku, {"state": "for_sale"}, now_iso=NOW)
        self.sale(sold_at=LATER, now_iso=LATER)
        self.assertEqual(self.store.get("ziman", self.sku).listed_at, NOW)

    def test_unknown_sku_creates_no_event(self):
        out = self.store.record_sale(
            "ziman", "ZM-9999", event_id="missing", sold_at=NOW,
            channel="direct", amount_unknown=True, fee_unknown=True, now_iso=NOW)
        self.assertFalse(out["ok"])
        self.assertEqual(self.store._conn.execute(
            "SELECT count(*) FROM product_sale_events").fetchone()[0], 0)

    def test_tenant_isolation_creates_no_event(self):
        out = self.store.record_sale(
            "other", self.sku, event_id="wrong-tenant", sold_at=NOW,
            channel="direct", amount_unknown=True, fee_unknown=True, now_iso=NOW)
        self.assertFalse(out["ok"])
        self.assertEqual(self.store._conn.execute(
            "SELECT count(*) FROM product_sale_events").fetchone()[0], 0)
        self.assertNotEqual(self.store.get("ziman", self.sku).state, "sold")

    def test_archived_product_creates_no_event(self):
        self.store.archive("ziman", self.sku, now_iso=NOW)
        out = self.sale()
        self.assertFalse(out["ok"])
        self.assertIn("archived", out["error"])
        self.assertEqual(self.store.sales("ziman", self.sku), [])

    def test_only_in_progress_or_for_sale_can_sell(self):
        self.store.update("ziman", self.sku, {"state": "gifted"}, now_iso=NOW)
        out = self.sale()
        self.assertFalse(out["ok"])
        self.assertEqual(self.store.get("ziman", self.sku).state, "gifted")

    def test_known_or_unknown_is_exactly_one_for_each_money_field(self):
        bad = [
            {},
            {"gross_cents": 1, "amount_unknown": True, "fee_cents": 1},
            {"gross_cents": 1},
            {"gross_cents": 1, "fee_cents": 1, "fee_unknown": True},
        ]
        for i, changes in enumerate(bad):
            args = dict(event_id=f"bad-{i}", sold_at=NOW, channel="direct",
                        gross_cents=None, amount_unknown=False,
                        fee_cents=None, fee_unknown=False, now_iso=NOW)
            args.update(changes)
            self.assertFalse(self.store.record_sale("ziman", self.sku, **args)["ok"])
        self.assertEqual(self.store.sales("ziman", self.sku), [])

    def test_explicit_unknown_amount_and_fee_are_accepted(self):
        out = self.sale(gross_cents=None, amount_unknown=True,
                        fee_cents=None, fee_unknown=True)
        self.assertTrue(out["ok"])
        row = self.store.sales("ziman", self.sku)[0]
        self.assertTrue(row["amount_unknown"])
        self.assertTrue(row["fee_unknown"])

    def test_negative_float_and_bool_money_are_rejected(self):
        for i, value in enumerate((-1, 1.5, True)):
            out = self.sale(event_id=f"gross-{i}", gross_cents=value)
            self.assertFalse(out["ok"])
        for i, value in enumerate((-1, 1.5, False)):
            out = self.sale(event_id=f"fee-{i}", fee_cents=value)
            self.assertFalse(out["ok"])
        self.assertEqual(self.store.sales("ziman", self.sku), [])

    def test_duplicate_event_does_not_mutate_another_product(self):
        self.assertTrue(self.sale()["ok"])
        other = self.store.create("ziman", "ZM", {"name": "دومی"}, now_iso=LATER)
        out = self.store.record_sale(
            "ziman", other.sku, event_id="s1", sold_at=LATER, channel="direct",
            amount_unknown=True, fee_unknown=True, now_iso=LATER)
        self.assertFalse(out["ok"])
        self.assertTrue(out["duplicate"])
        self.assertEqual(self.store.get("ziman", other.sku).state, "in_progress")
        self.assertEqual(len(self.store.sales("ziman", self.sku)), 1)

    def test_operational_receipt_does_not_create_payment(self):
        self.sale(evidence_digest="receipt-sha256")
        self.assertEqual(self.store._conn.execute(
            "SELECT count(*) FROM product_payments").fetchone()[0], 0)

    def test_sales_returns_provenance_and_evidence(self):
        self.sale(evidence_digest="proof", environment="test",
                  source="fixture", created_by="test-runner")
        row = self.store.sales("ziman", self.sku)[0]
        self.assertEqual(row["evidence_digest"], "proof")
        self.assertEqual(row["environment"], "test")
        self.assertEqual(row["source"], "fixture")
        self.assertEqual(row["created_by"], "test-runner")


class TestSoldBypass(ZimanBase):
    def test_create_and_update_cannot_set_sold(self):
        with self.assertRaisesRegex(ProductError, "record_sale"):
            self.store.create("ziman", "ZM", {"name": "x", "state": "sold",
                                                "channel": "direct"}, now_iso=NOW)
        with self.assertRaisesRegex(ProductError, "record_sale"):
            self.store.update("ziman", self.sku,
                              {"state": "sold", "channel": "direct"}, now_iso=NOW)


class TestProvenanceMigration(unittest.TestCase):
    def test_normal_create_provenance_is_not_editable(self):
        path = os.path.join(temp_dir(self), "p.sqlite")
        store = ProductStore(path, **FORMULA)
        self.addCleanup(store.close)
        p = store.create("ziman", "ZM", {"name": "x"}, now_iso=NOW)
        self.assertEqual(p.environment, "production")
        self.assertEqual(p.as_dict()["source"], "authenticated_panel")
        with self.assertRaises(ProductError):
            store.update("ziman", p.sku, {"environment": "seed"}, now_iso=NOW)

    def test_old_rows_migrate_to_legacy_unknown_idempotently(self):
        path = os.path.join(temp_dir(self), "legacy.sqlite")
        conn = sqlite3.connect(path)
        conn.executescript("""
          CREATE TABLE products (
            id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL DEFAULT 'ziman',
            sku TEXT NOT NULL, name TEXT NOT NULL, category TEXT, description TEXT,
            materials_cost_aud REAL NOT NULL DEFAULT 0,
            labour_hours REAL NOT NULL DEFAULT 0, hourly_rate_aud REAL NOT NULL DEFAULT 0,
            packaging_cost_aud REAL NOT NULL DEFAULT 0, cogs_aud REAL NOT NULL DEFAULT 0,
            price_aud REAL, state TEXT NOT NULL DEFAULT 'in_progress', channel TEXT,
            listed_at TEXT, sold_at TEXT, marketing_status TEXT NOT NULL DEFAULT 'not_started',
            marketing_notes TEXT, created_at TEXT NOT NULL, updated_at TEXT);
          INSERT INTO products (tenant_id, sku, name, created_at)
          VALUES ('ziman', 'ZM-0007', 'legacy', '2025-01-01');
          CREATE TABLE product_sale_events (
            event_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, sku TEXT NOT NULL,
            gross_cents INTEGER, amount_unknown INTEGER NOT NULL DEFAULT 0,
            channel TEXT NOT NULL, fee_cents INTEGER, fee_unknown INTEGER NOT NULL DEFAULT 0,
            sold_at TEXT NOT NULL, created_at TEXT NOT NULL);
          INSERT INTO product_sale_events VALUES
            ('old-sale','ziman','ZM-0007',100,0,'direct',0,0,'2025-01-02','2025-01-02');
        """)
        conn.commit(); conn.close()
        first = ProductStore(path, **FORMULA)
        self.assertEqual(first.get("ziman", "ZM-0007").environment, "legacy_unknown")
        self.assertEqual(first.sales("ziman", "ZM-0007")[0]["environment"],
                         "legacy_unknown")
        first.close()
        second = ProductStore(path, **FORMULA)
        self.addCleanup(second.close)
        self.assertEqual(second.get("ziman", "ZM-0007").source, "legacy_unknown")


class TestListingPacket(ZimanBase):
    def test_packet_is_deterministic(self):
        one = self.store.listing_packet("ziman", self.sku)
        two = self.store.listing_packet("ziman", self.sku)
        self.assertEqual(one["sha256"], two["sha256"])
        self.assertEqual(len(one["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
