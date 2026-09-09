"""Pin a TetrahedralBind so the recorded pyramid cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(slot → value:index:family).
The same triple again is already_pinned. A different value,
index, or family on the same slot fails closed as
pyramid_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from pentagonal/figure, hexagonal/lattice,
heptagonal/gonal, octagonal/vertex, triangular/series,
cube/cubic, square/root, remainder/leftover, and
payload_bound.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .tetrahedral_class import (
    OTHER,
    SAMPLE,
    TETRAHEDRAL,
    ZERO,
    TetrahedralBind,
    bind_tetrahedral,
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
    """A pyramid pin never authorizes a send. Structurally False."""
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


def missing_index_is_zero() -> bool:
    """Structurally False. Missing index is UNKNOWN, not 0."""
    return False


def pin_allows_send(bind: TetrahedralBind) -> bool:
    """Structurally False. Even a sample bind is not send_authorized."""
    if not isinstance(bind, TetrahedralBind):
        raise FailClosedError(f"bind must be a TetrahedralBind: {bind!r}")
    return False


def pin_allows_sample(bind: TetrahedralBind) -> bool:
    """True only when the pinned intent is sample and family is tetrahedral.

    This is not a grant of sampling and not send_authorized.
    HALT still stops the factory START. zero / other are
    recorded, not authorized as a clean pyramid.
    """
    if not isinstance(bind, TetrahedralBind):
        raise FailClosedError(f"bind must be a TetrahedralBind: {bind!r}")
    return bind.intent == SAMPLE and bind.family == TETRAHEDRAL


def _encode(bind: TetrahedralBind) -> str:
    idx = "-" if bind.index is None else str(bind.index)
    return f"{bind.value}:{idx}:{bind.family}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_pyramid(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    value_text, index_text, family = pinned.split(":")
    if family not in {ZERO, TETRAHEDRAL, OTHER}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not value_text.isdigit():
        raise FailClosedError(f"pinned value drifted: {pinned!r}")
    if index_text != "-":
        if not index_text.isdigit():
            raise FailClosedError(f"pinned index drifted: {pinned!r}")
        if family != TETRAHEDRAL:
            raise FailClosedError(f"pinned index drifted: {pinned!r}")
    elif family == TETRAHEDRAL:
        raise FailClosedError(f"pinned tetrahedral missing index: {pinned!r}")
    return pinned


def pin_pyramid(
    table: MutableMapping[str, str],
    bind: TetrahedralBind,
) -> str:
    """Record (slot → value:index:family) at most once per distinct encoding.

    First pin → pinned. Same encoding again → already_pinned.
    Different value, index, or family on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, TetrahedralBind):
        raise FailClosedError(f"bind must be a TetrahedralBind: {bind!r}")
    checked = bind_tetrahedral(
        bind.intent,
        bind.value,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.value != bind.value
        or checked.index != bind.index
    ):
        raise FailClosedError(
            "TetrahedralBind drifted from re-bind: "
            f"have family={bind.family!r} value={bind.value!r} "
            f"index={bind.index!r}")
    existing = peek_pyramid(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"pyramid_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: TetrahedralBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, TetrahedralBind):
        raise FailClosedError(f"bind must be a TetrahedralBind: {bind!r}")
    existing = peek_pyramid(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    value: object,
    *,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing intent/value/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or value is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(value, timeout=False) is None:
        return None
    return pin_pyramid(
        table, bind_tetrahedral(intent, value, slot=slot))
