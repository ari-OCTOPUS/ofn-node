"""Pin a GraceBind so the recorded linger cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(slot → elapsed:due_after:linger_after:family).
The same quadruple again is already_pinned. A different
elapsed, due_after, linger_after, or family on the same
slot fails closed as linger_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from stale/fresh, lease/renew, aging/decay,
ttl/expire, compact/retain, deadline_window, and seq.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .grace_class import (
    GRACE,
    LAPSED,
    LINGER,
    LIVE,
    GraceBind,
    bind_grace,
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
    """A linger pin never authorizes a send. Structurally False."""
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


def elapsed_is_zero() -> bool:
    """Structurally False. Missing elapsed is UNKNOWN, not 0."""
    return False


def peek_writes() -> bool:
    """Structurally False. peek never writes."""
    return False


def pin_allows_send(bind: GraceBind) -> bool:
    """Structurally False. Even a linger bind is not send_authorized."""
    if not isinstance(bind, GraceBind):
        raise FailClosedError(f"bind must be a GraceBind: {bind!r}")
    return False


def pin_allows_linger(bind: GraceBind) -> bool:
    """True only when the pinned intent is linger and family is grace.

    This is not a grant of lingering and not send_authorized.
    HALT still stops the factory START. A live family is
    recorded, not authorized as a linger. A lapsed family is
    recorded, not a linger grant.
    """
    if not isinstance(bind, GraceBind):
        raise FailClosedError(f"bind must be a GraceBind: {bind!r}")
    return bind.intent == LINGER and bind.family == GRACE


def _encode(bind: GraceBind) -> str:
    return (
        f"{bind.elapsed_ticks}:{bind.due_after}:"
        f"{bind.linger_after}:{bind.family}"
    )


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_linger(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    elapsed_text, due_text, linger_text, family = pinned.split(":")
    if family not in {LIVE, GRACE, LAPSED}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if (
        not elapsed_text.isdigit()
        or not due_text.isdigit()
        or not linger_text.isdigit()
    ):
        raise FailClosedError(
            f"pinned elapsed/due/linger drifted: {pinned!r}")
    return pinned


def pin_linger(
    table: MutableMapping[str, str],
    bind: GraceBind,
) -> str:
    """Record the quadruple at most once per distinct encoding.

    First pin → pinned. Same quadruple again → already_pinned.
    Different elapsed, due_after, linger_after, or family on
    the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, GraceBind):
        raise FailClosedError(f"bind must be a GraceBind: {bind!r}")
    checked = bind_grace(
        bind.intent,
        bind.elapsed_ticks,
        due_after=bind.due_after,
        linger_after=bind.linger_after,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.elapsed_ticks != bind.elapsed_ticks
        or checked.due_after != bind.due_after
        or checked.linger_after != bind.linger_after
        or checked.remaining != bind.remaining
    ):
        raise FailClosedError(
            "GraceBind drifted from re-bind: "
            f"have family={bind.family!r} elapsed={bind.elapsed_ticks!r} "
            f"due_after={bind.due_after!r} linger_after={bind.linger_after!r} "
            f"remaining={bind.remaining!r}")
    existing = peek_linger(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"linger_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: GraceBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, GraceBind):
        raise FailClosedError(f"bind must be a GraceBind: {bind!r}")
    existing = peek_linger(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    elapsed_ticks: object,
    *,
    due_after: object,
    linger_after: object,
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
        or elapsed_ticks is None
        or due_after is None
        or linger_after is None
        or slot is None
    ):
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(
        elapsed_ticks,
        due_after=due_after,
        linger_after=linger_after,
        timeout=False,
    ) is None:
        return None
    return pin_linger(
        table,
        bind_grace(
            intent,
            elapsed_ticks,
            due_after=due_after,
            linger_after=linger_after,
            slot=slot,
        ),
    )
