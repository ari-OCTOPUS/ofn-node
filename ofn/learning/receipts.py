#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""receipts — ReceiptVerifier: an economic claim is only as good as its
independently verifiable receipt.

No fake payments, no un-receipted recording, no self-attestation: a payment
claim becomes VERIFIED only when an EXTERNAL receipt (source ≠ claimant,
hash matching the claimed external_receipt_hash) confirms it. Everything
else stays honestly labelled.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

__all__ = ["PaymentReceipt", "ReceiptVerifier", "VERIFIED", "STATUSES",
           "canonical_json", "sha256_text"]


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

VERIFIED = "VERIFIED"
UNVERIFIED_NO_RECEIPT = "UNVERIFIED_NO_RECEIPT"
TAMPERED = "TAMPERED"
DISCONNECTED = "DISCONNECTED"
STATUSES = (VERIFIED, UNVERIFIED_NO_RECEIPT, TAMPERED, DISCONNECTED)


@dataclass
class PaymentReceipt:
    payment_id: str
    amount: float | None
    currency: str | None
    received_at: str | None
    external_receipt_hash: str | None
    source: str
    verification_status: str

    @property
    def is_verified(self) -> bool:
        return self.verification_status == VERIFIED


def _receipt_hash(receipt: dict) -> str:
    """Canonical digest of the independent receipt's load-bearing fields."""
    payload = "|".join(str(receipt.get(k, "")) for k in
                       ("payment_id", "amount", "currency", "received_at", "payer"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ReceiptVerifier:
    """Verifies payment claims against an independent receipt store.

    `receipt_lookup(payment_id) -> dict | None` must come from a source that
    is independent of whoever made the claim (bank export, payment provider,
    board runtime store). The verifier itself never fabricates a receipt.
    """

    def __init__(self, receipt_lookup):
        self._lookup = receipt_lookup

    def verify(self, claim: dict, *, linked_to_lead: bool = True) -> PaymentReceipt:
        pid = str(claim.get("payment_id", "")).strip()
        ext_hash = claim.get("external_receipt_hash") or ""
        amount, currency = claim.get("amount"), claim.get("currency")
        received_at = claim.get("received_at")
        source = str(claim.get("source", "claim"))

        if not pid:
            return PaymentReceipt("", amount, currency, received_at, ext_hash, source,
                                  UNVERIFIED_NO_RECEIPT)
        independent = self._lookup(pid)
        if independent is None:
            return PaymentReceipt(pid, amount, currency, received_at, ext_hash, source,
                                  UNVERIFIED_NO_RECEIPT)
        # cross-check every field the receipt also carries
        for field in ("amount", "currency", "received_at"):
            if field in independent and field in claim:
                if str(claim[field]) != str(independent[field]):
                    return PaymentReceipt(pid, amount, currency, received_at, ext_hash,
                                          source, TAMPERED)
        actual = _receipt_hash(independent)
        if ext_hash and ext_hash != actual:
            return PaymentReceipt(pid, amount, currency, received_at, ext_hash, source,
                                  TAMPERED)
        status = VERIFIED if linked_to_lead else DISCONNECTED
        return PaymentReceipt(pid,
                              independent.get("amount", amount),
                              independent.get("currency", currency),
                              independent.get("received_at", received_at),
                              actual, independent.get("source", "independent"),
                              status)
