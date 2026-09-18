"""Pin a StrideBind so the recorded step cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → family:stride:from_index).
The same triple again is already_pinned. A different family,
stride, or from_index on the same slot fails closed as
step_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from seq.SeqCursor, segment/slice, byte/length,
unpublished offset/range, unpublished scan/walk, and
unpublished cursor/advance.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .stride_class import (
    ADMIT,
    SKIP,
    UNIT,
    StrideBind,
    bind_stride,
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
    """A step pin never authorizes a send. Structurally False."""
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


def pin_allows_send(bind: StrideBind) -> bool:
    """Structurally False. Even an admit bind is not send_authorized."""
    if not isinstance(bind, StrideBind):
        raise FailClosedError(f"bind must be a StrideBind: {bind!r}")
    return False


def pin_allows_admit(bind: StrideBind) -> bool:
    """True only when the pinned intent is admit and family is
    unit or skip.

    This is not a grant of admitting and not send_authorized.
    HALT still stops the factory START. skip is recorded,
    not authorized.
    """
    if not isinstance(bind, StrideBind):
        raise FailClosedError(f"bind must be a StrideBind: {bind!r}")
    return bind.intent == ADMIT and bind.family in {UNIT, SKIP}


def _encode(bind: StrideBind) -> str:
    return f"{bind.family}:{bind.stride}:{bind.from_index}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_step(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    family, stride_text, from_text = pinned.split(":")
    if family not in {UNIT, SKIP}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not stride_text.isdigit() or not from_text.isdigit():
        raise FailClosedError(f"pinned stride/from drifted: {pinned!r}")
    return pinned


def pin_step(
    table: MutableMapping[str, str],
    bind: StrideBind,
) -> str:
    """Record (slot → family:stride:from_index) at most once per triple.

    First pin → pinned. Same triple again → already_pinned.
    Different family, stride, or from_index on the same slot
    fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, StrideBind):
        raise FailClosedError(f"bind must be a StrideBind: {bind!r}")
    checked = bind_stride(
        bind.intent,
        bind.stride,
        from_index=bind.from_index,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.stride != bind.stride
        or checked.from_index != bind.from_index
        or checked.next_index != bind.next_index
    ):
        raise FailClosedError(
            "StrideBind drifted from re-bind: "
            f"have family={bind.family!r} stride={bind.stride!r} "
            f"from_index={bind.from_index!r} next_index={bind.next_index!r}")
    existing = peek_step(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"step_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: StrideBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, StrideBind):
        raise FailClosedError(f"bind must be a StrideBind: {bind!r}")
    existing = peek_step(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    stride: object,
    *,
    from_index: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing stride/intent/from_index/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or stride is None or from_index is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(stride, timeout=False) is None:
        return None
    return pin_step(
        table,
        bind_stride(
            intent, stride, from_index=from_index, slot=slot),
    )
