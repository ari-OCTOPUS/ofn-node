"""Pin an InclusiveBind so recorded inclusion cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → kind:bound:family).
The same triple again is already_pinned. A different kind,
bound, or family on the same slot fails closed as
exclusive_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from above/below, inside/outside, offset/range,
deadline_window, hysteresis, sign/magnitude, token_ceiling,
and seq.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .inclusive_class import (
    FAMILIES,
    INCLUSIVE,
    ON,
    SAMPLE,
    InclusiveBind,
    bind_inclusive,
    classify_family,
    classify_intent,
    classify_kind,
)

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """An exclusive pin never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A pin does not re-arm outbound."""
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


def exclusive_on_bound_is_on() -> bool:
    """Structurally False. Exclusive + equal is OUT, not ON."""
    return False


def pin_allows_send(bind: InclusiveBind) -> bool:
    """Structurally False. Even a sample bind is not send_authorized."""
    if not isinstance(bind, InclusiveBind):
        raise FailClosedError(f"bind must be an InclusiveBind: {bind!r}")
    return False


def pin_allows_sample(bind: InclusiveBind) -> bool:
    """True only when the pinned intent is sample and family is ON.

    This is not a grant of sampling and not send_authorized.
    HALT still stops the factory START. Exclusive OUT is
    recorded, not authorized as an on-bound sample.
    """
    if not isinstance(bind, InclusiveBind):
        raise FailClosedError(f"bind must be an InclusiveBind: {bind!r}")
    return bind.intent == SAMPLE and bind.family == ON and bind.kind == INCLUSIVE


def _encode(bind: InclusiveBind) -> str:
    return f"{bind.kind}:{bind.bound}:{bind.family}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_exclusive(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    kind_text, bound_text, family = pinned.split(":")
    if family not in FAMILIES:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if kind_text not in {"inclusive", "exclusive"}:
        raise FailClosedError(f"pinned kind drifted: {kind_text!r}")
    if bound_text.startswith("-"):
        digits = bound_text[1:]
    else:
        digits = bound_text
    if not digits.isdigit():
        raise FailClosedError(f"pinned bound drifted: {pinned!r}")
    return pinned


def pin_exclusive(
    table: MutableMapping[str, str],
    bind: InclusiveBind,
) -> str:
    """Record (slot → kind:bound:family) at most once per distinct triple.

    First pin → pinned. Same triple again → already_pinned.
    Different kind, bound, or family on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, InclusiveBind):
        raise FailClosedError(f"bind must be an InclusiveBind: {bind!r}")
    checked = bind_inclusive(
        bind.intent,
        bind.value,
        bound=bind.bound,
        kind=bind.kind,
        slot=bind.slot,
    )
    if (
        checked.kind != bind.kind
        or checked.family != bind.family
        or checked.value != bind.value
        or checked.bound != bind.bound
    ):
        raise FailClosedError(
            "InclusiveBind drifted from re-bind: "
            f"have kind={bind.kind!r} family={bind.family!r} "
            f"value={bind.value!r} bound={bind.bound!r}")
    existing = peek_exclusive(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"exclusive_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: InclusiveBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, InclusiveBind):
        raise FailClosedError(f"bind must be an InclusiveBind: {bind!r}")
    existing = peek_exclusive(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    value: object,
    *,
    bound: object,
    kind: object,
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
        or value is None
        or bound is None
        or kind is None
        or slot is None
    ):
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_kind(kind) == "UNKNOWN":
        return None
    if classify_family(value, bound=bound, kind=kind, timeout=False) is None:
        return None
    return pin_exclusive(
        table,
        bind_inclusive(
            intent, value, bound=bound, kind=kind, slot=slot),
    )
