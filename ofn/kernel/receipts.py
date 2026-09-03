"""Typed ExecutionReceipt + in-memory ReceiptIndex.

The adapter stamps a JSON canonical digest. The store indexes
EXECUTION_RECEIPT event_ids. This module is neither: a frozen typed
receipt whose identity is a hashlib digest of length-safe field hashes,
plus an append-only index that refuses a reused receipt_id bound to a
different contract.

Not wired into the run store (that file is owned by another open change).
A receipt records an in-node effect. It does not grant send_authorized,
quote_sent, or campaign_envelope_ready.

HALT stops STARTS. This index has no halt parameter: in-flight receipts
must still record so recovery does not need the owner.

Kernel purity: hashlib + dataclasses + re. No json, no clock, no I/O.
``receipt_id`` is minted at the boundary the same way ``run_id`` is —
the factory formats; it does not generate randomness.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import EXECUTION_RECEIPT, is_forbidden_effect_name

OUTCOMES = frozenset({"ok", "rejected", "failed"})
# "sent" / "authorized" / "ready" are not outcomes. Recording them here
# would collapse a receipt into a send.

RECEIPT_ID_RE = re.compile(r"^rcp-[0-9]{10,12}-[a-z0-9]{10,}$")

_SEP = "\n"

# Sealed names that must not appear as identity, tool, outcome, ref, or
# detail. Wider than the event helper so hyphen/underscore aliases die
# here too — a receipt is not a place to smuggle a send.
_SEALED_ALIASES = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED_ALIASES:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in {s.replace("-", "_") for s in _SEALED_ALIASES}:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")


def mint_receipt_id(now_epoch_s: int, rand: str) -> str:
    """Format a receipt_id from boundary-supplied time and randomness.

    The kernel formats; it does not generate. ``rand`` must be at least
    ten lowercase hex characters — os.urandom(8).hex() at the call site
    is the intended shape.
    """
    if not isinstance(now_epoch_s, int) or isinstance(now_epoch_s, bool):
        raise FailClosedError(f"now_epoch_s must be int: {now_epoch_s!r}")
    if not isinstance(rand, str):
        raise FailClosedError(f"rand must be a string: {rand!r}")
    receipt_id = f"rcp-{now_epoch_s}-{rand}"
    if not RECEIPT_ID_RE.match(receipt_id):
        raise FailClosedError(f"refusing malformed receipt_id: {receipt_id!r}")
    return receipt_id


@dataclass(frozen=True)
class ExecutionReceipt:
    """The typed contract of one EXECUTION_RECEIPT.

    ``kind`` is fixed to the spine name. A caller cannot construct a
    proposal disguised as a receipt by passing another kind.
    """

    receipt_id: str
    run_id: str
    tool: str
    outcome: str
    ts: int
    ref: Optional[str] = None
    detail: str = ""

    def __post_init__(self) -> None:
        if not RECEIPT_ID_RE.match(self.receipt_id or ""):
            raise FailClosedError(
                f"receipt_id not minted at the boundary: {self.receipt_id!r}")
        _refuse_sealed(self.receipt_id, what="receipt_id")
        if not RUN_ID_RE.match(self.run_id or ""):
            raise FailClosedError(
                f"run_id not minted at the boundary: {self.run_id!r}")
        if not isinstance(self.tool, str) or not self.tool.strip():
            raise FailClosedError(f"tool name required: {self.tool!r}")
        _refuse_sealed(self.tool, what="tool")
        if self.outcome not in OUTCOMES:
            raise FailClosedError(
                f"outcome must be one of {sorted(OUTCOMES)}: {self.outcome!r}")
        if not isinstance(self.ts, int) or isinstance(self.ts, bool):
            raise FailClosedError(f"ts must be int: {self.ts!r}")
        if self.ref is not None:
            if not isinstance(self.ref, str) or not self.ref.strip():
                raise FailClosedError(f"ref must be a non-empty id: {self.ref!r}")
            _refuse_sealed(self.ref, what="ref")
        if not isinstance(self.detail, str):
            raise FailClosedError(f"detail must be a string: {self.detail!r}")
        if self.detail:
            _refuse_sealed(self.detail, what="detail")

    @property
    def kind(self) -> str:
        """Always EXECUTION_RECEIPT. Proposal is a different kind."""
        return EXECUTION_RECEIPT

    def binding_material(self) -> str:
        """Canonical, length-safe material including receipt_id.

        Each field is hashed before join so a newline inside ``detail``
        cannot collide with the separator.
        """
        fields = (
            f"receipt_id={self.receipt_id}",
            f"run_id={self.run_id}",
            f"tool={self.tool}",
            f"outcome={self.outcome}",
            f"ts={self.ts}",
            f"ref={self.ref or ''}",
            f"detail={self.detail}",
        )
        return _SEP.join(_digest_text(f) for f in fields)

    def binding_hash(self) -> str:
        """sha256 hex of the full contract, including receipt_id."""
        return _digest_text(self.binding_material())

    def content_hash(self) -> str:
        """sha256 hex of the effect, excluding receipt_id.

        Two ids naming the same effect are a lie. Replay of the same
        id is handled by binding_hash, not this digest.
        """
        fields = (
            f"run_id={self.run_id}",
            f"tool={self.tool}",
            f"outcome={self.outcome}",
            f"ts={self.ts}",
            f"ref={self.ref or ''}",
            f"detail={self.detail}",
        )
        return _digest_text(_SEP.join(_digest_text(f) for f in fields))


def create_receipt(
    *,
    run_id: str,
    tool: str,
    outcome: str,
    now_epoch_s: int,
    rand: str,
    ref: Optional[str] = None,
    detail: str = "",
) -> ExecutionReceipt:
    """The boundary's only sanctioned constructor. Arms call this; they
    cannot inject a receipt_id because the parameter does not exist."""
    return ExecutionReceipt(
        receipt_id=mint_receipt_id(now_epoch_s, rand),
        run_id=run_id,
        tool=tool,
        outcome=outcome,
        ts=now_epoch_s,
        ref=ref,
        detail=detail,
    )


def grants_send(receipt: Optional[ExecutionReceipt] = None) -> bool:
    """A typed receipt is never a send authorization. Structurally False."""
    if receipt is not None and not isinstance(receipt, ExecutionReceipt):
        raise FailClosedError(
            f"grants_send needs ExecutionReceipt: {type(receipt)!r}")
    return False


def halt_blocks_receipt_mint() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight receipts."""
    return False


