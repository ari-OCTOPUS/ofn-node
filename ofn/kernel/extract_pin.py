"""Pin a CarveBind so the recorded extract cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(slot → cut_at:guest_len:host_len:family).
The same quadruple again is already_pinned. A different cut,
guest, host, or family on the same slot fails closed as
extract_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from remainder/leftover, splice/stitch, offset/range,
segment/slice, stride/step, window/bound, payload_bound,
token_ceiling, and seq.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .carve_class import (
    CARVE,
    FITS,
    OVERHANG,
    PAST,
    CarveBind,
    bind_carve,
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
    """An extract pin never authorizes a send. Structurally False."""
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


def extracted_is_zero() -> bool:
    """Structurally False. Missing extracted length is UNKNOWN, not 0."""
    return False


def pin_allows_send(bind: CarveBind) -> bool:
    """Structurally False. Even a carve bind is not send_authorized."""
    if not isinstance(bind, CarveBind):
        raise FailClosedError(f"bind must be a CarveBind: {bind!r}")
    return False


def pin_allows_carve(bind: CarveBind) -> bool:
    """True only when the pinned intent is carve and family is fits.

    This is not a grant of carving and not send_authorized.
    HALT still stops the factory START. overhang / past are
    recorded, not authorized as a clean extract.
    """
    if not isinstance(bind, CarveBind):
        raise FailClosedError(f"bind must be a CarveBind: {bind!r}")
    return bind.intent == CARVE and bind.family == FITS


def _encode(bind: CarveBind) -> str:
    return f"{bind.cut_at}:{bind.guest_len}:{bind.host_len}:{bind.family}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_extract(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    cut_text, guest_text, host_text, family = pinned.split(":")
    if family not in {FITS, OVERHANG, PAST}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if (
        not cut_text.isdigit()
        or not guest_text.isdigit()
        or not host_text.isdigit()
    ):
        raise FailClosedError(f"pinned cut/guest/host drifted: {pinned!r}")
    return pinned


def pin_extract(
    table: MutableMapping[str, str],
    bind: CarveBind,
) -> str:
    """Record (slot → cut:guest:host:family) at most once per quadruple.

    First pin → pinned. Same quadruple again → already_pinned.
    Different cut, guest, host, or family on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, CarveBind):
        raise FailClosedError(f"bind must be a CarveBind: {bind!r}")
    checked = bind_carve(
        bind.intent,
        bind.host_len,
        cut_at=bind.cut_at,
        guest_len=bind.guest_len,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.cut_at != bind.cut_at
        or checked.guest_len != bind.guest_len
        or checked.host_len != bind.host_len
        or checked.extracted != bind.extracted
    ):
        raise FailClosedError(
            "CarveBind drifted from re-bind: "
            f"have family={bind.family!r} cut_at={bind.cut_at!r} "
            f"guest_len={bind.guest_len!r} host_len={bind.host_len!r} "
            f"extracted={bind.extracted!r}")
    existing = peek_extract(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"extract_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: CarveBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, CarveBind):
        raise FailClosedError(f"bind must be a CarveBind: {bind!r}")
    existing = peek_extract(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    host_len: object,
    *,
    cut_at: object,
    guest_len: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing sides or timeout is UNKNOWN (None).

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
        or host_len is None
        or cut_at is None
        or guest_len is None
        or slot is None
    ):
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(
        host_len, cut_at=cut_at, guest_len=guest_len, timeout=False,
    ) is None:
        return None
    return pin_extract(
        table,
        bind_carve(
            intent, host_len, cut_at=cut_at, guest_len=guest_len, slot=slot),
    )
