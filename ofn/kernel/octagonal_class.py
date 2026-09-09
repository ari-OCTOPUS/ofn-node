"""Classify one exact integer as an octagonal figure without granting a send.

heptagonal_class / gonal_pin (other body / #253) own He_n = n(5n-3)/2.
pentagonal_class / figure_pin (other body / #252) own P_n = n(3n-1)/2.
hexagonal_class / lattice_pin (unpublished / other body) own H_n = n(2n-1).
triangular_class / series_pin (unpublished / other body) own T_n = n(n+1)/2.
square_class / root_pin (#235) own perfect squares.
cube_class / cubic_pin (#243) own perfect cubes.
pell_class / silver_pin (#250) own the Pell walk.
catalan_class / nest_pin (#249) own C_n.
fibonacci_class / sequence_pin (unpublished / other body) own F_n.
padovan_class / plastic_pin (unpublished / other body) own the Padovan walk.

This module is the eight-gonal witness: ZERO / OCTAGONAL / OTHER
from one non-negative exact int as O_n = n(3n-2).
Walk identity 3·O + 1 = (3n-1)^2 fail-closes when it
disagrees with the closed form. Missing the value is UNKNOWN
(None), not FALSE and not 0. A present-but-wrong type fails
closed. Timeout is UNKNOWN and does not prove a writer.

sample is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a
send and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and remainder_class.

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
OCTAGONAL = "octagonal"
OTHER = "other"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({ZERO, OCTAGONAL, OTHER})

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
    """An octagonal classifier never authorizes a send. Structurally False."""
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
    """Structurally False. A recorded figure is not an external effect."""
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


def missing_value_is_zero() -> bool:
    """Structurally False. Missing value is UNKNOWN, not 0."""
    return False


def measured_zero_is_octagonal() -> bool:
    """Structurally False. Measured 0 is ZERO, never OCTAGONAL."""
    return False


def measured_one_is_unknown() -> bool:
    """Structurally False. Measured 1 is OCTAGONAL index 1, never UNKNOWN."""
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


def _require_value(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{name} must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(
            f"{name} must be non-negative: {value!r} — n<0 is not a family")
    return value


def _isqrt(n: int) -> Optional[int]:
    """Integer square root or None when n is not a perfect square."""
    if n < 0:
        return None
    lo, hi = 0, n
    found: Optional[int] = None
    while lo <= hi:
        mid = (lo + hi) // 2
        sq = mid * mid
        if sq == n:
            found = mid
            break
        if sq < n:
            lo = mid + 1
        else:
            hi = mid - 1
    return found


def _closed_form(index: int) -> int:
    return index * (3 * index - 2)


def _walk_index(value: int) -> Optional[int]:
    """Return n>=0 such that O_n = value, or None.

    Closed form and walk identity must agree. Disagreement
    fail-closes — a drifted figure is not OTHER and not UNKNOWN.
    """
    if value == 0:
        if _closed_form(0) != 0:
            raise FailClosedError("walk identity drifted at zero")
        if 3 * value + 1 != (3 * 0 - 1) ** 2:
            raise FailClosedError("walk identity drifted at zero")
        return 0
    disc = 3 * value + 1
    root = _isqrt(disc)
    if root is None:
        return None
    if (root + 1) % 3 != 0:
        return None
    index = (root + 1) // 3
    if index < 1:
        return None
    computed = _closed_form(index)
    if computed != value:
        raise FailClosedError(
            "walk identity drifted: closed form "
            f"{computed!r} != value {value!r}")
    if 3 * value + 1 != (3 * index - 1) ** 2:
        raise FailClosedError(
            "walk identity drifted: 3O+1 != (3n-1)^2")
    return index


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
    """zero / octagonal / other, or None when missing or timed out.

    Missing value is UNKNOWN (None), not FALSE and not 0.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Value must be an exact
    non-negative int. bool is not an int here. Measured 0 is
    ZERO, never OCTAGONAL. Measured 1 is OCTAGONAL index 1,
    never UNKNOWN.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if value is None:
        return None
    n = _require_value(value, name="value")
    index = _walk_index(n)
    if index is None:
        return OTHER
    if index == 0:
        return ZERO
    return OCTAGONAL


def index_of(
    value: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return n where O_n = value, or None when missing, other, or timed out.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails closed.
    OTHER has no index (None), not 0. ZERO has index 0 — that 0 is
    measured, not missing.
    """
    family = classify_family(value, timeout=timeout)
    if family is None:
        return None
    if family == OTHER:
        return None
    n = _require_value(value, name="value")
    return _walk_index(n)


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class OctagonalBind:
    """One intent + family + value + index + slot.

    Frozen so a later write cannot silently retcon the recorded
    figure into send_authorized. index is 0 for ZERO, n>=1 for
    OCTAGONAL, and None for OTHER.
    """

    intent: str
    family: str
    value: int
    index: Optional[int]
    slot: str


def bind_octagonal(
    intent: object,
    value: object,
    *,
    slot: object,
) -> OctagonalBind:
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
    n = _require_value(value, name="value")
    key = _require_slot(slot)
    idx = _walk_index(n)
    if family == OTHER:
        idx = None
    return OctagonalBind(
        intent=klass,
        family=family,
        value=n,
        index=idx,
        slot=key,
    )


def try_bind(
    intent: object,
    value: object,
    *,
    slot: object,
) -> Optional[OctagonalBind]:
    """Missing intent, value, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or value is None or slot is None:
        return None
    return bind_octagonal(intent, value, slot=slot)


def admit_octagonal(
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
