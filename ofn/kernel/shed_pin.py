"""Pin a BacklogBind so the recorded shed line cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → depth:threshold:family).
The same triple again is already_pinned. A different depth,
threshold, or family on the same slot fails closed as shed_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from capacity/room, overflow/carry, remainder/leftover,
rate/throttle, cascade/stop, token_ceiling, and seq.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .backlog_class import (
    AT,
    BELOW,
    OVER,
    SHED,
    BacklogBind,
    bind_backlog,
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


def grants_send() -> bool:
    """A shed pin never authorizes a send. Structurally False."""
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
    """Structurally False. Missing room is UNKNOWN, not 0."""
    return False


def over_is_negative() -> bool:
    """Structurally False. Over-threshold room is UNKNOWN, not a negative."""
    return False


def pin_allows_send(bind: BacklogBind) -> bool:
    """Structurally False. Even a shed bind is not send_authorized."""
    if not isinstance(bind, BacklogBind):
        raise FailClosedError(f"bind must be a BacklogBind: {bind!r}")
    return False


def pin_allows_shed(bind: BacklogBind) -> bool:
    """True only when the pinned intent is shed and family is at or over.

    This is not a grant of dropping work and not send_authorized.
    HALT still stops the factory START. Below-threshold is
    recorded, not authorized as a shed.
    """
    if not isinstance(bind, BacklogBind):
        raise FailClosedError(f"bind must be a BacklogBind: {bind!r}")
    return bind.intent == SHED and bind.family in {AT, OVER}


def _encode(bind: BacklogBind) -> str:
    return f"{bind.depth}:{bind.threshold}:{bind.family}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_shed(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    if type(pinned) is not str or pinned.count(":") != 2:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    depth_text, threshold_text, family = pinned.split(":")
    if family not in {BELOW, AT, OVER}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not depth_text.isdigit() or not threshold_text.isdigit():
        raise FailClosedError(f"pinned depth/threshold drifted: {pinned!r}")
    return pinned


def pin_shed(
    table: MutableMapping[str, str],
    bind: BacklogBind,
) -> str:
    """Record (slot → depth:threshold:family) at most once per distinct triple.

    First pin → pinned. Same triple again → already_pinned.
    Different depth, threshold, or family on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, BacklogBind):
        raise FailClosedError(f"bind must be a BacklogBind: {bind!r}")
    checked = bind_backlog(
        bind.intent,
        bind.depth,
        threshold=bind.threshold,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.depth != bind.depth
        or checked.threshold != bind.threshold
    ):
        raise FailClosedError(
            "BacklogBind drifted from re-bind: "
            f"have family={bind.family!r} depth={bind.depth!r} "
            f"threshold={bind.threshold!r}")
    existing = peek_shed(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"shed_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: BacklogBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, BacklogBind):
        raise FailClosedError(f"bind must be a BacklogBind: {bind!r}")
    existing = peek_shed(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    depth: object,
    *,
    threshold: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing depth/intent/threshold/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or depth is None or threshold is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(depth, threshold=threshold, timeout=False) is None:
        return None
    return pin_shed(
        table,
        bind_backlog(intent, depth, threshold=threshold, slot=slot),
    )
