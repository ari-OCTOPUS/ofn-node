"""Pin a LeftBind so the recorded side cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → family:index:origin).
The same triple again is already_pinned. A different family,
index, or origin on the same slot fails closed as
right_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

pin_allows_left only for mark+left. pin_allows_right only
for mark+right. AT is recorded, not a left grant and not a
right grant.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from near/far (#228), mid/center (#227),
head/tail (#226), carve/extract (#225), remainder/leftover
(#204), hysteresis/band (#217), digest/fold (#152),
unpublished offset/range, unpublished watermark/high,
unpublished prefix/stem, unpublished splice/stitch, and
payload_bound.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .left_class import (
    AT,
    LEFT,
    MARK,
    RIGHT,
    LeftBind,
    bind_left,
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
    """A right pin never authorizes a send. Structurally False."""
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


def missing_signed_is_zero() -> bool:
    """Structurally False. Missing signed offset is UNKNOWN, not 0."""
    return False


def at_is_send() -> bool:
    """Structurally False. AT is a family, not a send."""
    return False


def pin_allows_send(bind: LeftBind) -> bool:
    """Structurally False. Even a mark bind is not send_authorized."""
    if not isinstance(bind, LeftBind):
        raise FailClosedError(f"bind must be a LeftBind: {bind!r}")
    return False


def pin_allows_left(bind: LeftBind) -> bool:
    """True only when the pinned intent is mark and family is left.

    This is not a grant of sending and not send_authorized.
    HALT still stops the factory START. AT / RIGHT are recorded,
    not authorized as left.
    """
    if not isinstance(bind, LeftBind):
        raise FailClosedError(f"bind must be a LeftBind: {bind!r}")
    return bind.intent == MARK and bind.family == LEFT


def pin_allows_right(bind: LeftBind) -> bool:
    """True only when the pinned intent is mark and family is right.

    This is not a grant of sending and not send_authorized.
    """
    if not isinstance(bind, LeftBind):
        raise FailClosedError(f"bind must be a LeftBind: {bind!r}")
    return bind.intent == MARK and bind.family == RIGHT


def _encode(bind: LeftBind) -> str:
    return f"{bind.family}:{bind.index}:{bind.origin}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_right(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    family, index_text, origin_text = pinned.split(":")
    if family not in {AT, LEFT, RIGHT}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    for part, label in (
        (index_text, "index"),
        (origin_text, "origin"),
    ):
        if part.startswith("-"):
            digits = part[1:]
        else:
            digits = part
        if not digits.isdigit():
            raise FailClosedError(
                f"pinned {label} drifted: {pinned!r}")
    return pinned


def pin_right(
    table: MutableMapping[str, str],
    bind: LeftBind,
) -> str:
    """Record (slot → family:index:origin) at most once per distinct triple.

    First pin → pinned. Same triple again → already_pinned.
    Different family, index, or origin on the same slot
    fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, LeftBind):
        raise FailClosedError(f"bind must be a LeftBind: {bind!r}")
    checked = bind_left(
        bind.intent,
        bind.index,
        origin=bind.origin,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.index != bind.index
        or checked.origin != bind.origin
        or checked.signed != bind.signed
    ):
        raise FailClosedError(
            "LeftBind drifted from re-bind: "
            f"have family={bind.family!r} index={bind.index!r} "
            f"origin={bind.origin!r} signed={bind.signed!r}")
    existing = peek_right(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"right_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: LeftBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, LeftBind):
        raise FailClosedError(f"bind must be a LeftBind: {bind!r}")
    existing = peek_right(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    index: object,
    *,
    origin: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing index/intent/origin/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or index is None or origin is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(index, origin=origin, timeout=False) is None:
        return None
    return pin_right(
        table,
        bind_left(intent, index, origin=origin, slot=slot),
    )
