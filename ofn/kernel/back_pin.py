"""Pin a FrontBind so the recorded depth cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → family:depth:plane).
The same triple again is already_pinned. A different family,
depth, or plane on the same slot fails closed as
back_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

pin_allows_back only for mark+back. pin_allows_front only
for mark+front. AT is recorded, not a back grant and not a
front grant.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from left/right (#229), near/far (#228),
mid/center (#227), head/tail (#226), carve/extract (#225),
remainder/leftover (#204), hysteresis/band (#217),
digest/fold (#152), unpublished offset/range, unpublished
watermark/high, unpublished prefix/stem, unpublished
splice/stitch, and payload_bound.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .front_class import (
    AT,
    BACK,
    FRONT,
    MARK,
    FrontBind,
    bind_front,
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
    """A back pin never authorizes a send. Structurally False."""
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
    """Structurally False. Missing signed depth is UNKNOWN, not 0."""
    return False


def at_is_send() -> bool:
    """Structurally False. AT is a family, not a send."""
    return False


def pin_allows_send(bind: FrontBind) -> bool:
    """Structurally False. Even a mark bind is not send_authorized."""
    if not isinstance(bind, FrontBind):
        raise FailClosedError(f"bind must be a FrontBind: {bind!r}")
    return False


def pin_allows_back(bind: FrontBind) -> bool:
    """True only when the pinned intent is mark and family is back.

    This is not a grant of sending and not send_authorized.
    HALT still stops the factory START. AT / FRONT are recorded,
    not authorized as back.
    """
    if not isinstance(bind, FrontBind):
        raise FailClosedError(f"bind must be a FrontBind: {bind!r}")
    return bind.intent == MARK and bind.family == BACK


def pin_allows_front(bind: FrontBind) -> bool:
    """True only when the pinned intent is mark and family is front.

    This is not a grant of sending and not send_authorized.
    """
    if not isinstance(bind, FrontBind):
        raise FailClosedError(f"bind must be a FrontBind: {bind!r}")
    return bind.intent == MARK and bind.family == FRONT


def _encode(bind: FrontBind) -> str:
    return f"{bind.family}:{bind.depth}:{bind.plane}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_back(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    family, depth_text, plane_text = pinned.split(":")
    if family not in {AT, BACK, FRONT}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    for part, label in (
        (depth_text, "depth"),
        (plane_text, "plane"),
    ):
        if part.startswith("-"):
            digits = part[1:]
        else:
            digits = part
        if not digits.isdigit():
            raise FailClosedError(
                f"pinned {label} drifted: {pinned!r}")
    return pinned


def pin_back(
    table: MutableMapping[str, str],
    bind: FrontBind,
) -> str:
    """Record (slot → family:depth:plane) at most once per distinct triple.

    First pin → pinned. Same triple again → already_pinned.
    Different family, depth, or plane on the same slot
    fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, FrontBind):
        raise FailClosedError(f"bind must be a FrontBind: {bind!r}")
    checked = bind_front(
        bind.intent,
        bind.depth,
        plane=bind.plane,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.depth != bind.depth
        or checked.plane != bind.plane
        or checked.signed != bind.signed
    ):
        raise FailClosedError(
            "FrontBind drifted from re-bind: "
            f"have family={bind.family!r} depth={bind.depth!r} "
            f"plane={bind.plane!r} signed={bind.signed!r}")
    existing = peek_back(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"back_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: FrontBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, FrontBind):
        raise FailClosedError(f"bind must be a FrontBind: {bind!r}")
    existing = peek_back(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    depth: object,
    *,
    plane: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing depth/intent/plane/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or depth is None or plane is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(depth, plane=plane, timeout=False) is None:
        return None
    return pin_back(
        table,
        bind_front(intent, depth, plane=plane, slot=slot),
    )
