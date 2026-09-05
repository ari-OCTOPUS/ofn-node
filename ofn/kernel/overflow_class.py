"""Classify used+add against capacity without granting a send.

remainder_class / leftover_pin (other body) own leftover after
integer division. quotient_class / divide_pin (other body) own
how-many-times. byte_class / length_pin (other body) own payload
length families. token_class / spend_fence (other body) own token
spend. payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the overflow witness: fits / overflow.
Missing used, add, or capacity is UNKNOWN (None), not FALSE.
A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer.

consume is a START. HALT refuses it. classify / observe
continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, remainder_class, and
byte_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

FITS = "fits"
OVERFLOW = "overflow"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({FITS, OVERFLOW})

CONSUME = "consume"
CLASSIFY = "classify"
OBSERVE = "observe"

INTENTS = frozenset({CONSUME, CLASSIFY, OBSERVE})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An overflow classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_consume() -> bool:
    """Structurally True. consume is a START; HALT refuses it."""
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
    """Structurally False. A recorded overflow is not an external effect."""
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


def carry_is_zero() -> bool:
    """Structurally False. Missing carry is UNKNOWN, not 0."""
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


def _require_used(used: object) -> int:
    if type(used) is not int:
        raise FailClosedError(f"used must be an exact int: {used!r}")
    if used < 0:
        raise FailClosedError(f"used must be >= 0: {used!r}")
    return used


def _require_add(add: object) -> int:
    if type(add) is not int:
        raise FailClosedError(f"add must be an exact int: {add!r}")
    if add < 0:
        raise FailClosedError(f"add must be >= 0: {add!r}")
    return add


def _require_capacity(capacity: object) -> int:
    if type(capacity) is not int:
        raise FailClosedError(f"capacity must be an exact int: {capacity!r}")
    if capacity < 1:
        raise FailClosedError(f"capacity must be >= 1: {capacity!r}")
    return capacity


def classify_intent(value: object) -> str:
    """consume / classify / observe or UNKNOWN.

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
    used: object,
    *,
    add: object,
    capacity: object,
    timeout: object = False,
) -> Optional[str]:
    """fits / overflow, or None when missing or timed out.

    Missing used, add, or capacity is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. used/add must be exact
    int >= 0. capacity must be exact int >= 1. bool is not an int
    here. This is addition-vs-capacity, not leftover-after-divide.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if used is None or add is None or capacity is None:
        return None
    occupied = _require_used(used)
    increment = _require_add(add)
    cap = _require_capacity(capacity)
    if occupied + increment <= cap:
        return FITS
    return OVERFLOW


def carry_of(
    used: object,
    *,
    add: object,
    capacity: object,
    timeout: object = False,
) -> Optional[int]:
    """Return max(0, used+add-capacity), or None when missing or timed out.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails closed.
    A measured fits records carry 0. Missing is not that 0.
    """
    if classify_family(
        used, add=add, capacity=capacity, timeout=timeout,
    ) is None:
        return None
    occupied = _require_used(used)
    increment = _require_add(add)
    cap = _require_capacity(capacity)
    extra = occupied + increment - cap
    if extra < 0:
        return 0
    return extra


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class OverflowBind:
    """One intent + family + carry + used + add + capacity + slot.

    Frozen so a later write cannot silently retcon the recorded
    overflow into send_authorized.
    """

    intent: str
    family: str
    carry: int
    used: int
    add: int
    capacity: int
    slot: str


def bind_overflow(
    intent: object,
    used: object,
    *,
    add: object,
    capacity: object,
    slot: object,
) -> OverflowBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(
        used, add=add, capacity=capacity, timeout=False)
    if family is None:
        raise FailClosedError(
            "used, add, or capacity missing — UNKNOWN is not a bind")
    occupied = _require_used(used)
    increment = _require_add(add)
    cap = _require_capacity(capacity)
    key = _require_slot(slot)
    extra = occupied + increment - cap
    carry = 0 if extra < 0 else extra
    return OverflowBind(
        intent=klass,
        family=family,
        carry=carry,
        used=occupied,
        add=increment,
        capacity=cap,
        slot=key,
    )


def try_bind(
    intent: object,
    used: object,
    *,
    add: object,
    capacity: object,
    slot: object,
) -> Optional[OverflowBind]:
    """Missing intent, used, add, capacity, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or used is None
        or add is None
        or capacity is None
        or slot is None
    ):
        return None
    return bind_overflow(
        intent, used, add=add, capacity=capacity, slot=slot)


def admit_overflow(
    intent: object,
    used: object,
    *,
    add: object,
    capacity: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, used, add, or capacity is UNKNOWN (None), not
    False. classify / observe continue under HALT. consume is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    Overflow family is a family, not a send, and does not invent
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
        used, add=add, capacity=capacity, timeout=False)
    if family is None:
        return None
    if klass == CONSUME:
        return not halted
    return True
