"""Shopify inbound connector — HMAC webhook → NormalisedEvent.

Scaffold only. Accepts nothing until a non-empty webhook secret is configured
and the connector is registered on the node. Customer PII never enters the
normalised payload — only digests and safe commerce ids.

Shopify signs webhooks with base64(HMAC-SHA256(raw_body, secret)) in
X-Shopify-Hmac-Sha256. Verification fails closed when secret or header is
missing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Mapping

from ofn.adapters.connector_contract import Connector, NormalisedEvent
from ofn.adapters.webhook_verify import VerifyResult
from ofn.kernel.tenancy import TenantScope


class ShopifyConnector(Connector):
    """Verify Shopify webhooks; normalise orders/checkouts to safe digests."""

    def __init__(
        self,
        secret: str,
        *,
        connector_id: str = "shopify",
        vendor: str = "shopify",
        signature_header: str = "X-Shopify-Hmac-Sha256",
    ) -> None:
        super().__init__(connector_id, vendor)
        self._secret = secret or ""
        self._signature_header = signature_header

    def verify(self, body: bytes, headers: Mapping[str, str]):
        if not self._secret:
            return VerifyResult(False, "shopify:no-secret")
        # Case-insensitive header lookup
        got = ""
        for k, v in headers.items():
            if k.lower() == self._signature_header.lower():
                got = str(v).strip()
                break
        if not got:
            return VerifyResult(False, "shopify:missing-hmac")
        digest = hmac.new(
            self._secret.encode("utf-8"), body, hashlib.sha256
        ).digest()
        expect = base64.b64encode(digest).decode("ascii")
        if not hmac.compare_digest(expect, got):
            return VerifyResult(False, "shopify:bad-hmac")
        return VerifyResult(True)

    def normalise(
        self,
        scope: TenantScope,
        raw_body: bytes,
        headers: Mapping[str, str],
        correlation_id: str,
    ) -> NormalisedEvent | None:
        try:
            decoded = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(decoded, dict):
            return None
        # Prefer Shopify topic header if present; else infer.
        topic = ""
        for k, v in headers.items():
            if k.lower() == "x-shopify-topic":
                topic = str(v).strip().lower()
                break
        event_type = "commerce.settlement" if "order" in topic or "order" in str(
            decoded.get("id", "")
        ) else "commerce.inquiry"
        # Never keep PII. Only opaque ids + body hash.
        raw_id = decoded.get("id") or decoded.get("admin_graphql_api_id") or ""
        vendor_event_id = str(raw_id).replace("/", "_")[:128] or hashlib.sha256(
            raw_body
        ).hexdigest()[:32]
        body_sha = hashlib.sha256(raw_body).hexdigest()
        safe = {
            "topic": topic[:80],
            "evidence_digest": body_sha,
        }
        if event_type == "commerce.settlement":
            # amount only if integer cents present without customer fields
            total = decoded.get("total_price")
            currency = decoded.get("currency") or decoded.get("presentment_currency")
            if isinstance(total, str) and total.replace(".", "", 1).isdigit():
                # dollars → cents without inventing; skip if unparsable
                try:
                    cents = int(round(float(total) * 100))
                    if cents > 0:
                        safe["amount_cents"] = str(cents)
                except ValueError:
                    pass
            if isinstance(currency, str) and currency:
                safe["currency"] = currency[:8]
            safe["status"] = "confirmed"
            safe["order_id"] = vendor_event_id[:64]
            safe["settlement_id"] = ("stl-" + body_sha[:24])
            safe["confirmed_at"] = str(decoded.get("created_at") or "")[:40]
        return NormalisedEvent(
            event_type=event_type,
            vendor=self.vendor,
            vendor_event_id=vendor_event_id[:128],
            body_sha256=body_sha,
            tenant=scope.tenant.value,
            occurred_at_epoch=0,
            correlation_id=correlation_id,
            payload=safe,
        )
