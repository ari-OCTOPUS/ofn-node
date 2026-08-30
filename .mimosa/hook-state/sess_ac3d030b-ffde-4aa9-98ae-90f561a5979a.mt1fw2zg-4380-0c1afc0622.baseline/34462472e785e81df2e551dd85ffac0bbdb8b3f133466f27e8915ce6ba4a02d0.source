"""Signed, provider-neutral inbound commerce events.

This is scaffolding, not a configured payment provider.  It accepts only a
small reviewed JSON shape, verifies the raw bytes with HMAC-SHA256, and emits
safe identifiers/digests for the Node to apply.  Customer names, addresses,
email, phone numbers, and raw provider payloads never enter the normalised
event.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Mapping

from .connector_contract import Connector, NormalisedEvent
from .webhook_verify import verify_with_header
from ..kernel.tenancy import TenantScope


_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED_TYPES = frozenset({"commerce.inquiry", "commerce.settlement"})
_ALLOWED_KEYS = {
    "commerce.inquiry": frozenset({
        "event_type", "event_id", "sku", "listing_id", "inquiry_id",
        "channel", "source_ref_digest", "received_at",
    }),
    "commerce.settlement": frozenset({
        "event_type", "event_id", "order_id", "settlement_id",
        "amount_cents", "fee_cents", "currency", "status",
        "evidence_digest", "confirmed_at",
    }),
}


class CommerceConnector(Connector):
    """Verify and reduce generic provider commerce callbacks.

    The connector is instantiated only when its feature flag is enabled and a
    non-empty signing secret is configured.  A future provider adapter may use
    a different header or signature construction without changing the store.
    """

    def __init__(self, secret: str, *, connector_id: str = "commerce",
                 vendor: str = "commerce_provider",
                 signature_header: str = "X-OFN-Signature") -> None:
        super().__init__(connector_id, vendor)
        self._secret = secret
        self._signature_header = signature_header

    def verify(self, body: bytes, headers: Mapping[str, str]):
        return verify_with_header(
            body, headers, self._signature_header, self._secret,
            algorithm="sha256")

    def normalise(self, scope: TenantScope, raw_body: bytes,
                  headers: Mapping[str, str],
                  correlation_id: str) -> NormalisedEvent | None:
        try:
            decoded = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(decoded, dict):
            return None
        event_type = decoded.get("event_type")
        if event_type not in _ALLOWED_TYPES:
            return None
        if set(decoded) - _ALLOWED_KEYS[event_type]:
            return None
        event_id = decoded.get("event_id")
        if not isinstance(event_id, str) or not _ID.fullmatch(event_id):
            return None

        payload = self._safe_payload(event_type, decoded)
        if payload is None:
            return None
        body_digest = hashlib.sha256(raw_body).hexdigest()
        return NormalisedEvent(
            event_type=event_type,
            vendor=self.vendor,
            vendor_event_id=event_id,
            body_sha256=body_digest,
            tenant=scope.tenant.value,
            occurred_at_epoch=0,
            correlation_id=correlation_id,
            payload=payload,
        )

    @staticmethod
    def _safe_payload(event_type: str,
                      data: Mapping[str, object]) -> Mapping[str, str]:
        required = (
            ("sku", "listing_id", "inquiry_id", "channel", "received_at")
            if event_type == "commerce.inquiry" else
            ("order_id", "settlement_id", "amount_cents", "currency",
             "status", "evidence_digest", "confirmed_at")
        )
        if any(key not in data for key in required):
            return None

        safe: dict[str, str] = {}
        for key, value in data.items():
            if key in ("event_type", "event_id"):
                continue
            if isinstance(value, bool) or not isinstance(value, (str, int)):
                return None
            safe[key] = str(value)

        id_keys = ("listing_id", "inquiry_id") if event_type == "commerce.inquiry" \
            else ("order_id", "settlement_id")
        if any(not _ID.fullmatch(safe.get(key, "")) for key in id_keys):
            return None
        digest_keys = (("source_ref_digest",)
                       if event_type == "commerce.inquiry"
                       else ("evidence_digest",))
        for key in digest_keys:
            value = safe.get(key, "")
            if value and not _DIGEST.fullmatch(value):
                return None
        if event_type == "commerce.settlement":
            try:
                amount = int(safe["amount_cents"])
                fee = int(safe["fee_cents"]) if "fee_cents" in safe else None
            except ValueError:
                return None
            if amount <= 0 or (fee is not None and fee < 0):
                return None
            if safe["status"] not in ("confirmed", "settled"):
                return None
            if not _DIGEST.fullmatch(safe["evidence_digest"]):
                return None
        return safe
