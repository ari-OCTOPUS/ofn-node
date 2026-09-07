"""Pin a NearBind so the recorded distance cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → family:index:origin:radius).
The same quadruple again is already_pinned. A different family,
index, origin, or radius on the same slot fails closed as
far_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

pin_allows_near only for mark+near. pin_allows_far only for
mark+far. AT is recorded, not a near grant and not a far grant.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from head/tail (#226), mid/center (#227),
carve/extract (#225), remainder/leftover (#204),
hysteresis/band (#217), digest/fold (#152), unpublished
offset/range, unpublished watermark/high, unpublished
prefix/stem, unpublished splice/stitch, and payload_bound.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .near_class import (
    AT,
    FAR,
    MARK,
    NEAR,
    NearBind,
    bind_near,
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
    """A far pin never authorizes a send. Structurally False."""
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


def missing_distance_is_zero() -> bool:
    """Structurally False. Missing distance is UNKNOWN, not 0."""
    return False


def at_is_send() -> bool:
    """Structurally False. AT is a family, not a send."""
    return False


def pin_allows_send(bind: NearBind) -> bool:
    """Structurally False. Even a mark bind is not send_authorized."""
    if not isinstance(bind, NearBind):
        raise FailClosedError(f"bind must be a NearBind: {bind!r}")
    return False


def pin_allows_near(bind: NearBind) -> bool:
    """True only when the pinned intent is mark and family is near.

    This is not a grant of sending and not send_authorized.
    HALT still stops the factory START. AT / FAR are recorded,
    not authorized as near.
    """
    if not isinstance(bind, NearBind):
        raise FailClosedError(f"bind must be a NearBind: {bind!r}")
    return bind.intent == MARK and bind.family == NEAR


def pin_allows_far(bind: NearBind) -> bool:
    """True only when the pinned intent is mark and family is far.

    This is not a grant of sending and not send_authorized.
    """
    if not isinstance(bind, NearBind):
        raise FailClosedError(f"bind must be a NearBind: {bind!r}")
    return bind.intent == MARK and bind.family == FAR


def _encode(bind: NearBind) -> str:
    return f"{bind.family}:{bind.index}:{bind.origin}:{bind.radius}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_far(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    family, index_text, origin_text, radius_text = pinned.split(":")
    if family not in {AT, NEAR, FAR}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    for part, label in (
        (index_text, "index"),
        (origin_text, "origin"),
        (radius_text, "radius"),
    ):
        if part.startswith("-"):
            digits = part[1:]
        else:
            digits = part
        if not digits.isdigit():
            raise FailClosedError(
                f"pinned {label} drifted: {pinned!r}")
    return pinned


def pin_far(
    table: MutableMapping[str, str],
    bind: NearBind,
) -> str:
    """Record (slot → family:index:origin:radius) at most once per distinct quadruple.

    First pin → pinned. Same quadruple again → already_pinned.
    Different family, index, origin, or radius on the same slot
    fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, NearBind):
        raise FailClosedError(f"bind must be a NearBind: {bind!r}")
    checked = bind_near(
        bind.intent,
        bind.index,
        origin=bind.origin,
        radius=bind.radius,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.index != bind.index
        or checked.origin != bind.origin
        or checked.radius != bind.radius
        or checked.distance != bind.distance
    ):
        raise FailClosedError(
            "NearBind drifted from re-bind: "
            f"have family={bind.family!r} index={bind.index!r} "
            f"origin={bind.origin!r} radius={bind.radius!r} "
            f"distance={bind.distance!r}")
    existing = peek_far(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"far_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: NearBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, NearBind):
        raise FailClosedError(f"bind must be a NearBind: {bind!r}")
    existing = peek_far(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    index: object,
    *,
    origin: object,
    radius: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing index/intent/origin/radius/slot or timeout is UNKNOWN (None).

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
        or index is None
        or origin is None
        or radius is None
        or slot is None
    ):
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(index, origin=origin, radius=radius, timeout=False) is None:
        return None
    return pin_far(
        table,
        bind_near(intent, index, origin=origin, radius=radius, slot=slot),
    )
