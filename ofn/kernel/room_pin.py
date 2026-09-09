"""Pin a CapacityBind so the recorded remaining room cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(slot → room:used:limit:family).
The same quadruple again is already_pinned. A different
room, used, limit, or family on the same slot fails closed
as room_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from overflow/carry, underflow/borrow, remainder/
leftover, saturation/clamp, token/spend, payload_bound,
token_ceiling, and seq.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .capacity_class import (
    EMPTY,
    FULL,
    HAS_ROOM,
    OVER_CAP,
    RESERVE,
    CapacityBind,
    bind_capacity,
    classify_family,
    classify_intent,
)
from .errors import FailClosedError

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})

_ROOM_UNKNOWN = "unknown"


def grants_send() -> bool:
    """A room pin never authorizes a send. Structurally False."""
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


def room_is_zero() -> bool:
    """Structurally False. Missing remaining room is UNKNOWN, not 0."""
    return False


def pin_allows_send(bind: CapacityBind) -> bool:
    """Structurally False. Even a reserve bind is not send_authorized."""
    if not isinstance(bind, CapacityBind):
        raise FailClosedError(f"bind must be a CapacityBind: {bind!r}")
    return False


def pin_allows_reserve(bind: CapacityBind) -> bool:
    """True only when the pinned intent is reserve and family has room.

    empty and has_room have remaining room. full / over_cap do not.
    This is not a grant of reserving and not send_authorized.
    HALT still stops the factory START.
    """
    if not isinstance(bind, CapacityBind):
        raise FailClosedError(f"bind must be a CapacityBind: {bind!r}")
    return bind.intent == RESERVE and bind.family in {EMPTY, HAS_ROOM}


def _encode(bind: CapacityBind) -> str:
    room_text = _ROOM_UNKNOWN if bind.room is None else str(bind.room)
    return f"{room_text}:{bind.used}:{bind.limit}:{bind.family}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_room(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    if type(pinned) is not str or pinned.count(":") != 3:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    room_text, used_text, limit_text, family = pinned.split(":")
    if family not in {EMPTY, HAS_ROOM, FULL, OVER_CAP}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if room_text != _ROOM_UNKNOWN and not room_text.isdigit():
        raise FailClosedError(f"pinned room drifted: {pinned!r}")
    if family == OVER_CAP and room_text != _ROOM_UNKNOWN:
        raise FailClosedError(
            f"pinned over_cap room must be unknown: {pinned!r}")
    if family != OVER_CAP and room_text == _ROOM_UNKNOWN:
        raise FailClosedError(
            f"pinned {family} room missing: {pinned!r}")
    for part, label in ((used_text, "used"), (limit_text, "limit")):
        if not part.isdigit():
            raise FailClosedError(f"pinned {label} drifted: {pinned!r}")
    return pinned


def pin_room(
    table: MutableMapping[str, str],
    bind: CapacityBind,
) -> str:
    """Record (slot → room:used:limit:family) at most once.

    First pin → pinned. Same quadruple again → already_pinned.
    Different room, used, limit, or family on the same slot
    fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, CapacityBind):
        raise FailClosedError(f"bind must be a CapacityBind: {bind!r}")
    checked = bind_capacity(
        bind.intent,
        bind.used,
        limit=bind.limit,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.room != bind.room
        or checked.used != bind.used
        or checked.limit != bind.limit
    ):
        raise FailClosedError(
            "CapacityBind drifted from re-bind: "
            f"have family={bind.family!r} room={bind.room!r} "
            f"used={bind.used!r} limit={bind.limit!r}")
    existing = peek_room(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"room_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: CapacityBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, CapacityBind):
        raise FailClosedError(f"bind must be a CapacityBind: {bind!r}")
    existing = peek_room(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    used: object,
    *,
    limit: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing used/intent/limit/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or used is None or limit is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(used, limit=limit, timeout=False) is None:
        return None
    return pin_room(
        table,
        bind_capacity(intent, used, limit=limit, slot=slot),
    )
