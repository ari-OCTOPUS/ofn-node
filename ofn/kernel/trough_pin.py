"""Pin a PeakBind so the recorded extremum cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → family:earlier:mid:later).
The same quadruple again is already_pinned. A different family
or sample on the same slot fails closed as trough_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

pin_allows_sample is True only for sample+TROUGH. A PEAK
or NEITHER bind is recorded, not a trough grant. This is
not send_authorized.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from rise/fall (two samples), wax/wane (counts),
above/below (one plane), hysteresis/band, even/odd, and
watermark/high.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .peak_class import (
    FAMILIES,
    NEITHER,
    PEAK,
    SAMPLE,
    TROUGH,
    PeakBind,
    bind_peak,
    classify_family,
    classify_intent,
)

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A trough pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
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


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def consumes_nonce() -> bool:
    """Structurally False. This pin is not nonce once-consume."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def missing_is_zero() -> bool:
    """Structurally False. Missing pin is UNKNOWN, not 0."""
    return False


def pin_allows_send(bind: PeakBind) -> bool:
    """Structurally False. Even a sample bind is not send_authorized."""
    if not isinstance(bind, PeakBind):
        raise FailClosedError(f"bind must be a PeakBind: {bind!r}")
    return False


def pin_allows_sample(bind: PeakBind) -> bool:
    """True only when the pinned intent is sample and family is TROUGH.

    This is not a grant of sampling and not send_authorized.
    HALT still stops the factory START. PEAK and NEITHER are
    recorded, not authorized as a trough.
    """
    if not isinstance(bind, PeakBind):
        raise FailClosedError(f"bind must be a PeakBind: {bind!r}")
    return bind.intent == SAMPLE and bind.family == TROUGH


def _encode(bind: PeakBind) -> str:
    return f"{bind.family}:{bind.earlier}:{bind.mid}:{bind.later}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def _parse_int_token(token: str, *, what: str) -> None:
    if not token or token == "-" or token == "+":
        raise FailClosedError(f"pinned {what} drifted: {token!r}")
    if token[0] in "+-":
        body = token[1:]
    else:
        body = token
    if not body.isdigit():
        raise FailClosedError(f"pinned {what} drifted: {token!r}")


def peek_trough(table: Mapping[str, str], slot: object) -> Optional[str]:
    """Return the pinned encoding or None.

    None is UNKNOWN, not FALSE. Never writes. Missing table key
    is UNKNOWN. A sealed slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if type(slot) is not str:
        if slot is None:
            return None
        raise FailClosedError(f"slot must be a str or None: {slot!r}")
    if not slot.strip():
        raise FailClosedError("slot is empty")
    _refuse_sealed_slot(slot)
    text = slot.strip()
    if text not in table:
        return None
    pinned = table[text]
    if type(pinned) is not str:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    parts = pinned.split(":")
    if len(parts) != 4:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    family, earlier_text, mid_text, later_text = parts
    if family not in FAMILIES:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    _parse_int_token(earlier_text, what="earlier")
    _parse_int_token(mid_text, what="mid")
    _parse_int_token(later_text, what="later")
    return pinned


def pin_trough(
    table: MutableMapping[str, str],
    bind: PeakBind,
) -> str:
    """Record (slot → family:earlier:mid:later) at most once per distinct quadruple.

    First pin → pinned. Same quadruple again → already_pinned.
    Different family or sample on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, PeakBind):
        raise FailClosedError(f"bind must be a PeakBind: {bind!r}")
    checked = bind_peak(
        bind.intent,
        bind.earlier,
        bind.mid,
        bind.later,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.earlier != bind.earlier
        or checked.mid != bind.mid
        or checked.later != bind.later
    ):
        raise FailClosedError(
            "PeakBind drifted from re-bind: "
            f"have family={bind.family!r} earlier={bind.earlier!r} "
            f"mid={bind.mid!r} later={bind.later!r}")
    existing = peek_trough(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"trough_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: PeakBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, PeakBind):
        raise FailClosedError(f"bind must be a PeakBind: {bind!r}")
    existing = peek_trough(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    earlier: object,
    mid: object,
    later: object,
    *,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing sample/intent/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if (
        intent is None
        or earlier is None
        or mid is None
        or later is None
        or slot is None
    ):
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(earlier, mid, later, timeout=False) is None:
        return None
    return pin_trough(
        table, bind_peak(intent, earlier, mid, later, slot=slot))


# Re-export family names so tests can pin without a second import path.
__all__ = (
    "ALREADY_PINNED",
    "NEITHER",
    "PEAK",
    "PINNED",
    "TROUGH",
    "claims_immutable",
    "consumes_nonce",
    "grants_send",
    "halt_blocks_pin",
    "later_disarm_supersedes",
    "missing_is_zero",
    "peek_trough",
    "pin_allows_sample",
    "pin_allows_send",
    "pin_trough",
    "promotes_ready_to_send",
    "proposal_is_execution",
    "ready_is_authorized",
    "retcon_refused",
    "timeout_proves_concurrent_write",
    "try_pin",
    "unknown_is_false",
    "wires_into_run_store",
)
