"""Receipt digest — the second witness of an EXECUTION_RECEIPT.

The store already stamps ``receipt_sha256`` on write and re-checks it on
load. That algorithm lives inline in ``run_store.py``, which an open PR
already owns. This adapter is the independent copy of the same rule:

  * digest the caller payload *without* ``receipt_sha256``
  * canonical form is ``json.dumps(..., ensure_ascii=False, sort_keys=True)``
  * a supplied digest must match or the write is refused
  * a missing digest is stamped, not invented as "clean without a hash"

Serialization belongs to adapters (kernel events stay json-free). This
module does not grant ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. A receipt is a record of an effect that
already happened inside the node, not a send.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional

from ofn.kernel import events as ev
from ofn.kernel.errors import FailClosedError

DIGEST_KEY = "receipt_sha256"
SEND_OR_READY = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def _as_mapping(payload: object, *, what: str) -> dict:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise FailClosedError(f"{what} must be a mapping: {payload!r}")
    return dict(payload)


def receipt_digest(body: Mapping[str, Any]) -> str:
    """sha256 hex of the canonical payload body (no digest key)."""
    if not isinstance(body, Mapping):
        raise FailClosedError(f"receipt body must be a mapping: {body!r}")
    if DIGEST_KEY in body:
        raise FailClosedError(
            "receipt_digest takes the body without receipt_sha256 — "
            "a self-hash is not a second witness")
    smuggled = ev.payload_forbidden_effect(body)
    if smuggled is not None:
        raise FailClosedError(
            f"receipt body smuggles forbidden effect name {smuggled!r}")
    return hashlib.sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def stamp_receipt(payload: Optional[Mapping[str, Any]] = None) -> dict:
    """Return a copy with ``receipt_sha256`` bound to the caller body.

    A caller-supplied digest is a check, not an input: mismatch refuses
    and writes nothing. Ready/authorized/sent names are refused.
    """
    incoming = _as_mapping(payload, what="EXECUTION_RECEIPT payload")
    claimed = incoming.pop(DIGEST_KEY, None)
    digest = receipt_digest(incoming)
    if claimed is not None and claimed != digest:
        raise FailClosedError(
            "receipt_sha256 does not match payload — refusing forged digest")
    incoming[DIGEST_KEY] = digest
    return incoming


def verify_receipt(payload: object) -> str:
    """Recompute and compare. Missing or mismatched digest fails closed.

    Returns the verified hex digest. Does not mutate ``payload``.
    """
    incoming = _as_mapping(payload, what="EXECUTION_RECEIPT payload")
    claimed = incoming.get(DIGEST_KEY)
    if not isinstance(claimed, str) or not claimed.strip():
        raise FailClosedError("EXECUTION_RECEIPT missing receipt_sha256")
    body = {k: v for k, v in incoming.items() if k != DIGEST_KEY}
    digest = receipt_digest(body)
    if claimed != digest:
        raise FailClosedError(
            "receipt_sha256 mismatch — refusing a tampered receipt")
    return digest


def grants_send(payload: Optional[Mapping[str, Any]] = None) -> bool:
    """A receipt stamp is never a send authorization. Structurally False."""
    if payload is not None:
        blob = json.dumps(payload, ensure_ascii=False)
        if any(name in blob for name in SEND_OR_READY):
            raise FailClosedError(
                "receipt mentioned a send/ready state — "
                "this module does not grant send_authorized")
    return False
