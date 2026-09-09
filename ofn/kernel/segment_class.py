"""Classify a payload segment without granting a send.

byte_class (other body / #200) owns whole-payload length.
offset_class / range_pin (unpublished / other body) own a
linear offset+span. overlap_class / collide_pin (unpublished
/ other body) own interval collision. payload_bound
(unpublished / other body) is a different module and is not
recreated here. split_view (other body) owns view splitting.
window_class owns time windows.

This module is the segment witness: a named kind
(header / body / trailer) plus a half-open [start, end)
against an exact int length. The span family is
fit / empty / overflow. Missing start/end/length is
UNKNOWN (None), not FALSE. A present-but-wrong type
fails closed. Timeout is UNKNOWN and does not prove a writer.

cut is a START. HALT refuses it. classify / observe continue
under HALT. Classification never grants a send and never
promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent, never a kind,
and never a slot. Not wired into run_store.py. Distinct from
envelope_class, store_class, receipts, and typed_event.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

HEADER = "header"
BODY = "body"
TRAILER = "trailer"

KINDS = frozenset({HEADER, BODY, TRAILER})

FIT = "fit"
EMPTY = "empty"
OVERFLOW = "overflow"

SPANS = frozenset({FIT, EMPTY, OVERFLOW})

CUT = "cut"
CLASSIFY = "classify"
OBSERVE = "observe"

INTENTS = frozenset({CUT, CLASSIFY, OBSERVE})

UNKNOWN = "UNKNOWN"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A segment classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_cut() -> bool:
    """Structurally True. cut is a START; HALT refuses it."""
    return True


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classify is not filesystem immutability."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A recorded segment is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This classifies."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return UNKNOWN


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {_fold(s) for s in _SEALED}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "ready is not authorized")


def _require_offset(value: object, *, what: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{what} must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(f"{what} must be >= 0: {value!r}")
    return value


def classify_intent(value: object) -> str:
    """cut / classify / observe or UNKNOWN.

    None → UNKNOWN (no witness). bool/int/float/bytes fail closed.
    Empty / unknown / sealed names fail closed. UNKNOWN is not FALSE.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"intent must be a str or None: {value!r}")
    _refuse_sealed(value, what="intent")
    text = value.strip()
    if not text:
        raise FailClosedError("intent is empty")
    folded = _fold(text)
    if folded in INTENTS:
        return folded
    raise FailClosedError(
        f"unknown intent is not a refusal and not a grant: {value!r}")


def classify_kind(value: object) -> str:
    """header / body / trailer or UNKNOWN.

    None → UNKNOWN (no witness). bool/int/float fail closed.
    Empty / unknown / sealed names fail closed. UNKNOWN is not FALSE.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"kind must be a str or None: {value!r}")
    _refuse_sealed(value, what="kind")
    text = value.strip()
    if not text:
        raise FailClosedError("kind is empty")
    folded = _fold(text)
    if folded in KINDS:
        return folded
    raise FailClosedError(
        f"unknown kind is not a refusal and not a grant: {value!r}")


def classify_span(
    start: object,
    end: object,
    length: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """fit / empty / overflow, or None when missing or timed out.

    Missing start, end, or length is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Offsets must be exact
    int >= 0. bool is not an int here. start > end is a shape
    error, not a family.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if start is None or end is None or length is None:
        return None
    left = _require_offset(start, what="start")
    right = _require_offset(end, what="end")
    total = _require_offset(length, what="length")
    if left > right:
        raise FailClosedError(
            f"start must be <= end: start={left!r} end={right!r}")
    if right > total or left > total:
        return OVERFLOW
    if left == right:
        return EMPTY
    return FIT


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class SegmentBind:
    """One intent + kind + span + [start, end) + length + slot.

    Frozen so a later write cannot silently retcon the recorded
    segment into send_authorized.
    """

    intent: str
    kind: str
    span: str
    start: int
    end: int
    length: int
    slot: str


def bind_segment(
    intent: object,
    kind: object,
    *,
    start: object,
    end: object,
    length: object,
    slot: object,
) -> SegmentBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    named = classify_kind(kind)
    if named == UNKNOWN:
        raise FailClosedError("kind missing — UNKNOWN is not a bind")
    span = classify_span(start, end, length, timeout=False)
    if span is None:
        raise FailClosedError(
            "start/end/length missing — UNKNOWN is not a bind")
    left = _require_offset(start, what="start")
    right = _require_offset(end, what="end")
    total = _require_offset(length, what="length")
    key = _require_slot(slot)
    return SegmentBind(
        intent=klass,
        kind=named,
        span=span,
        start=left,
        end=right,
        length=total,
        slot=key,
    )


def try_bind(
    intent: object,
    kind: object,
    *,
    start: object,
    end: object,
    length: object,
    slot: object,
) -> Optional[SegmentBind]:
    """Missing intent, kind, span side, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default kind.
    """
    if (
        intent is None
        or kind is None
        or start is None
        or end is None
        or length is None
        or slot is None
    ):
        return None
    return bind_segment(
        intent, kind, start=start, end=end, length=length, slot=slot)


def admit_segment(
    intent: object,
    kind: object,
    *,
    start: object,
    end: object,
    length: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, kind, or span is UNKNOWN (None), not False.
    classify / observe continue under HALT. cut is refused
    when halted. Timeout is UNKNOWN (None) and does not prove
    a writer. A send name never reaches True — it fails closed
    at classify. halted / timeout must be exact bools.
    Overflow is a family, not a send, and does not invent False
    for classify / observe.
    """
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timeout) is not bool:
        raise FailClosedError(f"timeout must be an exact bool: {timeout!r}")
    if timeout:
        return None
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        return None
    named = classify_kind(kind)
    if named == UNKNOWN:
        return None
    span = classify_span(start, end, length, timeout=False)
    if span is None:
        return None
    if klass == CUT:
        return not halted
    return True
