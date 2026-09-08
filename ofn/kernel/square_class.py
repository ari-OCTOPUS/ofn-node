"""Classify one non-negative exact int as zero / square / other.

pow2_class / log2_pin (other body) own exact powers of two.
prime_class / composite_pin (other body) own one-integer
zero / unit / prime / composite. even_class / odd_pin (other
body) own parity. remainder_class / leftover_pin own leftover
after division. quotient_class / divide_pin (other body) own
exact quotient. hex/width and byte/length (other bodies) own
encoding width. above/below owns a signed-height plane.

This module is the one-integer square witness: zero / square /
other. Missing value is UNKNOWN (None), not FALSE and not 0.
A measured 0 is ZERO, never UNKNOWN and never SQUARE.
A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer. Negative fails closed — a
signed value is not a square family here.

sample is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a
send and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and pow2_class.

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
SQUARE = "square"
OTHER = "other"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({ZERO, SQUARE, OTHER})

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
    """A square classifier never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A square class does not re-arm outbound."""
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
    """Structurally False. A recorded square is not an external effect."""
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


def missing_root_is_zero() -> bool:
    """Structurally False. Missing root is UNKNOWN, not 0."""
    return False


def measured_zero_is_unknown() -> bool:
    """Structurally False. A measured 0 is ZERO, never UNKNOWN."""
    return False


def measured_zero_is_square() -> bool:
    """Structurally False. A measured 0 is ZERO, never SQUARE."""
    return False


def other_is_false() -> bool:
    """Structurally False. OTHER is a family, not FALSE."""
    return False


def floor_root_is_exact() -> bool:
    """Structurally False. Only an exact square root is recorded."""
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


def _require_nonneg(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{name} must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(
            f"{name} must be a non-negative exact int: {value!r}")
    return value


def _isqrt(n: int) -> int:
    """Exact-int integer square root (floor). No float, no clock."""
    if n < 2:
        return n
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


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
    """zero / square / other, or None when missing or timed out.

    Missing value is UNKNOWN (None), not FALSE and not 0.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Value must be a
    non-negative exact int. bool is not an int here.
    A measured 0 is ZERO, never UNKNOWN and never SQUARE.
    A non-square is OTHER, never FALSE.
    Floor-of-sqrt is not an exact square.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if value is None:
        return None
    measured = _require_nonneg(value, name="value")
    if measured == 0:
        return ZERO
    root = _isqrt(measured)
    if root * root == measured:
        return SQUARE
    return OTHER


def root_of(
    value: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return the exact integer square root, or None when missing.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails
    closed. ZERO records root 0. SQUARE records the exact root.
    OTHER fails closed — a floor root is not an exact square.
    """
    family = classify_family(value, timeout=timeout)
    if family is None:
        return None
    measured = _require_nonneg(value, name="value")
    if family == ZERO:
        return 0
    if family == SQUARE:
        return _isqrt(measured)
    raise FailClosedError(
        f"other is not an exact square root: {measured!r}")


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class SquareBind:
    """One intent + family + value + root + slot.

    Frozen so a later write cannot silently retcon the recorded
    square into send_authorized. root is 0 for ZERO, the exact
    root for SQUARE, and None for OTHER (no exact root).
    """

    intent: str
    family: str
    value: int
    root: Optional[int]
    slot: str


def bind_square(
    intent: object,
    value: object,
    *,
    slot: object,
) -> SquareBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here. OTHER binds with root None — recorded, not
    granted as an exact square.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(value, timeout=False)
    if family is None:
        raise FailClosedError("value missing — UNKNOWN is not a bind")
    measured = _require_nonneg(value, name="value")
    key = _require_slot(slot)
    if family == OTHER:
        recorded_root: Optional[int] = None
    else:
        recorded_root = root_of(measured)
    return SquareBind(
        intent=klass,
        family=family,
        value=measured,
        root=recorded_root,
        slot=key,
    )


def try_bind(
    intent: object,
    value: object,
    *,
    slot: object,
) -> Optional[SquareBind]:
    """Missing intent, value, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or value is None or slot is None:
        return None
    return bind_square(intent, value, slot=slot)


def admit_square(
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
