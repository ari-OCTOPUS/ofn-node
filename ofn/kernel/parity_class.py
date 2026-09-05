"""Classify even vs odd count parity without granting a send.

overflow_class / carry_pin (other body, #205) own used+add vs
capacity. underflow_class / borrow_pin (other body, #207) own
subtract underflow. remainder_class / leftover_pin (other body,
#204) own leftover after integer division. modulus_class /
wrap_pin (unpublished / other body) own wrap-to-modulus.
capacity_class / room_pin (other body, #209) own occupancy vs
limit. digest_class / fold_pin (other body, #152) own hash fold.
payload_bound (unpublished / other body) is a different module
and is not recreated here.

This module is the parity witness: even / odd. There is no
modulus operand and no leftover. Missing count is UNKNOWN
(None), not FALSE. A present-but-wrong type fails closed.
Timeout is UNKNOWN and does not prove a writer.

record is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, receipts, dedup, and remainder_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

EVEN = "even"
ODD = "odd"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EVEN, ODD})

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
    """A parity classifier never authorizes a send. Structurally False."""
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
    """Structurally False. A recorded parity is not an external effect."""
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


def even_is_authorized() -> bool:
    """Structurally False. even is a family, not send_authorized."""
    return False


def odd_is_false() -> bool:
    """Structurally False. odd is a family, not FALSE."""
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


def _require_count(count: object) -> int:
    if type(count) is not int:
        raise FailClosedError(f"count must be an exact int: {count!r}")
    if count < 0:
        raise FailClosedError(f"count must be >= 0: {count!r}")
    return count


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


def classify_family(
    count: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """even / odd, or None when missing or timed out.

    Missing count is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. count must be exact int >= 0.
    bool is not an int here. This is even/odd of one count, not
    leftover-after-divide and not wrap-to-modulus.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if count is None:
        return None
    n = _require_count(count)
    if n % 2 == 0:
        return EVEN
    return ODD


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class ParityBind:
    """One intent + family + count + slot.

    Frozen so a later write cannot silently retcon the recorded
    parity into send_authorized.
    """

    intent: str
    family: str
    count: int
    slot: str


def bind_parity(
    intent: object,
    count: object,
    *,
    slot: object,
) -> ParityBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(count, timeout=False)
    if family is None:
        raise FailClosedError(
            "count missing — UNKNOWN is not a bind")
    n = _require_count(count)
    key = _require_slot(slot)
    return ParityBind(
        intent=klass,
        family=family,
        count=n,
        slot=key,
    )


def try_bind(
    intent: object,
    count: object,
    *,
    slot: object,
) -> Optional[ParityBind]:
    """Missing intent, count, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or count is None or slot is None:
        return None
    return bind_parity(intent, count, slot=slot)


def admit_parity(
    intent: object,
    count: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or count is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. record is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    Parity family is a family, not a send, and does not invent
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
    family = classify_family(count, timeout=False)
    if family is None:
        return None
    if klass == RECORD:
        return not halted
    return True
