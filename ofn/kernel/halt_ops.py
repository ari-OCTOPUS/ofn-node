"""Layer-3 operation classifier — HALT stops STARTS, not recovery.

``kernel.halt.is_halted`` answers "is the switch on?". This module
answers the next question: given that verdict, which operations may
proceed? The two are independent witnesses. A flag that is on does
not, by itself, say what is forbidden; an operation name that is
unknown is not treated as allowed.

Closed sets:

  * START_OPS     — refused while halted (new work)
  * IN_FLIGHT_OPS — allowed while halted (owner-absent recovery)
  * NEVER_OPS     — refused always (this module never grants a resend
                    or an external send)

``send_authorized``, ``quote_sent``, and ``campaign_envelope_ready``
are not operations here. Passing one as ``op`` fails closed — ready
is not authorized, and a rename is not a grant.

Not wired into ``run_gate`` or ``run_store`` (those files are owned
by open changes). Callers import the predicate.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import FrozenSet

from .errors import FailClosedError
from .events import FORBIDDEN_EFFECT_KINDS, is_forbidden_effect_name

START_RUN = "start_run"
ISSUE_CLAIM = "issue_claim"
APPEND_IN_FLIGHT = "append_in_flight"
CLOSE_IN_FLIGHT = "close_in_flight"
HOLD_IN_FLIGHT = "hold_in_flight"
SETTLE_IN_FLIGHT = "settle_in_flight"
DEDUP_IN_FLIGHT = "dedup_in_flight"
RECORD_REJECTION = "record_rejection"
RECOVER_AFTER_RESTART = "recover_after_restart"
RESEND = "resend"

START_OPS: FrozenSet[str] = frozenset({START_RUN, ISSUE_CLAIM})
IN_FLIGHT_OPS: FrozenSet[str] = frozenset({
    APPEND_IN_FLIGHT,
    CLOSE_IN_FLIGHT,
    HOLD_IN_FLIGHT,
    SETTLE_IN_FLIGHT,
    DEDUP_IN_FLIGHT,
    RECORD_REJECTION,
    RECOVER_AFTER_RESTART,
})
NEVER_OPS: FrozenSet[str] = frozenset({RESEND})

KNOWN_OPS: FrozenSet[str] = START_OPS | IN_FLIGHT_OPS | NEVER_OPS

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An operation classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_inflight() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight close."""
    return False


def _refuse_sealed(value: str, *, what: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} required: {value!r}")
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")
    if value in FORBIDDEN_EFFECT_KINDS:
        raise FailClosedError(
            f"{what} is a sealed effect kind: {value!r}")


def _require_op(op: str) -> str:
    _refuse_sealed(op, what="op")
    if op not in KNOWN_OPS:
        raise FailClosedError(f"unknown operation: {op!r}")
    return op


def _require_halted(halted: object) -> bool:
    if type(halted) is not bool:
        raise FailClosedError(
            f"halted must be a bool (unknown is not False): {halted!r}")
    return halted


def classify(op: str) -> str:
    """Return the bucket for a known operation. Never 'allowed' or 'send'."""
    op = _require_op(op)
    if op in START_OPS:
        return "start"
    if op in IN_FLIGHT_OPS:
        return "in_flight"
    return "never"


def may_proceed(halted: bool, op: str) -> bool:
    """May this operation proceed under the given halt verdict?

    START ops: only while not halted.
    IN_FLIGHT ops: always (recovery must not need the owner).
    NEVER ops (resend): always False — structurally, not a missing flag.
    Sealed send/ready names: FailClosedError, not False.
    Unknown ops: FailClosedError (UNKNOWN is not allowed).
    """
    halted = _require_halted(halted)
    op = _require_op(op)
    if op in NEVER_OPS:
        return False
    if op in START_OPS:
        return not halted
    return True
