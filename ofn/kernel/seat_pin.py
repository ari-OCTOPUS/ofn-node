"""Pin a QuorumBind so the recorded threshold cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(seat → family:present:required).
The same pair again is already_pinned. A different
family or counts on the same seat fails closed
as quorum_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from capacity/room, approval/independent,
census, slot/occupy, lease/renew, parity/check,
receipts, and dedup.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .quorum_class import (
    QUORUM,
    RECORD,
    SHORT,
    QuorumBind,
    bind_quorum,
    classify_intent,
    classify_threshold,
)

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A seat pin never authorizes a send. Structurally False."""
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


def quorum_is_authorized() -> bool:
    """Structurally False. quorum is a family, not send_authorized."""
    return False


def pin_allows_send(bind: QuorumBind) -> bool:
    """Structurally False. Even a record bind is not send_authorized."""
    if not isinstance(bind, QuorumBind):
        raise FailClosedError(f"bind must be a QuorumBind: {bind!r}")
    return False


def pin_allows_record(bind: QuorumBind) -> bool:
    """True only when the pinned intent is record and family is
    quorum or short.

    Both families are valid thresholds. This is not a grant of
    sending and not send_authorized. HALT still stops the
    factory START.
    """
    if not isinstance(bind, QuorumBind):
        raise FailClosedError(f"bind must be a QuorumBind: {bind!r}")
    return bind.intent == RECORD and bind.family in {QUORUM, SHORT}


def _encode(bind: QuorumBind) -> str:
    return f"{bind.family}:{bind.present}:{bind.required}"


def _refuse_sealed_seat(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"seat names a sealed send/ready state: {value!r}")


def peek_seat(table: Mapping[str, str], seat: object) -> Optional[str]:
    """Return the pinned encoding or None.

    None is UNKNOWN, not FALSE. Never writes. Missing table key
    is UNKNOWN. A sealed seat fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if type(seat) is not str:
        if seat is None:
            return None
        raise FailClosedError(f"seat must be a str or None: {seat!r}")
    if not seat.strip():
        raise FailClosedError("seat is empty")
    _refuse_sealed_seat(seat)
    text = seat.strip()
    if text not in table:
        return None
    pinned = table[text]
    if type(pinned) is not str or pinned.count(":") != 2:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    family, present_text, required_text = pinned.split(":")
    if family not in {QUORUM, SHORT}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not present_text.isdigit() or not required_text.isdigit():
        raise FailClosedError(f"pinned counts drifted: {pinned!r}")
    return pinned


def pin_seat(
    table: MutableMapping[str, str],
    bind: QuorumBind,
) -> str:
    """Record (seat → family:present:required) at most once.

    First pin → pinned. Same pair again → already_pinned.
    Different family or counts on the same seat fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, QuorumBind):
        raise FailClosedError(f"bind must be a QuorumBind: {bind!r}")
    checked = bind_quorum(
        bind.intent,
        bind.present,
        bind.required,
        seat=bind.seat,
    )
    if (
        checked.family != bind.family
        or checked.present != bind.present
        or checked.required != bind.required
    ):
        raise FailClosedError(
            "QuorumBind drifted from re-bind: "
            f"have family={bind.family!r} present={bind.present!r} "
            f"required={bind.required!r}")
    existing = peek_seat(table, checked.seat)
    encoded = _encode(checked)
    if existing is None:
        table[checked.seat] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"quorum_collision: seat {checked.seat!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: QuorumBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, QuorumBind):
        raise FailClosedError(f"bind must be a QuorumBind: {bind!r}")
    existing = peek_seat(table, bind.seat)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    present: object,
    required: object,
    *,
    seat: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing present/required/intent/seat or timeout is UNKNOWN (None).

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
        or present is None
        or required is None
        or seat is None
    ):
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_threshold(present, required, timeout=False) is None:
        return None
    return pin_seat(
        table,
        bind_quorum(intent, present, required, seat=seat),
    )
