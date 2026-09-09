"""Classify one non-negative integer as a dodecagonal number.

hendecagonal_class / undecagon_pin (other body) own Hd_n = n(9n-7)/2.
decagonal_class / decagon_pin (other body) own De_n = n(4n-3).
nonagonal_class / nonagon_pin (other body) own No_n = n(7n-5)/2.
octagonal_class / vertex_pin (other body) own O_n = n(3n-2).
heptagonal_class / gonal_pin (other body) own He_n = n(5n-3)/2.
pentagonal_class / figure_pin (other body) own P_n = n(3n-1)/2.
hexagonal_class / lattice_pin (other body) own H_n = n(2n-1).
triangular_class / series_pin (other body) own T_n = n(n+1)/2.
tetrahedral_class / pyramid_pin (other body) own Te_n = n(n+1)(n+2)/6.
square_class / root_pin own exact squares. 64 is both a square
and Do_4 — this module records DODECAGONAL, not OTHER.

This module is the 12-gonal witness: ZERO / DODECAGONAL / OTHER
for Do_n = n(5n-4). Missing the value is UNKNOWN (None),
not FALSE and not 0. A present-but-wrong type fails closed.
Timeout is UNKNOWN and does not prove a writer. n<0 fails
closed. Measured 0 is ZERO, never DODECAGONAL. Measured 1 is
DODECAGONAL index 1, never UNKNOWN.

Walk identity Do = n(5n-4) and 5Do+4 = (5n-2)^2
fail-close when they disagree with the recovered index.

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
DODECAGONAL = "dodecagonal"
OTHER = "other"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({ZERO, DODECAGONAL, OTHER})

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
    """A dodecagonal classifier never authorizes a send. Structurally False."""
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
    """Structurally False. A recorded value is not an external effect."""
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


def measured_zero_is_dodecagonal() -> bool:
    """Structurally False. Measured 0 is ZERO, never DODECAGONAL."""
    return False


def measured_one_is_unknown() -> bool:
    """Structurally False. Measured 1 is DODECAGONAL index 1, never UNKNOWN."""
    return False


def square_is_other_here() -> bool:
    """Structurally False. A square that is also Do_n is DODECAGONAL.

    64 is Do_4. This module does not reclassify it as OTHER just
    because another witness owns exact squares.
    """
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
        raise FailClosedError(f"{name} must be >= 0: {value!r}")
    return value


def _isqrt(n: int) -> int:
    if n < 2:
        return n
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def _value_at(index: int) -> int:
    return index * (5 * index - 4)


def _index_for(value: int) -> Optional[int]:
    """Return n such that n(5n-4) == value, or None.

    Inverse of 5n^2 - 4n - v = 0:
    n = (4 ± sqrt(16 + 20v)) / 10.
    Walk identities must hold or the pair fails closed.
    """
    disc = 16 + 20 * value
    side = _isqrt(disc)
    if side * side != disc:
        return None
    found: Optional[int] = None
    for numer in (4 + side, 4 - side):
        if numer % 10 != 0:
            continue
        index = numer // 10
        if index < 0:
            continue
        if _value_at(index) != value:
            raise FailClosedError(
                f"dodeca walk drifted: value={value!r} index={index!r}")
        if index * (5 * index - 4) != value:
            raise FailClosedError(
                f"dodeca Do identity drifted: value={value!r} "
                f"index={index!r}")
        expected = (5 * index - 2) * (5 * index - 2)
        if 5 * value + 4 != expected:
            raise FailClosedError(
                f"dodeca square identity drifted: value={value!r} "
                f"index={index!r}")
        if found is not None and found != index:
            raise FailClosedError(
                f"dodeca index collision: {found!r} vs {index!r}")
        found = index
    return found


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
    """zero / dodecagonal / other, or None when missing or timed out.

    Missing value is UNKNOWN (None), not FALSE and not 0.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Value must be an exact
    int >= 0. bool is not an int here. Measured 0 is ZERO,
    never DODECAGONAL. Measured 1 is DODECAGONAL, never UNKNOWN.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if value is None:
        return None
    number = _require_nonneg(value, name="value")
    if number == 0:
        return ZERO
    index = _index_for(number)
    if index is None:
        return OTHER
    if index == 0:
        raise FailClosedError(
            "index 0 recovered for a non-zero value — not a family")
    return DODECAGONAL


def index_of(
    value: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return n for Do_n, or None when missing, timed out, or OTHER.

    None is UNKNOWN, not 0 and not FALSE. Measured 0 returns 0
    (ZERO family). OTHER has no index (None), not 0.
    """
    family = classify_family(value, timeout=timeout)
    if family is None:
        return None
    number = _require_nonneg(value, name="value")
    if family == ZERO:
        return 0
    if family == OTHER:
        return None
    index = _index_for(number)
    if index is None:
        raise FailClosedError(
            f"dodeca family without index: {number!r}")
    return index


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class DodecaBind:
    """One intent + family + value + index + slot.

    Frozen so a later write cannot silently retcon the recorded
    figure into send_authorized. index is None only for OTHER.
    """

    intent: str
    family: str
    value: int
    index: Optional[int]
    slot: str


def bind_dodeca(
    intent: object,
    value: object,
    *,
    slot: object,
) -> DodecaBind:
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
    number = _require_nonneg(value, name="value")
    key = _require_slot(slot)
    index = index_of(number)
    return DodecaBind(
        intent=klass,
        family=family,
        value=number,
        index=index,
        slot=key,
    )


def try_bind(
    intent: object,
    value: object,
    *,
    slot: object,
) -> Optional[DodecaBind]:
    """Missing intent, value, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or value is None or slot is None:
        return None
    return bind_dodeca(intent, value, slot=slot)


def admit_dodeca(
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
