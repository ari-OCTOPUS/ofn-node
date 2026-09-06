"""Classify a value against a two-threshold hysteresis band.

A rise crosses high from a non-HIGH prior. A fall crosses low
from a non-LOW prior. A hold stays on the latched side.
Missing value, low, high, or prior is UNKNOWN (None), not
FALSE and not 0.

low == high fails closed — a point is not a band.
low > high fails closed — inverted bounds are not a band.
Bool/float/str values fail closed. Sealed send/ready names
are not a band, a value, or a prior.

This module never grants a send and never re-arms after a
hold. campaign_envelope_ready stays distinct from
send_authorized.

Distinct from later_hold (epoch compare), scoped_authz
(newer scoped record), deadline_window, token_ceiling,
saturation-clamp (clip), and watermark-high (single
threshold). Not wired into run_store.py. HALT stops
STARTS, not this classify.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

BELOW = "BELOW"
INSIDE = "INSIDE"
ABOVE = "ABOVE"
HIGH = "HIGH"
LOW = "LOW"
RISE = "RISE"
FALL = "FALL"
HOLD = "HOLD"
UNKNOWN = "UNKNOWN"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})
_PRIORS = frozenset({HIGH, LOW, INSIDE})
_BANDS = frozenset({BELOW, INSIDE, ABOVE})


def grants_send() -> bool:
    """A hysteresis classify never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A band class does not re-arm outbound."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A band class is not a rename of authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classify is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A band class is not an external effect."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This module is not imported by the store."""
    return False


def later_hold_supersedes_older() -> bool:
    """Structurally True. A later hold still beats an older claim."""
    return True


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return UNKNOWN


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed_name(value: object, *, what: str) -> None:
    if type(value) is not str:
        return
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {s.replace("-", "_") for s in _SEALED}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "a band is not a send")


def require_int(value: object, name: str) -> int:
    """Exact int, not bool/float/str. ``int(True)`` is not a band."""
    _refuse_sealed_name(value, what=name)
    if type(value) is not int:
        raise FailClosedError(f"{name} must be int: {value!r}")
    return value


def _int_or_unknown(value: object, *, what: str) -> Optional[int]:
    if value is None:
        return None
    return require_int(value, what)


def _require_band(low: object, high: object) -> Optional[tuple[int, int]]:
    lo = _int_or_unknown(low, what="low")
    hi = _int_or_unknown(high, what="high")
    if lo is None or hi is None:
        return None
    if lo == hi:
        raise FailClosedError(
            "low equals high — a point is not a hysteresis band")
    if lo > hi:
        raise FailClosedError(
            "low greater than high — inverted bounds are not a band")
    return lo, hi


def classify_band(value: object, low: object, high: object) -> str:
    """BELOW / INSIDE / ABOVE, or UNKNOWN.

    Missing any side is UNKNOWN, not FALSE. Equal or inverted
    bounds fail closed. Present-but-bad still fails closed.
    This is position, not the latched hysteresis side.
    """
    band = _require_band(low, high)
    measured = _int_or_unknown(value, what="value")
    if band is None or measured is None:
        return UNKNOWN
    lo, hi = band
    if measured < lo:
        return BELOW
    if measured > hi:
        return ABOVE
    return INSIDE


def classify_prior(value: object) -> str:
    """HIGH / LOW / INSIDE, or UNKNOWN.

    None → UNKNOWN (no witness). Empty / unknown / sealed
    names fail closed. UNKNOWN is not FALSE.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"prior must be a str or None: {value!r}")
    _refuse_sealed_name(value, what="prior")
    text = value.strip()
    if not text:
        raise FailClosedError("prior is empty")
    folded = text.upper()
    if folded in _PRIORS:
        return folded
    raise FailClosedError(
        f"unknown prior is not a refusal and not a grant: {value!r}")


def latch_band(
    prior: object, value: object, low: object, high: object,
) -> Optional[str]:
    """HIGH / LOW / INSIDE, or None when any side is missing.

    HIGH holds while value > low and falls at value <= low.
    LOW holds while value < high and rises at value >= high.
    INSIDE rises at value >= high and falls at value <= low.
    None is UNKNOWN, not FALSE and not a default side.
    """
    band = _require_band(low, high)
    measured = _int_or_unknown(value, what="value")
    prior_klass = classify_prior(prior)
    if band is None or measured is None or prior_klass == UNKNOWN:
        return None
    lo, hi = band
    if prior_klass == HIGH:
        return LOW if measured <= lo else HIGH
    if prior_klass == LOW:
        return HIGH if measured >= hi else LOW
    if measured >= hi:
        return HIGH
    if measured <= lo:
        return LOW
    return INSIDE


def classify_edge(
    prior: object, value: object, low: object, high: object,
) -> str:
    """RISE / FALL / HOLD, or UNKNOWN.

    Missing any side is UNKNOWN, not FALSE. A measured
    disagreement of sides is RISE or FALL. Same latched
    side is HOLD. Present-but-bad still fails closed.
    """
    prior_klass = classify_prior(prior)
    latched = latch_band(prior, value, low, high)
    if prior_klass == UNKNOWN or latched is None:
        return UNKNOWN
    if prior_klass == HIGH and latched == LOW:
        return FALL
    if prior_klass == LOW and latched == HIGH:
        return RISE
    if prior_klass == INSIDE and latched == HIGH:
        return RISE
    if prior_klass == INSIDE and latched == LOW:
        return FALL
    return HOLD


def admit_send_after_edge(
    prior: object, value: object, low: object, high: object,
) -> Optional[bool]:
    """True is unreachable. RISE/FALL/HOLD is False. Missing is None."""
    klass = classify_edge(prior, value, low, high)
    if klass == UNKNOWN:
        return None
    return False


@dataclass(frozen=True)
class HysteresisClass:
    """One prior + value + band class. Frozen so a later write
    cannot silently retcon RISE into a send grant.
    """

    prior: str
    value: int
    low: int
    high: int
    edge_class: str
    latched: str


def pin_edge(
    prior: object, value: object, low: object, high: object,
) -> HysteresisClass:
    """Require RISE or FALL. Missing fails closed (use try_pin)."""
    klass = classify_edge(prior, value, low, high)
    if klass == UNKNOWN:
        raise FailClosedError(
            "edge missing — UNKNOWN is not a hysteresis pin")
    if klass == HOLD:
        raise FailClosedError(
            "edge is HOLD, not RISE/FALL — a hold does not pin an edge")
    latched = latch_band(prior, value, low, high)
    if latched is None:
        raise FailClosedError("latch missing — UNKNOWN is not a pin")
    return HysteresisClass(
        prior=classify_prior(prior),
        value=require_int(value, "value"),
        low=require_int(low, "low"),
        high=require_int(high, "high"),
        edge_class=klass,
        latched=latched,
    )


def try_pin(
    prior: object, value: object, low: object, high: object,
) -> Optional[HysteresisClass]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    if prior is None or value is None or low is None or high is None:
        return None
    return pin_edge(prior, value, low, high)
