"""Pin a SegmentBind so the recorded slice cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → kind:start:end:length).
The same quadruple again is already_pinned. A different kind,
start, end, or length on the same slot fails closed as
slice_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from byte/length, offset/range, overlap/collide,
payload_bound, window/bound, and split_view.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .segment_class import (
    BODY,
    CUT,
    FIT,
    HEADER,
    TRAILER,
    SegmentBind,
    bind_segment,
    classify_intent,
    classify_kind,
    classify_span,
)

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A slice pin never authorizes a send. Structurally False."""
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


def pin_allows_send(bind: SegmentBind) -> bool:
    """Structurally False. Even a cut bind is not send_authorized."""
    if not isinstance(bind, SegmentBind):
        raise FailClosedError(f"bind must be a SegmentBind: {bind!r}")
    return False


def pin_allows_cut(bind: SegmentBind) -> bool:
    """True only when the pinned intent is cut and span is fit.

    This is not a grant of cutting and not send_authorized.
    HALT still stops the factory START. Empty or overflow is
    recorded, not authorized.
    """
    if not isinstance(bind, SegmentBind):
        raise FailClosedError(f"bind must be a SegmentBind: {bind!r}")
    return bind.intent == CUT and bind.span == FIT and bind.kind in {
        HEADER, BODY, TRAILER,
    }


def _encode(bind: SegmentBind) -> str:
    return f"{bind.kind}:{bind.start}:{bind.end}:{bind.length}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_slice(table: Mapping[str, str], slot: object) -> Optional[str]:
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
    kind, start_text, end_text, length_text = pinned.split(":")
    if kind not in {HEADER, BODY, TRAILER}:
        raise FailClosedError(f"pinned kind drifted: {kind!r}")
    if (
        not start_text.isdigit()
        or not end_text.isdigit()
        or not length_text.isdigit()
    ):
        raise FailClosedError(f"pinned offsets drifted: {pinned!r}")
    return pinned


def pin_slice(
    table: MutableMapping[str, str],
    bind: SegmentBind,
) -> str:
    """Record (slot → kind:start:end:length) at most once per distinct quadruple.

    First pin → pinned. Same quadruple again → already_pinned.
    Different kind, start, end, or length on the same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, SegmentBind):
        raise FailClosedError(f"bind must be a SegmentBind: {bind!r}")
    checked = bind_segment(
        bind.intent,
        bind.kind,
        start=bind.start,
        end=bind.end,
        length=bind.length,
        slot=bind.slot,
    )
    if (
        checked.kind != bind.kind
        or checked.span != bind.span
        or checked.start != bind.start
        or checked.end != bind.end
        or checked.length != bind.length
    ):
        raise FailClosedError(
            "SegmentBind drifted from re-bind: "
            f"have kind={bind.kind!r} span={bind.span!r} "
            f"start={bind.start!r} end={bind.end!r} "
            f"length={bind.length!r}")
    existing = peek_slice(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"slice_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: SegmentBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, SegmentBind):
        raise FailClosedError(f"bind must be a SegmentBind: {bind!r}")
    existing = peek_slice(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    kind: object,
    *,
    start: object,
    end: object,
    length: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing kind/span/slot/intent or timeout is UNKNOWN (None).

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
        or kind is None
        or start is None
        or end is None
        or length is None
        or slot is None
    ):
        return None
    # classify_* keep the fail-closed wall before bind.
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_kind(kind) == "UNKNOWN":
        return None
    if classify_span(start, end, length, timeout=False) is None:
        return None
    return pin_slice(
        table,
        bind_segment(
            intent, kind, start=start, end=end, length=length, slot=slot),
    )
