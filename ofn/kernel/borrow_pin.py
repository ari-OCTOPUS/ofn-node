"""Pin an UnderflowBind so the recorded borrow cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(slot → family:minuend:subtrahend:floor:wrap). The same
encoding again is already_pinned. A different family, operand,
floor, or wrap flag on the same slot fails closed as
borrow_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from overflow/carry (other body), remainder/leftover
(other body), byte/length, token_ceiling, seq, and
unpublished payload_bound.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .underflow_class import (
    EXACT,
    MEASURE,
    UNDERFLOW,
    WRAP,
    UnderflowBind,
    bind_sub,
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
    """A borrow pin never authorizes a send. Structurally False."""
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


def pin_allows_send(bind: UnderflowBind) -> bool:
    """Structurally False. Even a measure bind is not send_authorized."""
    if not isinstance(bind, UnderflowBind):
        raise FailClosedError(f"bind must be an UnderflowBind: {bind!r}")
    return False


def pin_allows_borrow(bind: UnderflowBind) -> bool:
    """True only when the pinned family is underflow.

    This is not a grant of spending and not send_authorized.
    HALT still stops the factory START. wrap and exact are
    recorded, not a borrow bit.
    """
    if not isinstance(bind, UnderflowBind):
        raise FailClosedError(f"bind must be an UnderflowBind: {bind!r}")
    return bind.family == UNDERFLOW


def pin_allows_measure(bind: UnderflowBind) -> bool:
    """True only when the pinned intent is measure and family is exact.

    This is not a grant of measuring and not send_authorized.
    HALT still stops the factory START. underflow / wrap are
    recorded, not authorized.
    """
    if not isinstance(bind, UnderflowBind):
        raise FailClosedError(f"bind must be an UnderflowBind: {bind!r}")
    return bind.intent == MEASURE and bind.family == EXACT


def _encode(bind: UnderflowBind) -> str:
    wrap_bit = "1" if bind.wrap_requested else "0"
    return (
        f"{bind.family}:{bind.minuend}:{bind.subtrahend}:"
        f"{bind.floor}:{wrap_bit}"
    )


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_borrow(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    family, minuend_text, sub_text, floor_text, wrap_text = pinned.split(":")
    if family not in {EXACT, UNDERFLOW, WRAP}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if (
        not minuend_text.isdigit()
        or not sub_text.isdigit()
        or not floor_text.isdigit()
        or wrap_text not in {"0", "1"}
    ):
        raise FailClosedError(f"pinned operands drifted: {pinned!r}")
    return pinned


def pin_borrow(
    table: MutableMapping[str, str],
    bind: UnderflowBind,
) -> str:
    """Record the encoding at most once per distinct tuple.

    First pin → pinned. Same encoding again → already_pinned.
    Different family / operands / floor / wrap on the same
    slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, UnderflowBind):
        raise FailClosedError(f"bind must be an UnderflowBind: {bind!r}")
    checked = bind_sub(
        bind.intent,
        bind.minuend,
        bind.subtrahend,
        floor=bind.floor,
        slot=bind.slot,
        wrap_requested=bind.wrap_requested,
    )
    if (
        checked.family != bind.family
        or checked.minuend != bind.minuend
        or checked.subtrahend != bind.subtrahend
        or checked.floor != bind.floor
        or checked.wrap_requested != bind.wrap_requested
    ):
        raise FailClosedError(
            "UnderflowBind drifted from re-bind: "
            f"have family={bind.family!r} minuend={bind.minuend!r} "
            f"subtrahend={bind.subtrahend!r} floor={bind.floor!r} "
            f"wrap_requested={bind.wrap_requested!r}")
    existing = peek_borrow(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"borrow_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: UnderflowBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, UnderflowBind):
        raise FailClosedError(f"bind must be an UnderflowBind: {bind!r}")
    existing = peek_borrow(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    minuend: object,
    subtrahend: object,
    *,
    floor: object,
    slot: object,
    wrap_requested: object = False,
    timeout: object = False,
) -> Optional[str]:
    """Missing operand/intent/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or minuend is None or subtrahend is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(
        minuend, subtrahend, floor=floor,
        wrap_requested=wrap_requested, timeout=False,
    ) is None:
        return None
    return pin_borrow(
        table,
        bind_sub(
            intent, minuend, subtrahend, floor=floor, slot=slot,
            wrap_requested=wrap_requested),
    )
