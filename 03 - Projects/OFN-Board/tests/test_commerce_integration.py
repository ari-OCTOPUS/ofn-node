"""Phase C integration: the wired commerce path end-to-end.

These tests prove the three properties the plan requires of the gated
commerce surface:

  1. A signed provider webhook with a verified settlement atomically marks
     the order paid and the product sold.
  2. An unsigned or tampered webhook is rejected (fail closed) and sells
     nothing.
  3. The authenticated audited-settlement route is 404 by default and only
     an owner session can call it when enabled.

No raw webhook body, customer PII, or untrusted confirmation may pass.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.inbound_rate import InboundRateLimiter
from ofn.adapters.connector_metrics import ConnectorMetrics
from ofn.adapters.ledger import Ledger
from ofn.adapters.marketing_inbox import MarketingInbox
from ofn.adapters.outbox import Outbox
from ofn.adapters.packloader import load_pack
from ofn.adapters.products import ProductStore
from ofn.adapters.commerce_connector import CommerceConnector
from ofn.kernel.auth import issue_session
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from tests.tmpdir import temp_dir

NOW_S = 1_785_000_000
NOW_ISO = "2026-08-10T12:00:00Z"
SECRET = "s"
OWNER = "7"
HOST = {"host": "z.test"}
LISTING_AT = "2026-08-10T10:00:00Z"
INQUIRY_AT = "2026-08-10T11:00:00Z"
RESERVED_AT = "2026-08-10T11:30:00Z"
EXPIRY = "2026-08-17T11:30:00Z"
SETTLED_AT = "2026-08-10T12:30:00Z"
EVIDENCE = hashlib.sha256(b"bank-receipt-42").hexdigest()


def _signed(body: dict, secret: str) -> tuple[bytes, str]:
    raw = json.dumps(body, sort_keys=True).encode()
    sig = "sha256=" + hmac.new(
        secret.encode(), raw, hashlib.sha256).hexdigest()
    return raw, sig


class _Base(unittest.TestCase):
    WEBHOOK_SECRET = "wh-secret-commerce"

    def setUp(self):
        d = temp_dir(self)
        pack = load_pack("packs/ziman.yaml")
        self.pack = pack
        self.registry = TenantRegistry({"ziman": pack})
        self.ledger = Ledger(os.path.join(d, "l.sqlite"))
        self.products = ProductStore(
            os.path.join(d, "p.sqlite"),
            cost_fields=pack.cost_fields,
            labour_hours_field=pack.labour_hours_field,
            labour_rate_field=pack.labour_rate_field)
        self.inbox = MarketingInbox(os.path.join(d, "inbox.sqlite"))
        self.node = Node(
            registry=self.registry, quota=None, ledger=self.ledger,
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            products=self.products, inbox=self.inbox,
            rate_limiter=InboundRateLimiter(),
            connector_metrics=ConnectorMetrics(),
            connectors={"commerce": CommerceConnector(
                secret=self.WEBHOOK_SECRET)})
        self.addCleanup(self.products.close)
        self._seed_production_chain()

    def _seed_production_chain(self):
        """Create a product + listing + inquiry + reservation (production)."""
        self.products.create("ziman", "ZM", {"name": "گلدان"},
                             now_iso=NOW_ISO)
        self.products.record_listing(
            "ziman", "ZM-0001", listing_id="listing-0001",
            channel="instagram",
            packet_sha256=hashlib.sha256(b"packet").hexdigest(),
            published_at=LISTING_AT, now_iso=NOW_ISO)
        self.products.create_inquiry(
            "ziman", "ZM-0001", inquiry_id="inquiry-0001",
            listing_id="listing-0001", channel="instagram",
            received_at=INQUIRY_AT, now_iso=NOW_ISO)
        self.products.reserve(
            "ziman", "ZM-0001", order_id="order-0001",
            listing_id="listing-0001", inquiry_id="inquiry-0001",
            reserved_at=RESERVED_AT, expires_at=EXPIRY, now_iso=NOW_ISO)

    def _webhook(self, body: dict, *, secret: str | None = None,
                 omit_signature: bool = False):
        raw, sig = _signed(body, secret or self.WEBHOOK_SECRET)
        headers = dict(HOST)
        if not omit_signature:
            headers["X-OFN-Signature"] = sig
        return self.node.handle_webhook("ziman", "commerce", headers, raw)


class TestSignedSettlementSells(_Base):
    SETTLEMENT = {
        "event_type": "commerce.settlement",
        "event_id": "event-settlement-0001",
        "order_id": "order-0001",
        "settlement_id": "settlement-0001",
        "amount_cents": 12000,
        "fee_cents": 300,
        "currency": "AUD",
        "status": "confirmed",
        "evidence_digest": EVIDENCE,
        "confirmed_at": SETTLED_AT,
    }

    def test_signed_settlement_marks_order_paid_and_product_sold(self):
        out = self._webhook(self.SETTLEMENT)
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "accepted")
        self.assertEqual(
            self.products.get("ziman", "ZM-0001").state, "sold")
        order_row = self.products.orders("ziman", "ZM-0001")[0]
        self.assertEqual(order_row["status"], "paid")
        self.assertEqual(len(self.products.payments("ziman", "order-0001")), 1)

    def test_unsigned_settlement_is_rejected_and_sells_nothing(self):
        out = self._webhook(self.SETTLEMENT, omit_signature=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "webhook:signature-invalid")
        self.assertEqual(
            self.products.get("ziman", "ZM-0001").state, "in_progress")
        self.assertEqual(len(self.products.payments("ziman", "order-0001")), 0)

    def test_tampered_secret_is_rejected(self):
        out = self._webhook(self.SETTLEMENT, secret="wrong-secret")
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "webhook:signature-invalid")

    def test_replayed_settlement_is_idempotent(self):
        self.assertTrue(self._webhook(self.SETTLEMENT)["ok"])
        out2 = self._webhook(self.SETTLEMENT)
        # Idempotent: the second call does not create a second payment or sale.
        self.assertEqual(len(self.products.payments("ziman", "order-0001")), 1)
        self.assertEqual(len(self.products.sales("ziman", "ZM-0001")), 1)

    def test_customer_pii_in_payload_is_rejected(self):
        bad = dict(self.SETTLEMENT, customer_email="buyer@example.com")
        out = self._webhook(bad)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "webhook:not-for-connector")


class TestSignedInquiry(_Base):
    INQUIRY = {
        "event_type": "commerce.inquiry",
        "event_id": "event-inquiry-0099",
        "sku": "ZM-0001",
        "listing_id": "listing-0001",
        "inquiry_id": "inquiry-webhook-0099",
        "channel": "instagram",
        "source_ref_digest": hashlib.sha256(b"dm-42").hexdigest(),
        "received_at": INQUIRY_AT,
    }

    def test_signed_inquiry_creates_inquiry_record(self):
        out = self._webhook(self.INQUIRY)
        self.assertTrue(out["ok"])
        ids = [i["inquiry_id"] for i in self.products.inquiries("ziman")]
        self.assertIn("inquiry-webhook-0099", ids)


class TestUnknownConnectorFailsClosed(_Base):
    def test_unknown_connector_id_is_rejected(self):
        body = {"event_type": "commerce.settlement", "event_id": "x" * 10}
        raw, sig = _signed(body, self.WEBHOOK_SECRET)
        headers = dict(HOST, **{"X-OFN-Signature": sig})
        out = self.node.handle_webhook("ziman", "unknown-connector", headers,
                                       raw)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "webhook:unknown-connector")


class TestAuditedSettlementRoute(unittest.TestCase):
    """The authenticated audited-receipt path: default-off, owner-only."""

    def setUp(self):
        d = temp_dir(self)
        pack = load_pack("packs/ziman.yaml")
        self.registry = TenantRegistry({"ziman": pack})
        self.ledger = Ledger(os.path.join(d, "l.sqlite"))
        self.products = ProductStore(
            os.path.join(d, "p.sqlite"),
            cost_fields=pack.cost_fields,
            labour_hours_field=pack.labour_hours_field,
            labour_rate_field=pack.labour_rate_field)
        self.node = Node(
            registry=self.registry, quota=None, ledger=self.ledger,
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            products=self.products)
        self.addCleanup(self.products.close)
        self.products.create("ziman", "ZM", {"name": "گلدان"},
                             now_iso=NOW_ISO)
        self.products.record_listing(
            "ziman", "ZM-0001", listing_id="listing-0001",
            channel="instagram",
            packet_sha256=hashlib.sha256(b"pkt").hexdigest(),
            published_at=LISTING_AT, now_iso=NOW_ISO)
        self.products.create_inquiry(
            "ziman", "ZM-0001", inquiry_id="inquiry-0001",
            listing_id="listing-0001", channel="instagram",
            received_at=INQUIRY_AT, now_iso=NOW_ISO)
        self.products.reserve(
            "ziman", "ZM-0001", order_id="order-0001",
            listing_id="listing-0001", inquiry_id="inquiry-0001",
            reserved_at=RESERVED_AT, expires_at=EXPIRY, now_iso=NOW_ISO)
        self.session = issue_session("owner", OWNER, SECRET, now_epoch_s=NOW_S)

    def _app(self, *, enabled: bool):
        return ApiApp(
            self.registry,
            HostMap(tenants={"z.test": "ziman"}, owner_host="p.test"),
            bot_tokens={"__owner__": "t"}, session_secret=SECRET,
            owner_user_ids=(OWNER,), now=lambda: NOW_S,
            confirm_order_settlement=self.node.confirm_order_settlement,
            audited_settlements_enabled=enabled)

    SETTLEMENT_BODY = {
        "order_id": "order-0001",
        "settlement_id": "settlement-0099",
        "amount_cents": 9000,
        "fee_cents": 200,
        "currency": "AUD",
        "evidence": "bank transfer receipt #42",
        "confirmed_at": SETTLED_AT,
        "production_confirmed": True,
    }

    def test_route_is_404_by_default(self):
        app = self._app(enabled=False)
        headers = {"host": "p.test",
                   "authorization": "Bearer " + self.session}
        r = app.handle("POST", "/api/v1/owner/orders/settlements",
                       headers,
                       json.dumps(self.SETTLEMENT_BODY).encode())
        self.assertEqual(r.status, 404)

    def test_enabled_owner_session_confirms_settlement(self):
        app = self._app(enabled=True)
        headers = {"host": "p.test",
                   "authorization": "Bearer " + self.session}
        r = app.handle("POST", "/api/v1/owner/orders/settlements",
                       headers,
                       json.dumps(self.SETTLEMENT_BODY).encode())
        self.assertEqual(r.status, 200)
        self.assertTrue(r.body["ok"])
        self.assertTrue(r.body["payment_confirmed"])
        self.assertEqual(
            self.products.get("ziman", "ZM-0001").state, "sold")

    def test_enabled_but_unauthenticated_is_401(self):
        app = self._app(enabled=True)
        r = app.handle("POST", "/api/v1/owner/orders/settlements",
                       {"host": "p.test"},
                       json.dumps(self.SETTLEMENT_BODY).encode())
        self.assertEqual(r.status, 401)

    def test_missing_callback_is_404_even_if_enabled(self):
        app = ApiApp(
            self.registry,
            HostMap(tenants={"z.test": "ziman"}, owner_host="p.test"),
            bot_tokens={"__owner__": "t"}, session_secret=SECRET,
            owner_user_ids=(OWNER,), now=lambda: NOW_S,
            audited_settlements_enabled=True)
        headers = {"host": "p.test",
                   "authorization": "Bearer " + self.session}
        r = app.handle("POST", "/api/v1/owner/orders/settlements",
                       headers,
                       json.dumps(self.SETTLEMENT_BODY).encode())
        self.assertEqual(r.status, 404)


if __name__ == "__main__":
    unittest.main()
