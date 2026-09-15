"""Classify unsigned subtraction that would go below a floor.

overflow_class / carry_pin (other body, PR #205) own addition
that would exceed a ceiling. remainder_class / leftover_pin
(other body) own leftover after divide. quotient_class (other
body, unpublished) owns divide. Those modules are not
recreated here.

This module is the floor-subtraction witness: exact /
underflow / wrap. Missing minuend or subtrahend is UNKNOWN
(None), not FALSE. A present-but-wrong type fails closed.
Timeout is UNKNOWN and does not prove a writer.

measure is a START. HALT refuses it. classify / observe
continue under HALT. Classification never grants a send and
never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, token_ceiling, seq, campaign_bind, send_fence,
byte_class, and unpublished payload_bound.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

EXACT = "exact"
UNDERFLOW = "underflow"
WRAP = "wrap"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EXACT, UNDERFLOW, WRAP})

MEASURE = "measure"
CLASSIFY = "classify"
OBSERVE = "observe"

INTENTS = frozenset({MEASURE, CLASSIFY, OBSERVE})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An underflow classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_measure() -> bool:
    """Structurally True. measure is a START; HALT refuses it."""
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
    """Structurally False. A recorded difference is not an external effect."""
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


def _require_nonneg_int(value: object, *, what: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{what} must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(f"{what} must be >= 0: {value!r}")
    return value


def _require_wrap_flag(value: object) -> bool:
    if type(value) is not bool:
        raise FailClosedError(f"wrap_requested must be an exact bool: {value!r}")
    return value


def classify_intent(value: object) -> str:
    """measure / classify / observe or UNKNOWN.

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


def classify_family(
    minuend: object,
    subtrahend: object,
    *,
    floor: object,
    wrap_requested: object = False,
    timeout: object = False,
) -> Optional[str]:
    """exact / underflow / wrap, or None when missing or timed out.

    Missing minuend or subtrahend is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. floor / operands must be
    exact int >= 0. bool is not an int here.
    wrap_requested is exact bool. When True and the raw difference
    would go below floor, the family is wrap — recorded, not a send.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    low = _require_nonneg_int(floor, what="floor")
    wrap = _require_wrap_flag(wrap_requested)
    if minuend is None or subtrahend is None:
        return None
    left = _require_nonneg_int(minuend, what="minuend")
    right = _require_nonneg_int(subtrahend, what="subtrahend")
    if left - right >= low:
        return EXACT
    if wrap:
        return WRAP
    return UNDERFLOW


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class UnderflowBind:
    """One intent + family + operands + floor + wrap + slot.

    Frozen so a later write cannot silently retcon the recorded
    difference into send_authorized.
    """

    intent: str
    family: str
    minuend: int
    subtrahend: int
    floor: int
    wrap_requested: bool
    slot: str


def bind_sub(
    intent: object,
    minuend: object,
    subtrahend: object,
    *,
    floor: object,
    slot: object,
    wrap_requested: object = False,
) -> UnderflowBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(
        minuend, subtrahend, floor=floor,
        wrap_requested=wrap_requested, timeout=False)
    if family is None:
        raise FailClosedError("operand missing — UNKNOWN is not a bind")
    left = _require_nonneg_int(minuend, what="minuend")
    right = _require_nonneg_int(subtrahend, what="subtrahend")
    low = _require_nonneg_int(floor, what="floor")
    wrap = _require_wrap_flag(wrap_requested)
    key = _require_slot(slot)
    return UnderflowBind(
        intent=klass,
        family=family,
        minuend=left,
        subtrahend=right,
        floor=low,
        wrap_requested=wrap,
        slot=key,
    )


def try_bind(
    intent: object,
    minuend: object,
    subtrahend: object,
    *,
    floor: object,
    slot: object,
    wrap_requested: object = False,
) -> Optional[UnderflowBind]:
    """Missing intent, operand, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or minuend is None or subtrahend is None or slot is None:
        return None
    return bind_sub(
        intent, minuend, subtrahend, floor=floor, slot=slot,
        wrap_requested=wrap_requested)


def admit_sub(
    intent: object,
    minuend: object,
    subtrahend: object,
    *,
    floor: object,
    wrap_requested: object = False,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or operand is UNKNOWN (None), not False.
    classify / observe continue under HALT. measure is refused
    when halted. Timeout is UNKNOWN (None) and does not prove
    a writer. A send name never reaches True — it fails closed
    at classify. halted / timeout must be exact bools.
    underflow / wrap are families, not a send, and do not invent
    False for classify / observe.
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
    family = classify_family(
        minuend, subtrahend, floor=floor,
        wrap_requested=wrap_requested, timeout=False)
    if family is None:
        return None
    if klass == MEASURE:
        return not halted
    return True
