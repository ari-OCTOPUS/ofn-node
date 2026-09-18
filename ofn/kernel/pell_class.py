"""Classify one non-negative exact int as zero / pell / other.

cube_class / cubic_pin (other body) own signed cubes.
square_class / root_pin (other body) own non-negative squares.
catalan_class / nest_pin (other body) own Catalan numbers.
fibonacci_class / sequence_pin (other body) own Fibonacci
numbers. lucas_class / companion_pin (other body) own Lucas
numbers. triangular_class / series_pin (other body) own
triangular numbers. remainder_class / leftover_pin own
leftover after division. stride_class / step_pin (other
body) own walk-distance stride.

This module is the one-integer Pell witness: zero / pell /
other. P_0 = 0, P_1 = 1, P_n = 2 P_{n-1} + P_{n-2}. Missing
value is UNKNOWN (None), not FALSE and not 0. A measured 0
is ZERO, never UNKNOWN and never PELL. A measured 1 is
PELL (P_1 = 1), never UNKNOWN; the recorded index is 1.
A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer. Negatives fail closed (Pell
numbers used here are non-negative).

Walk identity (Cassini analog) is checked on every step:
P_{n+1} P_{n-1} - P_n^2 = (-1)^n. Disagreement fail-closes.
No float. No closed form.

sample is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a
send and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and catalan_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

ZERO = "zero"
PELL = "pell"
OTHER = "other"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({ZERO, PELL, OTHER})

SAMPLE = "sample"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({SAMPLE, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A Pell classifier never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A Pell class does not re-arm outbound."""
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


def halt_blocks_sample() -> bool:
    """Structurally True. sample is a START; HALT refuses it."""
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
    """Structurally False. A recorded Pell is not an external effect."""
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


def missing_index_is_zero() -> bool:
    """Structurally False. Missing index is UNKNOWN, not 0."""
    return False


def measured_zero_is_unknown() -> bool:
    """Structurally False. A measured 0 is ZERO, never UNKNOWN."""
    return False


def measured_zero_is_pell() -> bool:
    """Structurally False. A measured 0 is ZERO, never PELL."""
    return False


def measured_one_is_unknown() -> bool:
    """Structurally False. A measured 1 is PELL, never UNKNOWN."""
    return False


def other_is_false() -> bool:
    """Structurally False. OTHER is a family, not FALSE."""
    return False


def fibonacci_is_pell() -> bool:
    """Structurally False. Fibonacci numbers are a different module."""
    return False


def catalan_is_pell() -> bool:
    """Structurally False. Catalan numbers are a different module."""
    return False


def lucas_is_pell() -> bool:
    """Structurally False. Lucas numbers are a different module."""
    return False


def stride_is_pell() -> bool:
    """Structurally False. Stride/step is a different module."""
    return False


def negative_is_other() -> bool:
    """Structurally False. A negative fails closed, not OTHER."""
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


def _require_nonneg_int(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{name} must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(f"{name} must be >= 0: {value!r}")
    return value


def _pell_index(value: int) -> Optional[int]:
    """Smallest n>=1 with P_n == value, or None if not Pell.

    Walks P_{n+1} = 2 P_n + P_{n-1} with exact integer
    arithmetic. Cassini analog P_{n+1} P_{n-1} - P_n^2 =
    (-1)^n is checked on every step. Disagreement
    fail-closes. No float, no clock. P_0 = 0 is not an
    index here (ZERO family).
    """
    if value < 1:
        return None
    prev, current = 0, 1
    n = 1
    while current < value:
        nxt = 2 * current + prev
        if nxt * prev - current * current != (-1) ** n:
            raise FailClosedError(
                f"pell walk identity disagreed at n={n}: "
                f"P={current} prev={prev} next={nxt}")
        prev, current = current, nxt
        n += 1
    if current == value:
        return n
    return None


def classify_intent(value: object) -> str:
    """sample / classify / observe / inspect or UNKNOWN.

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
    value: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """zero / pell / other, or None when missing or timed out.

    Missing value is UNKNOWN (None), not FALSE and not 0.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Value must be an
    exact int >= 0. bool is not an int here. Negatives fail
    closed. A measured 0 is ZERO, never UNKNOWN and never
    PELL. A measured 1 is PELL, never UNKNOWN. A
    non-Pell is OTHER, never FALSE.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if value is None:
        return None
    measured = _require_nonneg_int(value, name="value")
    if measured == 0:
        return ZERO
    if _pell_index(measured) is not None:
        return PELL
    return OTHER


def index_of(
    value: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return the Pell index n>=1, or None when missing.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails
    closed. ZERO records no index (None). PELL records the
    smallest n>=1 with P_n == value (so 1 → 1). OTHER fails
    closed — a nearby integer is not a Pell number.
    """
    family = classify_family(value, timeout=timeout)
    if family is None:
        return None
    if family == ZERO:
        return None
    measured = _require_nonneg_int(value, name="value")
    if family == PELL:
        found = _pell_index(measured)
        if found is None:
            raise FailClosedError(
                f"pell family without index: {measured!r}")
        return found
    raise FailClosedError(
        f"other is not an exact Pell index: {measured!r}")


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class PellBind:
    """One intent + family + value + index + slot.

    Frozen so a later write cannot silently retcon the recorded
    Pell into send_authorized. index is n>=1 for PELL, and
    None for ZERO and OTHER (no Pell index).
    """

    intent: str
    family: str
    value: int
    index: Optional[int]
    slot: str


def bind_pell(
    intent: object,
    value: object,
    *,
    slot: object,
) -> PellBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here. OTHER and ZERO bind with index None —
    recorded, not granted as an exact Pell sample.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(value, timeout=False)
    if family is None:
        raise FailClosedError("value missing — UNKNOWN is not a bind")
    measured = _require_nonneg_int(value, name="value")
    key = _require_slot(slot)
    if family == PELL:
        recorded_index = index_of(measured)
    else:
        recorded_index = None
    return PellBind(
        intent=klass,
        family=family,
        value=measured,
        index=recorded_index,
        slot=key,
    )


def try_bind(
    intent: object,
    value: object,
    *,
    slot: object,
) -> Optional[PellBind]:
    """Missing intent, value, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or value is None or slot is None:
        return None
    return bind_pell(intent, value, slot=slot)


def admit_pell(
    intent: object,
    value: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or value is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. sample is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    OTHER is a family, not a send, and does not invent False
    for classify / observe / inspect.
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
    family = classify_family(value, timeout=False)
    if family is None:
        return None
    if klass == SAMPLE:
        return not halted
    return True
