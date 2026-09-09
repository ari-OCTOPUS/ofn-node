"""Pin an OverflowBind so the recorded carry cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(slot → carry:used:add:capacity:family).
The same quintuple again is already_pinned. A different
carry, used, add, capacity, or family on the same slot
fails closed as carry_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from remainder/leftover, byte/length, token/spend,
payload_bound, token_ceiling, and seq.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .overflow_class import (
    CONSUME,
    FITS,
    OVERFLOW,
    OverflowBind,
    bind_overflow,
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
    """A carry pin never authorizes a send. Structurally False."""
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


def carry_is_zero() -> bool:
    """Structurally False. Missing carry is UNKNOWN, not 0."""
    return False


def pin_allows_send(bind: OverflowBind) -> bool:
    """Structurally False. Even a consume bind is not send_authorized."""
    if not isinstance(bind, OverflowBind):
        raise FailClosedError(f"bind must be an OverflowBind: {bind!r}")
    return False


def pin_allows_consume(bind: OverflowBind) -> bool:
    """True only when the pinned intent is consume and family is fits.

    This is not a grant of consuming and not send_authorized.
    HALT still stops the factory START. Overflow family is
    recorded, not authorized as a clean fill.
    """
    if not isinstance(bind, OverflowBind):
        raise FailClosedError(f"bind must be an OverflowBind: {bind!r}")
    return bind.intent == CONSUME and bind.family == FITS


def _encode(bind: OverflowBind) -> str:
    return (
        f"{bind.carry}:{bind.used}:{bind.add}:"
        f"{bind.capacity}:{bind.family}"
    )


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_carry(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    if type(pinned) is not str or pinned.count(":") != 4:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    carry_text, used_text, add_text, cap_text, family = pinned.split(":")
    if family not in {FITS, OVERFLOW}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    for part, label in (
        (carry_text, "carry"),
        (used_text, "used"),
        (add_text, "add"),
        (cap_text, "capacity"),
    ):
        if not part.isdigit():
            raise FailClosedError(
                f"pinned {label} drifted: {pinned!r}")
    return pinned


def pin_carry(
    table: MutableMapping[str, str],
    bind: OverflowBind,
) -> str:
    """Record (slot → carry:used:add:capacity:family) at most once.

    First pin → pinned. Same quintuple again → already_pinned.
    Different carry, used, add, capacity, or family on the same
    slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, OverflowBind):
        raise FailClosedError(f"bind must be an OverflowBind: {bind!r}")
    checked = bind_overflow(
        bind.intent,
        bind.used,
        add=bind.add,
        capacity=bind.capacity,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.carry != bind.carry
        or checked.used != bind.used
        or checked.add != bind.add
        or checked.capacity != bind.capacity
    ):
        raise FailClosedError(
            "OverflowBind drifted from re-bind: "
            f"have family={bind.family!r} carry={bind.carry!r} "
            f"used={bind.used!r} add={bind.add!r} "
            f"capacity={bind.capacity!r}")
    existing = peek_carry(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"carry_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: OverflowBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, OverflowBind):
        raise FailClosedError(f"bind must be an OverflowBind: {bind!r}")
    existing = peek_carry(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    used: object,
    *,
    add: object,
    capacity: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing used/intent/add/capacity/slot or timeout is UNKNOWN (None).

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
        or used is None
        or add is None
        or capacity is None
        or slot is None
    ):
        return None
    # classify_* keep the fail-closed wall before bind.
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(
        used, add=add, capacity=capacity, timeout=False,
    ) is None:
        return None
    return pin_carry(
        table,
        bind_overflow(
            intent, used, add=add, capacity=capacity, slot=slot),
    )
