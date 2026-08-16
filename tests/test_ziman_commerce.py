"""Store-only gated commerce flow in products.sqlite."""

from __future__ import annotations

import os
import threading
import unittest

from ofn.adapters.products import ProductError, ProductStore
from tests.tmpdir import temp_dir

NOW = "2026-08-10T12:00:00Z"
LATER = "2026-08-10T13:00:00Z"
EXPIRY = "2026-08-11T12:00:00Z"
FORMULA = dict(cost_fields=["materials_cost_aud"],
               labour_hours_field="", labour_rate_field="")


class CommerceBase(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(temp_dir(self), "products.sqlite")
        self.s = ProductStore(self.path, **FORMULA)
        self.addCleanup(self.s.close)
        self.p = self.s.create("ziman", "ZM", {"name": "گلدان"}, now_iso=NOW,
                               environment="test", source="fixture",
                               created_by="runner")

    def listing(self, listing_id="l1", environment="test"):
        return self.s.record_listing(
            "ziman", self.p.sku, listing_id=listing_id, channel="instagram",
            packet_sha256="packet-sha", external_ref_digest="external-" + listing_id,
            published_at=NOW, environment=environment, source="fixture",
            created_by="runner", now_iso=NOW)

    def inquiry(self, inquiry_id="i1", listing_id="l1", environment="test"):
        return self.s.create_inquiry(
            "ziman", self.p.sku, inquiry_id=inquiry_id, listing_id=listing_id,
            channel="instagram", source_ref_digest="source-" + inquiry_id,
            received_at=NOW, environment=environment, source="fixture",
            created_by="runner", now_iso=NOW)

    def order(self, order_id="o1", listing_id="l1", inquiry_id="i1",
              environment="test"):
        return self.s.reserve(
            "ziman", self.p.sku, order_id=order_id, listing_id=listing_id,
            inquiry_id=inquiry_id, reserved_at=NOW, expires_at=EXPIRY,
            environment=environment, source="fixture", created_by="runner",
            now_iso=NOW)

    def chain(self, environment="test"):
        self.listing(environment=environment)
        self.inquiry(environment=environment)
        self.order(environment=environment)


class TestSchemaAndMetadata(CommerceBase):
    def test_all_tables_have_no_pii_columns(self):
        wanted = {"product_listing_events", "product_inquiries", "product_orders",
                  "product_payments"}
        tables = {r[0] for r in self.s._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(wanted <= tables)
        forbidden = {"name", "email", "phone", "address", "customer"}
        for table in wanted:
            cols = {r[1] for r in self.s._conn.execute(f"PRAGMA table_info({table})")}
            self.assertFalse(cols & forbidden)

    def test_seed_and_test_metadata_are_visible_for_exclusion(self):
        seed = self.s.create("ziman", "ZM", {"name": "seed"}, now_iso=NOW,
                             environment="seed", source="seed_loader",
                             created_by="seed_loader")
        self.assertEqual(seed.environment, "seed")
        self.listing()
        self.assertEqual(self.s.listings("ziman")[0]["environment"], "test")
        production = [p for p in self.s.list("ziman")
                      if p.environment == "production"]
        self.assertEqual(production, [])


class TestLinksAndReservation(CommerceBase):
    def test_linked_flow_and_availability(self):
        self.chain()
        self.assertFalse(self.s.is_available("ziman", self.p.sku, at_iso=LATER))
        self.assertEqual(self.s.orders("ziman")[0]["status"], "reserved")

    def test_wrong_tenant_and_links_are_refused(self):
        self.listing()
        with self.assertRaises(ProductError):
            self.s.create_inquiry(
                "other", self.p.sku, inquiry_id="bad", listing_id="l1",
                channel="instagram", received_at=NOW, environment="test",
                source="fixture", created_by="runner", now_iso=NOW)
        other = self.s.create("ziman", "ZM", {"name": "other"}, now_iso=NOW,
                              environment="test", source="fixture", created_by="runner")
        with self.assertRaises(ProductError):
            self.s.create_inquiry(
                "ziman", other.sku, inquiry_id="bad2", listing_id="l1",
                channel="instagram", received_at=NOW, environment="test",
                source="fixture", created_by="runner", now_iso=NOW)

    def test_reservation_race_allows_one_winner(self):
        self.listing(); self.inquiry()
        barrier = threading.Barrier(2)
        results = []
        def reserve(order_id):
            store = ProductStore(self.path, **FORMULA)
            try:
                barrier.wait()
                results.append(store.reserve(
                    "ziman", self.p.sku, order_id=order_id, listing_id="l1",
                    inquiry_id="i1", reserved_at=NOW, expires_at=EXPIRY,
                    environment="test", source="fixture", created_by="runner",
                    now_iso=NOW))
            except ProductError as exc:
                results.append(exc)
            finally:
                store.close()
        threads = [threading.Thread(target=reserve, args=(f"o{i}",)) for i in (1, 2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(sum(isinstance(x, dict) and x["ok"] for x in results), 1)
        self.assertEqual(sum(isinstance(x, ProductError) for x in results), 1)
        self.assertEqual(len(self.s.orders("ziman")), 1)

    def test_ids_are_idempotent(self):
        self.assertTrue(self.listing()["ok"])
        self.assertTrue(self.listing()["idempotent"])
        self.assertTrue(self.inquiry()["ok"])
        self.assertTrue(self.inquiry()["idempotent"])
        self.assertTrue(self.order()["ok"])
        self.assertTrue(self.order()["idempotent"])


class TestPayments(CommerceBase):
    def payment(self, **over):
        args = dict(payment_id="p1", order_id="o1", amount_cents=4500,
                    fee_cents=100, currency="AUD", status="confirmed",
                    provider="stripe", provider_event_digest="provider-event-1",
                    confirmation_source="provider_webhook", evidence_digest="proof",
                    confirmed_at=LATER, environment="test", source="webhook",
                    created_by="system", now_iso=LATER)
        args.update(over)
        return self.s.record_payment_confirmation("ziman", **args)

    def test_provider_webhook_confirms_order_and_sale_atomically(self):
        self.chain()
        out = self.payment()
        self.assertTrue(out["ok"])
        self.assertEqual(out["order_status"], "paid")
        self.assertEqual(self.s.get("ziman", self.p.sku).state, "sold")
        self.assertEqual(len(self.s.sales("ziman", self.p.sku)), 1)
        self.assertEqual(len(self.s.payments("ziman", "o1")), 1)

    def test_audited_receipt_is_accepted_in_production(self):
        p = self.s.create("ziman", "ZM", {"name": "prod"}, now_iso=NOW)
        self.p = p
        self.chain(environment="production")
        out = self.payment(environment="production",
                           confirmation_source="audited_receipt")
        self.assertTrue(out["ok"])

    def test_untrusted_or_empty_evidence_refused_in_production(self):
        p = self.s.create("ziman", "ZM", {"name": "prod"}, now_iso=NOW)
        self.p = p
        self.chain(environment="production")
        with self.assertRaises(ProductError):
            self.payment(environment="production", confirmation_source="manual")
        with self.assertRaises(ProductError):
            self.payment(environment="production", evidence_digest="")
        self.assertEqual(self.s.payments("ziman", "o1"), [])

    def test_test_order_cannot_be_labelled_production(self):
        self.chain()
        with self.assertRaises(ProductError):
            self.payment(environment="production")

    def test_payment_id_and_provider_event_are_idempotent(self):
        self.chain()
        self.assertTrue(self.payment()["ok"])
        self.assertTrue(self.payment()["idempotent"])
        second = self.payment(payment_id="p2")
        self.assertTrue(second["idempotent"])
        self.assertEqual(len(self.s.payments("ziman", "o1")), 1)

    def test_refunded_and_reversed_are_representable_without_reselling(self):
        self.chain()
        for status, suffix in (("refunded", "r"), ("reversed", "v")):
            out = self.payment(payment_id="p-" + suffix, status=status,
                               provider_event_digest="event-" + suffix,
                               confirmed_at=None)
            self.assertTrue(out["ok"])
        self.assertEqual({p["status"] for p in self.s.payments("ziman", "o1")},
                         {"refunded", "reversed"})
        self.assertEqual(self.s.get("ziman", self.p.sku).state, "in_progress")


if __name__ == "__main__":
    unittest.main()
