"""Pin a ByteBind so the recorded length cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → family:size:bound). The
same triple again is already_pinned. A different family, size,
or bound on the same slot fails closed as length_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from format/parse, codec/encode, utf8/decode,
hex/width, payload_bound, token_ceiling, and scope/limit.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .byte_class import (
    BOUNDED,
    EMPTY,
    MEASURE,
    OVERSIZE,
    ByteBind,
    bind_bytes,
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
    """A length pin never authorizes a send. Structurally False."""
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


def pin_allows_send(bind: ByteBind) -> bool:
    """Structurally False. Even a measure bind is not send_authorized."""
    if not isinstance(bind, ByteBind):
        raise FailClosedError(f"bind must be a ByteBind: {bind!r}")
    return False


def pin_allows_measure(bind: ByteBind) -> bool:
    """True only when the pinned intent is measure and family is
    empty or bounded.

    This is not a grant of measuring and not send_authorized.
    HALT still stops the factory START. Oversize is recorded,
    not authorized.
    """
    if not isinstance(bind, ByteBind):
        raise FailClosedError(f"bind must be a ByteBind: {bind!r}")
    return bind.intent == MEASURE and bind.family in {EMPTY, BOUNDED}


def _encode(bind: ByteBind) -> str:
    return f"{bind.family}:{bind.size}:{bind.bound}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_length(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    family, size_text, bound_text = pinned.split(":")
    if family not in {EMPTY, BOUNDED, OVERSIZE}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not size_text.isdigit() or not bound_text.isdigit():
        raise FailClosedError(f"pinned size/bound drifted: {pinned!r}")
    return pinned


def pin_length(
    table: MutableMapping[str, str],
    bind: ByteBind,
) -> str:
    """Record (slot → family:size:bound) at most once per distinct triple.

    First pin → pinned. Same triple again → already_pinned.
    Different family, size, or bound on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, ByteBind):
        raise FailClosedError(f"bind must be a ByteBind: {bind!r}")
    checked = bind_bytes(
        bind.intent,
        b"\x00" * bind.size if bind.size else b"",
        bound=bind.bound,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.size != bind.size
        or checked.bound != bind.bound
    ):
        raise FailClosedError(
            "ByteBind drifted from re-bind: "
            f"have family={bind.family!r} size={bind.size!r} "
            f"bound={bind.bound!r}")
    existing = peek_length(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"length_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: ByteBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, ByteBind):
        raise FailClosedError(f"bind must be a ByteBind: {bind!r}")
    existing = peek_length(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    payload: object,
    *,
    bound: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing payload/intent/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or payload is None or slot is None:
        return None
    # classify_* keep the fail-closed wall before bind.
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(payload, bound=bound, timeout=False) is None:
        return None
    return pin_length(
        table, bind_bytes(intent, payload, bound=bound, slot=slot))
