from __future__ import annotations

import hashlib
import hmac
import json
import unittest

from ofn.adapters.commerce_connector import CommerceConnector
from ofn.kernel.tenancy import TenantId, TenantScope


class TestCommerceConnector(unittest.TestCase):
    def setUp(self):
        self.secret = "test-secret"
        self.connector = CommerceConnector(self.secret)
        self.scope = TenantScope(TenantId("ziman"))

    def signed(self, body: bytes) -> dict[str, str]:
        digest = hmac.new(
            self.secret.encode(), body, hashlib.sha256).hexdigest()
        return {"X-OFN-Signature": f"sha256={digest}"}

    def test_signature_fails_closed(self):
        out = self.connector.verify(b"{}", {})
        self.assertFalse(out.valid)

    def test_settlement_normalises_only_reviewed_fields(self):
        body = json.dumps({
            "event_type": "commerce.settlement",
            "event_id": "evt-00000001",
            "order_id": "ord-00000001",
            "settlement_id": "pay-00000001",
            "amount_cents": 12000,
            "fee_cents": 300,
            "currency": "AUD",
            "status": "settled",
            "evidence_digest": "a" * 64,
            "confirmed_at": "2026-08-10T12:00:00Z",
        }, separators=(",", ":")).encode()
        self.assertTrue(self.connector.verify(body, self.signed(body)).valid)
        event = self.connector.normalise(
            self.scope, body, self.signed(body), "cid")
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.event_type, "commerce.settlement")
        self.assertEqual(event.vendor_event_id, "evt-00000001")
        self.assertEqual(event.payload["order_id"], "ord-00000001")
        self.assertEqual(event.payload["amount_cents"], "12000")
        self.assertEqual(event.body_sha256, hashlib.sha256(body).hexdigest())

    def test_customer_data_is_rejected_not_normalised(self):
        body = json.dumps({
            "event_type": "commerce.inquiry",
            "event_id": "evt-00000002",
            "listing_id": "lst-00000001",
            "inquiry_id": "inq-00000001",
            "sku": "ZM-0001",
            "channel": "instagram",
            "received_at": "2026-08-10T12:00:00Z",
            "email": "customer@example.test",
        }).encode()
        event = self.connector.normalise(
            self.scope, body, self.signed(body), "cid")
        self.assertIsNone(event)

    def test_non_positive_settlement_is_rejected(self):
        body = json.dumps({
            "event_type": "commerce.settlement",
            "event_id": "evt-00000003",
            "order_id": "ord-00000001",
            "settlement_id": "pay-00000001",
            "amount_cents": 0,
            "currency": "AUD",
            "status": "confirmed",
            "evidence_digest": "a" * 64,
            "confirmed_at": "2026-08-10T12:00:00Z",
        }).encode()
        self.assertIsNone(self.connector.normalise(
            self.scope, body, self.signed(body), "cid"))

    def test_fake_status_cannot_confirm(self):
        body = json.dumps({
            "event_type": "commerce.settlement",
            "event_id": "evt-00000004",
            "order_id": "ord-00000001",
            "settlement_id": "pay-00000001",
            "amount_cents": 100,
            "currency": "AUD",
            "status": "sandbox",
            "evidence_digest": "a" * 64,
            "confirmed_at": "2026-08-10T12:00:00Z",
        }).encode()
        self.assertIsNone(self.connector.normalise(
            self.scope, body, self.signed(body), "cid"))


if __name__ == "__main__":
    unittest.main()
