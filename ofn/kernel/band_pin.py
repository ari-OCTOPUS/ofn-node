"""Pin a latched hysteresis band so the side cannot be retconned.

The caller owns the table. This module does no I/O and does
not latch from a missing prior. First pin records
(run_id → HIGH/LOW/INSIDE). The same pair again is
already_pinned. A different band on the same run_id fails
closed as band_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized.

Not wired into run_store.py. HALT stops STARTS, not a pin.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .envelope import RUN_ID_RE, is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .hysteresis_class import (
    HIGH,
    HOLD,
    INSIDE,
    LOW,
    HysteresisClass,
    classify_prior,
    latch_band,
    pin_edge,
)

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})
_LATCHED = frozenset({HIGH, LOW, INSIDE})


def grants_send() -> bool:
    """A band pin never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A pin does not re-arm outbound."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A pin is not an external effect."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def later_hold_supersedes_older() -> bool:
    """Structurally True. A later hold still beats an older claim."""
    return True


def pin_allows_send(latched: object) -> bool:
    """Structurally False. Even HIGH is not send_authorized."""
    if latched is None:
        return False
    if type(latched) is not str:
        raise FailClosedError(f"latched must be a str or None: {latched!r}")
    folded = latched.strip().upper()
    if folded in _LATCHED or folded == HOLD:
        return False
    _refuse_sealed(latched, what="latched")
    raise FailClosedError(f"unknown latched band: {latched!r}")


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed(value: object, *, what: str) -> None:
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
            "ready is not a band")


def _require_run_id(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"run_id must be a str: {value!r}")
    _refuse_sealed(value, what="run_id")
    text = value.strip()
    if not text:
        raise FailClosedError("run_id is empty")
    if RUN_ID_RE.match(text) is None:
        raise FailClosedError(f"run_id is malformed: {value!r}")
    return text


def peek_pin(table: Mapping[str, str], run_id: object) -> Optional[str]:
    """Return the pinned latched band or None.

    None is UNKNOWN, not FALSE. Never writes. Missing table key
    is UNKNOWN. A sealed run_id fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if type(run_id) is not str:
        if run_id is None:
            return None
        raise FailClosedError(f"run_id must be a str or None: {run_id!r}")
    if not run_id.strip():
        raise FailClosedError("run_id is empty")
    _refuse_sealed(run_id, what="run_id")
    text = run_id.strip()
    if text not in table:
        return None
    pinned = table[text]
    klass = classify_prior(pinned)
    if klass == "UNKNOWN":
        raise FailClosedError(
            f"pinned band drifted to UNKNOWN: {pinned!r}")
    return klass


def pin_band(
    table: MutableMapping[str, str],
    run_id: object,
    latched: object,
) -> str:
    """Record (run_id → latched) at most once per distinct band.

    First pin → pinned. Same pair again → already_pinned.
    Different band on the same run_id fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    rid = _require_run_id(run_id)
    klass = classify_prior(latched)
    if klass == "UNKNOWN":
        raise FailClosedError("latched missing — UNKNOWN is not a pin")
    existing = peek_pin(table, rid)
    if existing is None:
        table[rid] = klass
        return PINNED
    if existing == klass:
        return ALREADY_PINNED
    raise FailClosedError(
        f"band_collision: run_id {rid!r} pinned "
        f"{existing!r}, refused {klass!r}")


def pin_from_edge(
    table: MutableMapping[str, str],
    run_id: object,
    edge: HysteresisClass,
) -> str:
    """Pin the latched side of a classified RISE/FALL edge."""
    if not isinstance(edge, HysteresisClass):
        raise FailClosedError(f"edge must be a HysteresisClass: {edge!r}")
    checked = pin_edge(edge.prior, edge.value, edge.low, edge.high)
    return pin_band(table, run_id, checked.latched)


def try_latch(
    prior: object, value: object, low: object, high: object,
) -> Optional[str]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    if prior is None or value is None or low is None or high is None:
        return None
    latched = latch_band(prior, value, low, high)
    if latched is None:
        return None
    return latched


def retcon_refused(
    table: Mapping[str, str],
    run_id: object,
    latched: object,
) -> Optional[bool]:
    """True when latched disagrees with a pinned band.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    existing = peek_pin(table, run_id)
    if existing is None:
        return None
    klass = classify_prior(latched)
    if klass == "UNKNOWN":
        return None
    return existing != klass
