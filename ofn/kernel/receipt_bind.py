"""Bind a typed EXECUTION_RECEIPT to a caller-supplied digest.

The store stamps event_id. This module is the second witness for
*receipt identity*: a TYPED EXECUTION_RECEIPT plus a 64-hex sha256.
A proposal cannot bind as a receipt. Missing either side is
UNKNOWN (None), not FALSE and not an empty digest.

A forged digest (wrong length, uppercase, non-hex) fails closed.
The digest is recorded; it is not verified against a body here
(no I/O). Recording a digest is not filesystem immutability.

campaign_envelope_ready cannot be bound as a receipt and cannot
become send_authorized. This module does not write the store
and does not burn an idempotency key.

Not wired into run_store.py. HALT stops STARTS, not a bind.

Kernel purity: dataclasses + typing + re (via envelope). No I/O,
no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import SHA256_HEX_RE
from .errors import FailClosedError
from .events import EXECUTION_RECEIPT, PROPOSAL_CREATED
from .typed_event import (
    TYPED,
    TypedEvent,
    classify_record,
    is_execution,
    require_typed,
    try_typed,
)


def grants_send() -> bool:
    """A receipt bind never authorizes a send. Structurally False."""
    return False


def halt_blocks_bind() -> bool:
    """Structurally False. HALT stops STARTS, not receipt binding."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A digest bind is not filesystem immutability."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal cannot bind as a receipt."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. Binding a digest does not consume a key."""
    return False


def unknown_digest_is_empty() -> bool:
    """Structurally False. Missing digest is UNKNOWN, not ''."""
    return False


def _require_digest(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"digest must be a str: {value!r}")
    if not SHA256_HEX_RE.match(value):
        raise FailClosedError(
            f"digest must be 64 lowercase hex: {value!r}")
    return value


@dataclass(frozen=True)
class ReceiptBind:
    """One EXECUTION_RECEIPT + digest pair. Frozen so a later write
    cannot silently retcon the recorded identity.
    """

    run_id: str
    digest: str
    kind: str
    ts: int
    ref: Optional[str]


def bind_receipt(record: object, digest: object) -> ReceiptBind:
    """Require a TYPED EXECUTION_RECEIPT and a 64-hex digest.

    Explicit bind is not try_bind: missing is not softened to
    UNKNOWN here. PROPOSAL_CREATED fails closed.
    """
    typed = require_typed(record)
    if typed.kind == PROPOSAL_CREATED or not is_execution(typed.kind):
        raise FailClosedError(
            f"kind {typed.kind!r} is not EXECUTION_RECEIPT — "
            "proposal is not execution")
    hex_digest = _require_digest(digest)
    return ReceiptBind(
        run_id=typed.run_id,
        digest=hex_digest,
        kind=EXECUTION_RECEIPT,
        ts=typed.ts,
        ref=typed.ref,
    )


def try_bind(record: object, digest: object) -> Optional[ReceiptBind]:
    """Missing record, missing required field, or missing digest is
    UNKNOWN (None). Present-but-bad values still fail closed.
    """
    if digest is None:
        return None
    typed = try_typed(record)
    if typed is None:
        return None
    return bind_receipt(record, digest)


def digest_agrees(
    record: object, digest: object, expected: object,
) -> Optional[bool]:
    """True when the bound digest equals the expected 64-hex.

    Missing either side is UNKNOWN (None), not False. A bind that
    exists but names two different digests is False — that is a
    measured disagreement, not a missing witness.
    """
    if expected is None:
        return None
    bound = try_bind(record, digest)
    if bound is None:
        return None
    want = _require_digest(expected)
    return bound.digest == want


def typed_is_receipt(record: object) -> Optional[bool]:
    """True when classify_record is TYPED and kind is EXECUTION_RECEIPT.

    Missing record is UNKNOWN (None), not False. A TYPED proposal
    is False — measured, not missing.
    """
    klass = classify_record(record)
    if klass != TYPED:
        return None
    typed: TypedEvent = require_typed(record)
    return typed.kind == EXECUTION_RECEIPT
