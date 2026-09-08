"""Classify one positive exact int by the Möbius μ witness.

cube_class / cubic_pin (other body) own signed cubes.
square_class / root_pin (other body) own non-negative squares.
prime_class / composite_pin (other body) own one-integer
zero / unit / prime / composite. coprime_class / common_pin
own two-integer gcd. sign_class / magnitude_pin (other body)
own sign of one integer. factorial_class / permute_pin
(other body) own n!. perfect_class / aliquot_pin (other
body) own deficient / perfect / abundant.

This module is the one-integer Möbius witness: zero / plus /
minus from μ(n). Missing value is UNKNOWN (None), not FALSE
and not 0. A measured μ 0 is ZERO, never UNKNOWN.
A measured n 1 is PLUS (μ 1), never UNKNOWN.
n < 1 fails closed — μ is defined on positive ints only.
A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer.

sample is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a
send and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and coprime_class.

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
PLUS = "plus"
MINUS = "minus"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({ZERO, PLUS, MINUS})

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
    """A Möbius classifier never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A Möbius class does not re-arm outbound."""
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
    """Structurally False. A recorded μ is not an external effect."""
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


def missing_mu_is_zero() -> bool:
    """Structurally False. Missing μ is UNKNOWN, not 0."""
    return False


def measured_zero_is_unknown() -> bool:
    """Structurally False. A measured μ 0 is ZERO, never UNKNOWN."""
    return False


def measured_one_is_unknown() -> bool:
    """Structurally False. n 1 is PLUS (μ 1), never UNKNOWN."""
    return False


def zero_is_false() -> bool:
    """Structurally False. ZERO is a family, not FALSE."""
    return False


def minus_is_false() -> bool:
    """Structurally False. MINUS is a family, not FALSE."""
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


def _require_exact_int(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{name} must be an exact int: {value!r}")
    return value


def _mobius(n: int) -> int:
    """μ(n) for n >= 1. Integer trial only. No float, no clock."""
    if n == 1:
        return 1
    remaining = n
    primes = 0
    if remaining % 2 == 0:
        remaining //= 2
        primes += 1
        if remaining % 2 == 0:
            return 0
    factor = 3
    while factor * factor <= remaining:
        if remaining % factor == 0:
            remaining //= factor
            primes += 1
            if remaining % factor == 0:
                return 0
        factor += 2
    if remaining > 1:
        primes += 1
    if primes % 2 == 0:
        return 1
    return -1


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
    """zero / plus / minus, or None when missing or timed out.

    Missing value is UNKNOWN (None), not FALSE and not 0.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Value must be an
    exact int. bool is not an int here.
    n < 1 fails closed — μ is not a family there.
    A measured μ 0 is ZERO, never UNKNOWN.
    n 1 is PLUS, never UNKNOWN.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if value is None:
        return None
    measured = _require_exact_int(value, name="value")
    if measured < 1:
        raise FailClosedError(
            f"n < 1 is not a Möbius family: {measured!r}")
    mu = _mobius(measured)
    if mu == 0:
        return ZERO
    if mu == 1:
        return PLUS
    return MINUS


def mu_of(
    value: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return μ(n) in {-1, 0, 1}, or None when missing or timed out.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails
    closed. ZERO records 0. PLUS records 1. MINUS records -1.
    """
    family = classify_family(value, timeout=timeout)
    if family is None:
        return None
    measured = _require_exact_int(value, name="value")
    return _mobius(measured)


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class MobiusBind:
    """One intent + family + value + μ + slot.

    Frozen so a later write cannot silently retcon the recorded
    μ into send_authorized. mu is 0 for ZERO, 1 for PLUS,
    and -1 for MINUS.
    """

    intent: str
    family: str
    value: int
    mu: int
    slot: str


def bind_mobius(
    intent: object,
    value: object,
    *,
    slot: object,
) -> MobiusBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(value, timeout=False)
    if family is None:
        raise FailClosedError("value missing — UNKNOWN is not a bind")
    measured = _require_exact_int(value, name="value")
    key = _require_slot(slot)
    recorded = _mobius(measured)
    return MobiusBind(
        intent=klass,
        family=family,
        value=measured,
        mu=recorded,
        slot=key,
    )


def try_bind(
    intent: object,
    value: object,
    *,
    slot: object,
) -> Optional[MobiusBind]:
    """Missing intent, value, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or value is None or slot is None:
        return None
    return bind_mobius(intent, value, slot=slot)


def admit_mobius(
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
    ZERO / MINUS are families, not a send, and do not invent
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
    family = classify_family(value, timeout=False)
    if family is None:
        return None
    if klass == SAMPLE:
        return not halted
    return True
