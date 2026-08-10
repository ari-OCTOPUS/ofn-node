"""O6 — ziman operationalisation: sale events, listing packet.

- record_sale: idempotent, amount/fee known-or-unknown (never both),
  sale event + product state in one transaction.
- sales: per-piece history.
- listing_packet: read-only manual packet with hash.
"""

from __future__ import annotations

import os
import unittest

from ofn.adapters.products import ProductStore

from tests.tmpdir import temp_dir

NOW = "2026-08-10T12:00:00Z"


class ZimanBase(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        self.store = ProductStore(
            os.path.join(self.dir, "products.sqlite"),
            cost_fields=["materials_cost_aud"],
            labour_hours_field="labour_hours",
            labour_rate_field="hourly_rate_aud",
        )
        self.addCleanup(self.store.close)
        # Create a piece via the store's public create path
        p = self.store.create("ziman", "ZM", {
            "name": "گلدان", "materials_cost_aud": 10.0,
            "packaging_cost_aud": 2.0,
            "price_primary_aud": 45.0,
        }, now_iso=NOW)
        self.sku = p["product"]["sku"] if isinstance(p, dict) else p.sku


class TestSaleEvents(ZimanBase):
    def test_record_sale_marks_product_sold(self):
        out = self.store.record_sale(
            "ziman", self.sku, event_id="s1", sold_at=NOW,
            channel="instagram", gross_cents=4500, fee_cents=500,
            now_iso=NOW)
        self.assertTrue(out["ok"])
        self.assertEqual(out["state"], "sold")
        product = self.store.get("ziman", self.sku)
        self.assertEqual(product.state, "sold")

    def test_sale_idempotent_by_event_id(self):
        self.store.record_sale("ziman", self.sku, event_id="s1",
                               sold_at=NOW, channel="direct",
                               gross_cents=4500, now_iso=NOW)
        out = self.store.record_sale("ziman", self.sku, event_id="s1",
                                     sold_at=NOW, channel="direct",
                                     gross_cents=4500, now_iso=NOW)
        self.assertFalse(out["ok"])
        # Exactly one event survives — the duplicate was a no-op.
        self.assertEqual(len(self.store.sales("ziman", self.sku)), 1)

    def test_amount_unknown_explicit(self):
        out = self.store.record_sale(
            "ziman", self.sku, event_id="s2", sold_at=NOW,
            channel="direct", amount_unknown=True, fee_unknown=True,
            now_iso=NOW)
        self.assertTrue(out["ok"])
        sales = self.store.sales("ziman", self.sku)
        self.assertTrue(sales[0]["amount_unknown"])
        self.assertIsNone(sales[0]["gross_cents"])

    def test_amount_cannot_be_both_known_and_unknown(self):
        out = self.store.record_sale(
            "ziman", self.sku, event_id="s3", sold_at=NOW,
            channel="direct", gross_cents=100, amount_unknown=True,
            now_iso=NOW)
        self.assertFalse(out["ok"])
        self.assertIn("both", out["error"])


class TestListingPacket(ZimanBase):
    def test_packet_has_canonical_fields_and_hash(self):
        packet = self.store.listing_packet("ziman", self.sku)
        self.assertIsNotNone(packet)
        assert packet is not None
        self.assertEqual(packet["sku"], self.sku)
        self.assertEqual(len(packet["sha256"]), 64)
        self.assertIn("price_primary_aud", packet)

    def test_packet_is_deterministic(self):
        p1 = self.store.listing_packet("ziman", self.sku)
        p2 = self.store.listing_packet("ziman", self.sku)
        self.assertEqual(p1["sha256"], p2["sha256"])

    def test_unknown_sku_returns_none(self):
        self.assertIsNone(self.store.listing_packet("ziman", "ZM-9999"))


class TestSaleTableConstraints(unittest.TestCase):
    def test_schema_has_sale_events(self):
        d = temp_dir(self)
        store = ProductStore(
            os.path.join(d, "products.sqlite"),
            cost_fields=["materials_cost_aud"],
            labour_hours_field="labour_hours",
            labour_rate_field="hourly_rate_aud")
        tables = {r[0] for r in store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        store.close()
        self.assertIn("product_sale_events", tables)


if __name__ == "__main__":
    unittest.main()
