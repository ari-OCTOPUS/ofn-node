"""Pin a HeadBind so the recorded end cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → family:length:index).
The same triple again is already_pinned. A different family,
length, or index on the same slot fails closed as tail_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

pin_allows_take only for take+tail or take+single. head,
interior, empty, and past are recorded, not a tail grant.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from watermark/high, cursor/advance, checkpoint/mark,
seq, carve/extract, remainder/leftover, offset/range,
prefix/stem, and payload_bound.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .head_class import (
    EMPTY,
    HEAD,
    INTERIOR,
    PAST,
    SINGLE,
    TAIL,
    TAKE,
    HeadBind,
    bind_head,
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
    """A tail pin never authorizes a send. Structurally False."""
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


def empty_is_zero() -> bool:
    """Structurally False. Missing length is UNKNOWN, not 0."""
    return False


def peek_writes() -> bool:
    """Structurally False. peek never writes."""
    return False


def _encode(bind: HeadBind) -> str:
    return f"{bind.family}:{bind.length}:{bind.index}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def pin_allows_send(bind: HeadBind) -> bool:
    """Structurally False. Even a take bind is not send_authorized."""
    if not isinstance(bind, HeadBind):
        raise FailClosedError(f"bind must be a HeadBind: {bind!r}")
    return False


def pin_allows_take(bind: HeadBind) -> bool:
    """True only when the pinned intent is take and family is tail or single.

    This is not a grant of taking and not send_authorized.
    HALT still stops the factory START. head / interior / empty /
    past are recorded, not authorized as a tail take.
    """
    if not isinstance(bind, HeadBind):
        raise FailClosedError(f"bind must be a HeadBind: {bind!r}")
    return bind.intent == TAKE and bind.family in {TAIL, SINGLE}


def peek_tail(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    family, length_text, index_text = pinned.split(":")
    if family not in {EMPTY, SINGLE, HEAD, TAIL, INTERIOR, PAST}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not length_text.isdigit() or not index_text.isdigit():
        raise FailClosedError(f"pinned length/index drifted: {pinned!r}")
    return pinned


def pin_tail(
    table: MutableMapping[str, str],
    bind: HeadBind,
) -> str:
    """Record (slot → family:length:index) at most once per distinct triple.

    First pin → pinned. Same triple again → already_pinned.
    Different family, length, or index on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, HeadBind):
        raise FailClosedError(f"bind must be a HeadBind: {bind!r}")
    checked = bind_head(
        bind.intent,
        bind.length,
        index=bind.index,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.length != bind.length
        or checked.index != bind.index
    ):
        raise FailClosedError(
            "HeadBind drifted from re-bind: "
            f"have family={bind.family!r} length={bind.length!r} "
            f"index={bind.index!r}")
    existing = peek_tail(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"tail_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: HeadBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, HeadBind):
        raise FailClosedError(f"bind must be a HeadBind: {bind!r}")
    existing = peek_tail(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    length: object,
    *,
    index: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing length/intent/index/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or length is None or index is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(length, index=index, timeout=False) is None:
        return None
    return pin_tail(
        table, bind_head(intent, length, index=index, slot=slot))