class ReceiptIndex:
    """Append-only in-memory index. Replay does not write.

    Two independent claims, two indexes:

      * ``receipt_id`` → receipt   (identity; reuse with a new contract dies)
      * ``content_hash`` → id      (effect; two names for one effect die)
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, ExecutionReceipt] = {}
        self._by_content: Dict[str, str] = {}
        self._order: List[str] = []

    def record(self, receipt: ExecutionReceipt) -> ExecutionReceipt:
        if not isinstance(receipt, ExecutionReceipt):
            raise FailClosedError(
                f"ReceiptIndex.record needs ExecutionReceipt: {type(receipt)!r}")
        rid = receipt.receipt_id
        existing = self._by_id.get(rid)
        if existing is not None:
            if existing.binding_hash() != receipt.binding_hash():
                raise FailClosedError(
                    "receipt_id reused for a different contract — "
                    "silent collapse would be a lie")
            return existing
        owner = self._by_content.get(receipt.content_hash())
        if owner is not None:
            raise FailClosedError(
                f"duplicate effect under a second receipt_id "
                f"(first={owner!r})")
        self._by_id[rid] = receipt
        self._by_content[receipt.content_hash()] = rid
        self._order.append(rid)
        return receipt

    def get(self, receipt_id: str) -> Optional[ExecutionReceipt]:
        if not isinstance(receipt_id, str) or not receipt_id.strip():
            raise FailClosedError(f"receipt_id required: {receipt_id!r}")
        return self._by_id.get(receipt_id)

    def __len__(self) -> int:
        return len(self._order)

    def replay(self) -> Tuple[ExecutionReceipt, ...]:
        """Read-only snapshot in append order. Has no write path."""
        return tuple(self._by_id[i] for i in self._order)
