"""Classify a vote threshold without granting a send.

capacity_class / room_pin (other body, #209) own occupancy vs
limit (how full a bucket is). approval_class / independent_pin
(other body, #176) own reviewer identity vs author. census_class
(#124) owns worktree census. slot_class / occupy_pin (other body,
#165) own run-slot occupy. lease_class / renew_pin (other body,
#216) own timed leases. parity_class / check_pin (#210) own
even/odd of one count.

This module is the quorum witness: votes_present vs
votes_required. QUORUM means the threshold is met. SHORT means
it is not. There is no leftover, no room remaining, and no
reviewer identity. Missing either count is UNKNOWN (None), not
FALSE. A present-but-wrong type fails closed. required < 1
fails closed — lowering the required count does not satisfy.
Timeout is UNKNOWN and does not prove a writer.

record is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a seat.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, receipts, dedup, and capacity_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

QUORUM = "quorum"
SHORT = "short"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({QUORUM, SHORT})

RECORD = "record"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({RECORD, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A quorum classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_inspect() -> bool:
    """Structurally False. inspect continues under HALT."""
    return False


def halt_blocks_record() -> bool:
    """Structurally True. record is a START; HALT refuses it."""
    return True


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classify is not filesystem immutability."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A recorded quorum is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This classifies."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return UNKNOWN


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def quorum_is_authorized() -> bool:
    """Structurally False. quorum is a family, not send_authorized."""
    return False


def short_is_false() -> bool:
    """Structurally False. short is a family, not FALSE."""
    return False


def zero_required_satisfies() -> bool:
    """Structurally False. required < 1 fails closed."""
    return False


def lowering_required_satisfies() -> bool:
    """Structurally False. Cutting required-votes does not satisfy."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {_fold(s) for s in _SEALED}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "ready is not authorized")


def _require_present(present: object) -> int:
    if type(present) is not int:
        raise FailClosedError(f"present must be an exact int: {present!r}")
    if present < 0:
        raise FailClosedError(f"present must be >= 0: {present!r}")
    return present


def _require_required(required: object) -> int:
    if type(required) is not int:
        raise FailClosedError(f"required must be an exact int: {required!r}")
    if required < 1:
        raise FailClosedError(
            f"required must be >= 1 — lowering required does not "
            f"satisfy: {required!r}")
    return required


def classify_intent(value: object) -> str:
    """record / classify / observe / inspect or UNKNOWN.

    None → UNKNOWN (no witness). bool/int/float/bytes fail closed.
    Empty / unknown / sealed names fail closed. UNKNOWN is not FALSE.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"intent must be a str or None: {value!r}")
    _refuse_sealed(value, what="intent")
    text = value.strip()
    if not text:
        raise FailClosedError("intent is empty")
    folded = _fold(text)
    if folded in INTENTS:
        return folded
    raise FailClosedError(
        f"unknown intent is not a refusal and not a grant: {value!r}")


def classify_threshold(
    present: object,
    required: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """quorum / short, or None when missing or timed out.

    Missing present or required is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. present must be exact
    int >= 0. required must be exact int >= 1. bool is not an
    int here. This is a decision threshold, not occupancy vs
    limit and not even/odd of one count.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if present is None or required is None:
        return None
    have = _require_present(present)
    need = _require_required(required)
    if have >= need:
        return QUORUM
    return SHORT


def _require_seat(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"seat must be a str: {value!r}")
    _refuse_sealed(value, what="seat")
    text = value.strip()
    if not text:
        raise FailClosedError("seat is empty")
    return text


@dataclass(frozen=True)
class QuorumBind:
    """One intent + family + present + required + seat.

    Frozen so a later write cannot silently retcon the recorded
    threshold into send_authorized.
    """

    intent: str
    family: str
    present: int
    required: int
    seat: str


def bind_quorum(
    intent: object,
    present: object,
    required: object,
    *,
    seat: object,
) -> QuorumBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_threshold(present, required, timeout=False)
    if family is None:
        raise FailClosedError(
            "present or required missing — UNKNOWN is not a bind")
    have = _require_present(present)
    need = _require_required(required)
    key = _require_seat(seat)
    return QuorumBind(
        intent=klass,
        family=family,
        present=have,
        required=need,
        seat=key,
    )


def try_bind(
    intent: object,
    present: object,
    required: object,
    *,
    seat: object,
) -> Optional[QuorumBind]:
    """Missing intent, present, required, or seat is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or present is None
        or required is None
        or seat is None
    ):
        return None
    return bind_quorum(intent, present, required, seat=seat)


def admit_quorum(
    intent: object,
    present: object,
    required: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, present, or required is UNKNOWN (None), not
    False. classify / observe / inspect continue under HALT.
    record is refused when halted. Timeout is UNKNOWN (None) and
    does not prove a writer. A send name never reaches True — it
    fails closed at classify. halted / timeout must be exact
    bools. Quorum family is a family, not a send, and does not
    invent False for classify / observe / inspect.
    """
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timeout) is not bool:
        raise FailClosedError(f"timeout must be an exact bool: {timeout!r}")
    if timeout:
        return None
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        return None
    family = classify_threshold(present, required, timeout=False)
    if family is None:
        return None
    if klass == RECORD:
        return not halted
    return True
