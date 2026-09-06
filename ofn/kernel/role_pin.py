"""Pin a classified kind-role onto a caller-owned run_id.

The pin records (run_id → role). Same pair is already_pinned.
A second start is second_start. Inflight or debit after close
is after_close. A second debit is second_debit. peek never writes.

A pinned start or debit is not send_authorized. Ready is not
authorized. Missing is UNKNOWN (None), not FALSE.

PROPOSAL is never execution. The pin does not mint a run_id
and does not write a ledger.

Distinct from kind_graph, typed_event, halt_ops, store_class,
receipts, and settlement. Not wired into run_store.py.
HALT stops STARTS, not this pin.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Dict, Optional

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .kind_class import (
    CLOSE,
    DEBIT,
    REJECT,
    START,
    classify_role,
    grants_send as kind_grants_send,
    proposal_is_execution,
)


def grants_send() -> bool:
    """A role pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def pin_allows_send() -> bool:
    """Structurally False. A pinned start/debit is not a send."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not filesystem immutability."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Not wired into the run store."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def _run_id(value: object) -> str:
    if type(value) is not str or not RUN_ID_RE.match(value):
        raise FailClosedError(f"run_id required: {value!r}")
    return value


class RolePin:
    """Caller-owned (run_id → role) map. Replay / peek do not write."""

    def __init__(self) -> None:
        self._pinned: Dict[str, str] = {}
        self._debit: Dict[str, bool] = {}

    def peek(self, run_id: object) -> Optional[str]:
        """Read without writing. Missing run is None, not FALSE."""
        rid = _run_id(run_id)
        return self._pinned.get(rid)

    def pin(
        self,
        run_id: object,
        kind: object,
        *,
        timeout: object = False,
    ) -> str:
        """Record a classified role. Second same pair is already_pinned."""
        rid = _run_id(run_id)
        labeled = classify_role(kind, timeout=timeout)
        if labeled is None:
            raise FailClosedError(
                "kind missing or timed out — UNKNOWN is not a pin")
        if proposal_is_execution() or kind_grants_send():
            raise FailClosedError("kind/pin drifted into execution or send")
        prior = self._pinned.get(rid)
        if prior is None:
            self._pinned[rid] = labeled
            if labeled == DEBIT:
                self._debit[rid] = True
            return "pinned"
        if prior == CLOSE and labeled not in {CLOSE, REJECT}:
            raise FailClosedError(
                f"after_close run={rid!r} have={prior!r} got={labeled!r}")
        if labeled == START and prior == START:
            raise FailClosedError(
                f"second_start run={rid!r}")
        if labeled == DEBIT:
            if self._debit.get(rid):
                raise FailClosedError(
                    f"second_debit run={rid!r} — one verdict one effect")
            self._debit[rid] = True
            return "pinned"
        if prior == labeled:
            return "already_pinned"
        self._pinned[rid] = labeled
        return "pinned"

    def try_pin(
        self,
        run_id: object,
        kind: object,
        *,
        timeout: object = False,
    ) -> Optional[str]:
        """Missing kind or timeout is UNKNOWN (None). Present-but-bad fails closed."""
        if kind is None or timeout is True:
            return None
        return self.pin(run_id, kind, timeout=timeout)


def pin_allows_start_only(label: object) -> bool:
    """True only for the start label. Still does not grant a send."""
    if label is None:
        return False
    if type(label) is not str:
        raise FailClosedError(f"label must be a str or None: {label!r}")
    if kind_grants_send() or grants_send():
        raise FailClosedError("kind/pin drifted into granting send")
    return label == START
