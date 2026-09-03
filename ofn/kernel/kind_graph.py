"""kind_graph — which spine kinds may follow which, inside one run.

Typed events are a closed vocabulary. The store checks membership.
This module is the kernel-pure second witness for *succession*:

  * a run begins with RUN_CREATED and no other kind
  * progress kinds may follow a start or another progress kind
  * RUN_CLOSED is terminal — nothing follows
  * RUN_REJECTED is a refusal name, not a run-graph node
  * BUDGET_DEBIT requires a prior EXECUTION_RECEIPT on that run
  * PROPOSAL_CREATED is never EXECUTION_RECEIPT (rename is not a fact)
  * sealed ready/authorized/sent names are not nodes

Not wired into the run store (that file is owned by an open change).
Walking the graph is not send_authorized, quote_sent, or
campaign_envelope_ready.

HALT stops STARTS. This graph has no halt parameter: in-flight
succession must still be named so recovery does not need the owner.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Optional

from .errors import FailClosedError
from .events import (
    BUDGET_DEBIT,
    CLAIM_CREATED,
    EVENT_KINDS,
    EXECUTION_RECEIPT,
    FORBIDDEN_EFFECT_KINDS,
    POLICY_DECISION,
    PROPOSAL_CREATED,
    RUN_CLOSED,
    RUN_CREATED,
    RUN_REJECTED,
    TOOL_INVOKED,
    is_forbidden_effect_name,
)

START = "START"
PROPOSAL = "PROPOSAL"
EXECUTION = "EXECUTION"
SETTLEMENT = "SETTLEMENT"
PROGRESS = "PROGRESS"
TERMINAL = "TERMINAL"
REFUSAL = "REFUSAL"
SEALED = "SEALED"
UNKNOWN = "UNKNOWN"

CLASSES = frozenset({
    START, PROPOSAL, EXECUTION, SETTLEMENT, PROGRESS, TERMINAL, REFUSAL,
    SEALED, UNKNOWN,
})

PROGRESS_KINDS: FrozenSet[str] = frozenset({
    CLAIM_CREATED,
    PROPOSAL_CREATED,
    POLICY_DECISION,
    TOOL_INVOKED,
    EXECUTION_RECEIPT,
    BUDGET_DEBIT,
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A succession graph never authorizes a send. Structurally False."""
    return False


def halt_blocks_kind_graph() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight succession."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal is not an execution."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready is not a rename of authorized."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. An unknown kind is UNKNOWN, not FALSE."""
    return False


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")


def _require_run_id(run_id: object) -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise FailClosedError(f"run_id required: {run_id!r}")
    _refuse_sealed(run_id, what="run_id")
    return run_id


def classify_kind(kind: object) -> str:
    """Name the class of a kind. Unknown is UNKNOWN, not FALSE.

    Sealed ready/authorized/sent names are SEALED — they are not
    progress, and they are not a missing classification.
    """
    if not isinstance(kind, str) or not kind.strip():
        raise FailClosedError(f"kind required: {kind!r}")
    folded = kind.strip().lower().replace("-", "_")
    if (is_forbidden_effect_name(kind)
            or kind in FORBIDDEN_EFFECT_KINDS
            or kind.strip().lower() in _SEALED
            or folded in {s.replace("-", "_") for s in _SEALED}):
        return SEALED
    if kind == RUN_CREATED:
        return START
    if kind == PROPOSAL_CREATED:
        return PROPOSAL
    if kind == EXECUTION_RECEIPT:
        return EXECUTION
    if kind == BUDGET_DEBIT:
        return SETTLEMENT
    if kind == RUN_CLOSED:
        return TERMINAL
    if kind == RUN_REJECTED:
        return REFUSAL
    if kind in PROGRESS_KINDS:
        return PROGRESS
    if kind in EVENT_KINDS:
        return PROGRESS
    return UNKNOWN


