"""One verdict → one budget effect.

A BUDGET_DEBIT must settle exactly one prior receipt. The store
enforces this inline; this module is the kernel-pure second witness
so the rule can be tested without opening a ledger.

Not wired into the run store (that file is owned by another open
change). A settlement records an in-node debit. It does not grant
send_authorized, quote_sent, or campaign_envelope_ready.

HALT stops STARTS. This index has no halt parameter: in-flight
receipts must still settle so recovery does not need the owner.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# "sent" / "authorized" / "ready" are not receipt identities.
_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A settlement index never authorizes a send. Structurally False."""
    return False


def halt_blocks_settlement() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight settlement."""
    return False


def _require_receipt_id(receipt_id: str) -> str:
    if not isinstance(receipt_id, str) or not receipt_id.strip():
        raise FailClosedError(f"receipt_id required: {receipt_id!r}")
    if is_forbidden_effect_name(receipt_id) or receipt_id.strip().lower() in _SEALED:
        raise FailClosedError(
            f"receipt_id names a sealed send/ready state: {receipt_id!r}")
    return receipt_id


class SettlementIndex:
    """Append-only in-memory settlement map. Replay does not write.

    Two independent claims:

      * note_receipt  — a receipt must exist before it can be spent
      * settle        — a known receipt may be spent exactly once
    """

    def __init__(self) -> None:
        self._known: Dict[str, bool] = {}  # receipt_id -> settled?
        self._order: List[str] = []

    def note_receipt(self, receipt_id: str) -> bool:
        """Register a receipt. Re-noting the same id is idempotent.

        Returns True on first note, False on a no-op re-note.
        """
        receipt_id = _require_receipt_id(receipt_id)
        if receipt_id in self._known:
            return False
        self._known[receipt_id] = False
        self._order.append(receipt_id)
        return True

    def settle(self, receipt_id: str) -> None:
        """Spend exactly once. Unknown or already-settled fails closed."""
        receipt_id = _require_receipt_id(receipt_id)
        if receipt_id not in self._known:
            raise FailClosedError(
                f"BUDGET_DEBIT ref unknown receipt: {receipt_id!r} — "
                "one verdict → one budget effect starts with a real receipt")
        if self._known[receipt_id]:
            raise FailClosedError(
                f"receipt {receipt_id!r} already settled — "
                "refusing second budget effect")
        self._known[receipt_id] = True

    def is_settled(self, receipt_id: str) -> bool:
        receipt_id = _require_receipt_id(receipt_id)
        return bool(self._known.get(receipt_id))

    def known(self, receipt_id: str) -> bool:
        receipt_id = _require_receipt_id(receipt_id)
        return receipt_id in self._known

    def __len__(self) -> int:
        return len(self._order)

    def replay(self) -> Tuple[Tuple[str, bool], ...]:
        """Read-only snapshot in note order. Has no write path."""
        return tuple((rid, self._known[rid]) for rid in self._order)
