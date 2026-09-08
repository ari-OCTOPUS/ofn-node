"""Classify a bag of positive ints by integer harmonic mean.

mean_class / average_pin (other body) own arithmetic exact /
mixed from a sum. geometric_class / product_pin (other body)
own geometric exact / mixed from a product power. ratio_class
/ share_pin (other body) own proper / equal / improper of one
non-neg vs one positive. floor_class / ceil_pin (other body)
own floor / ceil of one signed int + unit. remainder_class /
leftover_pin own leftover after division. square_class /
root_pin own exact squares. lcm_class / least_pin own lcm
families. coprime_class / common_pin own two-integer gcd.

This module is the bag harmonic-mean witness: exact / mixed.
The integer harmonic mean of positives a1..an exists iff
n * P is divisible by Σ(P/ai), where P is the product.
Missing the bag is UNKNOWN (None), not FALSE and not 1.
A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer. Empty bag fails closed —
there is no family, and UNKNOWN is not 1. Zero or negative
fails closed — reciprocal of 0 is not a family.

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
from typing import Optional, Sequence, Tuple

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

EXACT = "exact"
MIXED = "mixed"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EXACT, MIXED})

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
    """A harmonic classifier never authorizes a send. Structurally False."""
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
    """Structurally False. A recorded bag is not an external effect."""
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


def missing_harmonic_is_one() -> bool:
    """Structurally False. Missing harmonic is UNKNOWN, not 1."""
    return False


def mixed_mean_is_zero() -> bool:
    """Structurally False. MIXED mean is UNKNOWN, not 0."""
    return False


def measured_one_is_unknown() -> bool:
    """Structurally False. Harmonic 1 is EXACT, never UNKNOWN."""
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


def _require_positive(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{name} must be an exact int: {value!r}")
    if value <= 0:
        raise FailClosedError(
            f"{name} must be a positive exact int: {value!r} — "
            "reciprocal of 0 is not a family")
    return value


def _as_sequence(values: object) -> Sequence[object]:
    if type(values) is str or type(values) is bytes:
        raise FailClosedError(
            f"values must be a list or tuple of exact ints: {values!r}")
    if type(values) is not list and type(values) is not tuple:
        raise FailClosedError(
            f"values must be a list or tuple of exact ints: {values!r}")
    return values


def _integer_harmonic(parts: Tuple[int, ...]) -> Optional[int]:
    """Integer harmonic mean, or None when MIXED.

    None here is MIXED (no integer mean), not missing. Callers
    must not treat it as 0 or 1.
    """
    n = len(parts)
    product = 1
    for part in parts:
        product *= part
    denom = 0
    for part in parts:
        denom += product // part
    if denom == 0:
        raise FailClosedError(
            "reciprocal sum vanished — not a family")
    numer = n * product
    if numer % denom != 0:
        return None
    return numer // denom


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
    values: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """exact / mixed, or None when missing or timed out.

    Missing bag is UNKNOWN (None), not FALSE and not 1.
    A None member inside an otherwise-shaped bag is UNKNOWN.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Members must be exact
    positive ints. bool is not an int here. Empty bag fails
    closed — UNKNOWN is not 1. Zero or negative fails closed.
    Harmonic 1 (all ones) is EXACT, never UNKNOWN.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if values is None:
        return None
    seq = _as_sequence(values)
    if len(seq) == 0:
        raise FailClosedError(
            "empty bag is not a family — UNKNOWN is not 1")
    missing = False
    for index, item in enumerate(seq):
        if item is None:
            missing = True
            continue
        _require_positive(item, name=f"values[{index}]")
    if missing:
        return None
    parts = tuple(_require_positive(item, name=f"values[{i}]")
                  for i, item in enumerate(seq))
    mean = _integer_harmonic(parts)
    if mean is None:
        return MIXED
    return EXACT


def harmonic_of(
    values: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return the integer harmonic mean, or None.

    None is UNKNOWN, not 0 and not 1 and not FALSE. MIXED (no
    integer mean) is also None — MIXED mean is UNKNOWN, not 0.
    Present-but-bad fails closed.
    """
    family = classify_family(values, timeout=timeout)
    if family is None:
        return None
    if family == MIXED:
        return None
    seq = _as_sequence(values)
    parts = tuple(_require_positive(item, name=f"values[{i}]")
                  for i, item in enumerate(seq))
    mean = _integer_harmonic(parts)
    if mean is None:
        raise FailClosedError(
            "exact family drifted from harmonic recompute")
    return mean


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class HarmonicBind:
    """One intent + family + harmonic + presented bag + slot.

    Frozen so a later write cannot silently retcon the recorded
    bag into send_authorized. values keep presented order.
    harmonic is the integer mean for EXACT, None for MIXED.
    """

    intent: str
    family: str
    harmonic: Optional[int]
    values: Tuple[int, ...]
    slot: str


def bind_harmonic(
    intent: object,
    values: object,
    *,
    slot: object,
) -> HarmonicBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(values, timeout=False)
    if family is None:
        raise FailClosedError("values missing — UNKNOWN is not a bind")
    seq = _as_sequence(values)
    parts = tuple(_require_positive(item, name=f"values[{i}]")
                  for i, item in enumerate(seq))
    key = _require_slot(slot)
    mean = harmonic_of(parts, timeout=False)
    if family == EXACT and mean is None:
        raise FailClosedError("exact family missing integer mean")
    if family == MIXED and mean is not None:
        raise FailClosedError("mixed family carried an integer mean")
    return HarmonicBind(
        intent=klass,
        family=family,
        harmonic=mean,
        values=parts,
        slot=key,
    )


def try_bind(
    intent: object,
    values: object,
    *,
    slot: object,
) -> Optional[HarmonicBind]:
    """Missing intent, values, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or values is None or slot is None:
        return None
    if classify_family(values, timeout=False) is None:
        return None
    return bind_harmonic(intent, values, slot=slot)


def admit_harmonic(
    intent: object,
    values: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or values is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. sample is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    Mixed mean is a family, not a send, and does not invent
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
    family = classify_family(values, timeout=False)
    if family is None:
        return None
    if klass == SAMPLE:
        return not halted
    return True