def may_follow(prev: Optional[str], nxt: str) -> bool:
    """True when ``nxt`` may follow ``prev`` inside one run.

    ``prev is None`` means the run has no events yet — only
    RUN_CREATED may start. Sealed / refusal / unknown kinds are
    never nodes. Does not consult a receipt index; BUDGET_DEBIT
    succession still needs ``KindGraph`` for the receipt pin.
    """
    nxt_class = classify_kind(nxt)
    if nxt_class in (SEALED, REFUSAL, UNKNOWN):
        return False
    if prev is None:
        return nxt == RUN_CREATED
    prev_class = classify_kind(prev)
    if prev_class in (SEALED, REFUSAL, UNKNOWN, TERMINAL):
        return False
    if nxt == RUN_CREATED:
        return False
    if nxt == RUN_CLOSED:
        return prev_class in (START, PROPOSAL, EXECUTION, SETTLEMENT, PROGRESS)
    if nxt_class in (PROPOSAL, EXECUTION, SETTLEMENT, PROGRESS):
        return prev_class in (START, PROPOSAL, EXECUTION, SETTLEMENT, PROGRESS)
    return False


class KindGraph:
    """Append-only per-run last-kind cursor. Replay does not write.

    Two independent claims:

      * first accept for a run must be RUN_CREATED
      * BUDGET_DEBIT requires a prior EXECUTION_RECEIPT on that run
    """

    def __init__(self) -> None:
        self._last: Dict[str, str] = {}
        self._receipt: Dict[str, bool] = {}
        self._closed: Dict[str, bool] = {}
        self._count: Dict[str, int] = {}

    def last(self, run_id: str) -> Optional[str]:
        """Last accepted kind, or None if this run has no prior event.

        None is UNKNOWN, not a fabricated RUN_CREATED.
        """
        run_id = _require_run_id(run_id)
        return self._last.get(run_id)

    def saw_receipt(self, run_id: str) -> bool:
        run_id = _require_run_id(run_id)
        return self._receipt.get(run_id, False)

    def is_closed(self, run_id: str) -> bool:
        run_id = _require_run_id(run_id)
        return self._closed.get(run_id, False)

    def accepted_count(self, run_id: str) -> int:
        run_id = _require_run_id(run_id)
        return self._count.get(run_id, 0)

    def accept(self, run_id: str, kind: str) -> str:
        run_id = _require_run_id(run_id)
        klass = classify_kind(kind)
        if klass == SEALED:
            raise FailClosedError(
                f"kind names a sealed send/ready state: {kind!r}")
        if klass == REFUSAL:
            raise FailClosedError(
                "RUN_REJECTED is a refusal record, not a run-graph node")
        if klass == UNKNOWN:
            raise FailClosedError(f"unknown event kind: {kind!r}")
        prior = self._last.get(run_id)
        if not may_follow(prior, kind):
            raise FailClosedError(
                f"kind {kind!r} may not follow {prior!r} on {run_id!r}")
        if kind == BUDGET_DEBIT and not self._receipt.get(run_id, False):
            raise FailClosedError(
                f"BUDGET_DEBIT requires a prior EXECUTION_RECEIPT on {run_id!r}")
        self._last[run_id] = kind
        self._count[run_id] = self._count.get(run_id, 0) + 1
        if kind == EXECUTION_RECEIPT:
            self._receipt[run_id] = True
        if kind == RUN_CLOSED:
            self._closed[run_id] = True
        return kind

    def peek_would_accept(self, run_id: object, kind: object) -> bool:
        """True only when ``accept`` would succeed. Does not write."""
        if not isinstance(run_id, str) or not run_id.strip():
            return False
        folded = run_id.strip().lower().replace("-", "_")
        if (is_forbidden_effect_name(run_id)
                or run_id.strip().lower() in _SEALED
                or folded in {s.replace("-", "_") for s in _SEALED}):
            return False
        if not isinstance(kind, str) or not kind.strip():
            return False
        try:
            klass = classify_kind(kind)
        except FailClosedError:
            return False
        if klass in (SEALED, REFUSAL, UNKNOWN):
            return False
        prior = self._last.get(run_id)
        if not may_follow(prior, kind):
            return False
        if kind == BUDGET_DEBIT and not self._receipt.get(run_id, False):
            return False
        return True
