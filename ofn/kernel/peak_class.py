"""Classify a three-sample local extremum without granting a send.

rise_class / fall_pin (other body) own two successive signed ints.
wax_class / wane_pin (other body) own two non-negative counts.
above_class / below_pin (other body) own one signed height vs a plane.
hysteresis_class / band_pin own two-threshold latch sides.
even_class / odd_pin (other body) own parity of one signed int.
watermark / high (other body) own a single threshold.

This module is the three-sample extremum witness: PEAK / TROUGH /
NEITHER. Missing earlier, mid, or later is UNKNOWN (None), not
FALSE and not 0. A present-but-wrong type fails closed. Timeout
is UNKNOWN and does not prove a writer.

A PEAK is a strict local max (mid > earlier and mid > later).
A TROUGH is a strict local min (mid < earlier and mid < later).
Everything else, including all-equal coincidence and a monotonic
slope, is NEITHER — never UNKNOWN and never a silent PEAK.

sample is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send and never
promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

PEAK = "PEAK"
TROUGH = "TROUGH"
NEITHER = "NEITHER"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({PEAK, TROUGH, NEITHER})

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
    """A peak classifier never authorizes a send. Structurally False."""
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
    """Structurally False. A recorded extremum is not an external effect."""
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


def missing_is_zero() -> bool:
    """Structurally False. Missing sample is UNKNOWN, not 0."""
    return False


def coincidence_is_peak() -> bool:
    """Structurally False. All-equal is NEITHER, never PEAK."""
    return False


def coincidence_is_trough() -> bool:
    """Structurally False. All-equal is NEITHER, never TROUGH."""
    return False


def two_sample_is_three() -> bool:
    """Structurally False. Two successive ints are a different witness."""
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


def _require_sample(value: object, *, what: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{what} must be an exact int: {value!r}")
    return value


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
    earlier: object,
    mid: object,
    later: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """PEAK / TROUGH / NEITHER, or None when missing or timed out.

    Missing any sample is UNKNOWN (None), not FALSE and not 0.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Each sample must be an
    exact int. bool is not an int here.

    Strict inequalities only. All-equal coincidence is NEITHER.
    A two-sample rise or fall is not a three-sample extremum.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if earlier is None or mid is None or later is None:
        return None
    left = _require_sample(earlier, what="earlier")
    center = _require_sample(mid, what="mid")
    right = _require_sample(later, what="later")
    if center > left and center > right:
        return PEAK
    if center < left and center < right:
        return TROUGH
    return NEITHER


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class PeakBind:
    """One intent + family + earlier + mid + later + slot.

    Frozen so a later write cannot silently retcon the recorded
    extremum into send_authorized.
    """

    intent: str
    family: str
    earlier: int
    mid: int
    later: int
    slot: str


def bind_peak(
    intent: object,
    earlier: object,
    mid: object,
    later: object,
    *,
    slot: object,
) -> PeakBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(earlier, mid, later, timeout=False)
    if family is None:
        raise FailClosedError("sample missing — UNKNOWN is not a bind")
    left = _require_sample(earlier, what="earlier")
    center = _require_sample(mid, what="mid")
    right = _require_sample(later, what="later")
    key = _require_slot(slot)
    return PeakBind(
        intent=klass,
        family=family,
        earlier=left,
        mid=center,
        later=right,
        slot=key,
    )


def try_bind(
    intent: object,
    earlier: object,
    mid: object,
    later: object,
    *,
    slot: object,
) -> Optional[PeakBind]:
    """Missing intent or any sample or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or earlier is None
        or mid is None
        or later is None
        or slot is None
    ):
        return None
    return bind_peak(intent, earlier, mid, later, slot=slot)


def admit_peak(
    intent: object,
    earlier: object,
    mid: object,
    later: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or any sample is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. sample is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    NEITHER is a family, not a send, and does not invent False
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
    family = classify_family(earlier, mid, later, timeout=False)
    if family is None:
        return None
    if klass == SAMPLE:
        return not halted
    return True
