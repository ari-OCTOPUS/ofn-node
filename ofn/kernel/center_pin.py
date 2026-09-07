"""Pin a MidBind so the recorded middle cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → family:length).
The same pair again is already_pinned. A different family
or length on the same slot fails closed as center_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

pin_allows_center only for center+odd_center or center+single.
even_split and empty are recorded, not a unique-center grant.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from head/tail (#226), carve/extract (#225),
remainder/leftover (#204), digest/fold (#152), unpublished
offset/range, unpublished prefix/stem, unpublished
watermark/high, unpublished cursor/advance, unpublished
checkpoint/mark, unpublished splice/stitch, and payload_bound.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .mid_class import (
    CENTER,
    EMPTY,
    EVEN_SPLIT,
    ODD_CENTER,
    SINGLE,
    MidBind,
    bind_mid,
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
    """A center pin never authorizes a send. Structurally False."""
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


def even_split_is_zero() -> bool:
    """Structurally False. Missing unique center is UNKNOWN, not 0."""
    return False


def peek_writes() -> bool:
    """Structurally False. peek never writes."""
    return False


def _encode(bind: MidBind) -> str:
    return f"{bind.family}:{bind.length}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def pin_allows_send(bind: MidBind) -> bool:
    """Structurally False. Even a center bind is not send_authorized."""
    if not isinstance(bind, MidBind):
        raise FailClosedError(f"bind must be a MidBind: {bind!r}")
    return False


def pin_allows_center(bind: MidBind) -> bool:
    """True only when the pinned intent is center and family is unique.

    Unique means odd_center or single. This is not a grant of
    centering and not send_authorized. HALT still stops the
    factory START. even_split / empty are recorded, not
    authorized as a unique-center take.
    """
    if not isinstance(bind, MidBind):
        raise FailClosedError(f"bind must be a MidBind: {bind!r}")
    return bind.intent == CENTER and bind.family in {ODD_CENTER, SINGLE}


def peek_center(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    if type(pinned) is not str or pinned.count(":") != 1:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    family, length_text = pinned.split(":")
    if family not in {EMPTY, SINGLE, ODD_CENTER, EVEN_SPLIT}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not length_text.isdigit():
        raise FailClosedError(f"pinned length drifted: {pinned!r}")
    return pinned


def pin_center(
    table: MutableMapping[str, str],
    bind: MidBind,
) -> str:
    """Record (slot → family:length) at most once per distinct pair.

    First pin → pinned. Same pair again → already_pinned.
    Different family or length on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, MidBind):
        raise FailClosedError(f"bind must be a MidBind: {bind!r}")
    checked = bind_mid(
        bind.intent,
        bind.length,
        slot=bind.slot,
    )
    if checked.family != bind.family or checked.length != bind.length:
        raise FailClosedError(
            "MidBind drifted from re-bind: "
            f"have family={bind.family!r} length={bind.length!r}")
    existing = peek_center(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"center_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: MidBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, MidBind):
        raise FailClosedError(f"bind must be a MidBind: {bind!r}")
    existing = peek_center(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    length: object,
    *,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing length/intent/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or length is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(length, timeout=False) is None:
        return None
    return pin_center(
        table, bind_mid(intent, length, slot=slot))
