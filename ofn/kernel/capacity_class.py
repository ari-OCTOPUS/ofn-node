"""Classify used vs limit remaining room without granting a send.

overflow_class / carry_pin (other body, #205) own used+add vs
capacity (fits / overflow + carry). underflow_class / borrow_pin
(other body, #207) own subtract underflow. remainder_class /
leftover_pin (other body, #204) own leftover after integer
division. saturation_class / clamp_pin (unpublished / other body)
own clamp-to-bound. token_class / spend_fence (other body) own
token spend. payload_bound (unpublished / other body) is a
different module and is not recreated here.

This module is the occupancy witness: empty / has_room / full /
over_cap. There is no add operand. Missing used or limit is
UNKNOWN (None), not FALSE. A present-but-wrong type fails closed.
Timeout is UNKNOWN and does not prove a writer. Remaining room
on over_cap is UNKNOWN (None), not a negative and not 0.

reserve is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, overflow_class, and quota.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

EMPTY = "empty"
HAS_ROOM = "has_room"
FULL = "full"
OVER_CAP = "over_cap"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EMPTY, HAS_ROOM, FULL, OVER_CAP})

RESERVE = "reserve"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({RESERVE, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A capacity classifier never authorizes a send. Structurally False."""
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


def halt_blocks_reserve() -> bool:
    """Structurally True. reserve is a START; HALT refuses it."""
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
    """Structurally False. A recorded occupancy is not an external effect."""
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


def room_is_zero() -> bool:
    """Structurally False. Missing remaining room is UNKNOWN, not 0."""
    return False


def over_cap_is_negative() -> bool:
    """Structurally False. over_cap remaining is UNKNOWN, not a debit."""
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


def _require_limit(limit: object) -> int:
    if type(limit) is not int:
        raise FailClosedError(f"limit must be an exact int: {limit!r}")
    if limit < 1:
        raise FailClosedError(f"limit must be >= 1: {limit!r}")
    return limit


def classify_intent(value: object) -> str:
    """reserve / classify / observe / inspect or UNKNOWN.

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
    limit: object,
    timeout: object = False,
) -> Optional[str]:
    """empty / has_room / full / over_cap, or None when missing or timed out.

    Missing used or limit is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. used must be exact int >= 0.
    limit must be exact int >= 1. bool is not an int here.
    This is occupancy-vs-limit, not used+add overflow and not leftover.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if used is None or limit is None:
        return None
    occupied = _require_used(used)
    cap = _require_limit(limit)
    if occupied == 0:
        return EMPTY
    if occupied < cap:
        return HAS_ROOM
    if occupied == cap:
        return FULL
    return OVER_CAP


def room_of(
    used: object,
    *,
    limit: object,
    timeout: object = False,
) -> Optional[int]:
    """Return remaining room, or None when missing, timed out, or over_cap.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails closed.
    empty / has_room record limit-used. full records 0. over_cap
    remaining is UNKNOWN (None), not a negative borrow.
    """
    family = classify_family(used, limit=limit, timeout=timeout)
    if family is None:
        return None
    if family == OVER_CAP:
        return None
    occupied = _require_used(used)
    cap = _require_limit(limit)
    remaining = cap - occupied
    if remaining < 0:
        raise FailClosedError(
            f"room drifted negative: used={occupied!r} limit={cap!r}")
    return remaining


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class CapacityBind:
    """One intent + family + room + used + limit + slot.

    Frozen so a later write cannot silently retcon the recorded
    occupancy into send_authorized. room is None only on over_cap.
    """

    intent: str
    family: str
    room: Optional[int]
    used: int
    limit: int
    slot: str


def bind_capacity(
    intent: object,
    used: object,
    *,
    limit: object,
    slot: object,
) -> CapacityBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(used, limit=limit, timeout=False)
    if family is None:
        raise FailClosedError(
            "used or limit missing — UNKNOWN is not a bind")
    occupied = _require_used(used)
    cap = _require_limit(limit)
    key = _require_slot(slot)
    remaining = room_of(occupied, limit=cap, timeout=False)
    return CapacityBind(
        intent=klass,
        family=family,
        room=remaining,
        used=occupied,
        limit=cap,
        slot=key,
    )


def try_bind(
    intent: object,
    used: object,
    *,
    limit: object,
    slot: object,
) -> Optional[CapacityBind]:
    """Missing intent, used, limit, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or used is None or limit is None or slot is None:
        return None
    return bind_capacity(intent, used, limit=limit, slot=slot)


def admit_capacity(
    intent: object,
    used: object,
    *,
    limit: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, used, or limit is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. reserve is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    Occupancy family is a family, not a send, and does not invent
    False for classify / observe / inspect.
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
    family = classify_family(used, limit=limit, timeout=False)
    if family is None:
        return None
    if klass == RESERVE:
        return not halted
    return True
