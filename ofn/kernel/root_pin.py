"""Pin a SquareBind so the recorded square cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → value:root:family).
The same encoding again is already_pinned. A different value,
root, or family on the same slot fails closed as
root_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from pow2/log2, prime/composite, even/odd,
remainder/leftover, quotient/divide, hex/width, byte/length,
above/below, inclusive/exclusive, and digest/fold.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .square_class import (
    FAMILIES,
    OTHER,
    SAMPLE,
    SQUARE,
    ZERO,
    SquareBind,
    bind_square,
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
    """A root pin never authorizes a send. Structurally False."""
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


def missing_root_is_zero() -> bool:
    """Structurally False. Missing root is UNKNOWN, not 0."""
    return False


def measured_zero_is_square() -> bool:
    """Structurally False. A measured 0 is ZERO, never SQUARE."""
    return False


def floor_root_is_exact() -> bool:
    """Structurally False. Only an exact square root is recorded."""
    return False


def pin_allows_send(bind: SquareBind) -> bool:
    """Structurally False. Even a sample bind is not send_authorized."""
    if not isinstance(bind, SquareBind):
        raise FailClosedError(f"bind must be a SquareBind: {bind!r}")
    return False


def pin_allows_sample(bind: SquareBind) -> bool:
    """True only when the pinned intent is sample and family is square.

    This is not a grant of sampling and not send_authorized.
    HALT still stops the factory START. ZERO and OTHER are
    recorded, not authorized as an exact-square sample.
    """
    if not isinstance(bind, SquareBind):
        raise FailClosedError(f"bind must be a SquareBind: {bind!r}")
    return bind.intent == SAMPLE and bind.family == SQUARE


def _encode(bind: SquareBind) -> str:
    if bind.family == OTHER:
        root_text = "-"
    elif bind.root is None:
        raise FailClosedError(
            f"square/zero bind missing exact root: {bind!r}")
    else:
        root_text = str(bind.root)
    return f"{bind.value}:{root_text}:{bind.family}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_root(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    value_text, root_text, family = pinned.split(":")
    if family not in FAMILIES:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not value_text.isdigit():
        raise FailClosedError(f"pinned value drifted: {pinned!r}")
    if family == OTHER:
        if root_text != "-":
            raise FailClosedError(f"pinned other-root drifted: {pinned!r}")
    else:
        if not root_text.isdigit():
            raise FailClosedError(f"pinned root drifted: {pinned!r}")
        if family == ZERO and (value_text != "0" or root_text != "0"):
            raise FailClosedError(f"pinned zero drifted: {pinned!r}")
    return pinned


def pin_root(
    table: MutableMapping[str, str],
    bind: SquareBind,
) -> str:
    """Record (slot → value:root:family) at most once per distinct encoding.

    First pin → pinned. Same encoding again → already_pinned.
    Different value, root, or family on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, SquareBind):
        raise FailClosedError(f"bind must be a SquareBind: {bind!r}")
    checked = bind_square(bind.intent, bind.value, slot=bind.slot)
    if (
        checked.family != bind.family
        or checked.value != bind.value
        or checked.root != bind.root
    ):
        raise FailClosedError(
            "SquareBind drifted from re-bind: "
            f"have family={bind.family!r} value={bind.value!r} "
            f"root={bind.root!r}")
    existing = peek_root(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"root_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: SquareBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, SquareBind):
        raise FailClosedError(f"bind must be a SquareBind: {bind!r}")
    existing = peek_root(table, bind.slot)
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
    return pin_root(table, bind_square(intent, value, slot=slot))
