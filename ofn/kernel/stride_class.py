"""Classify a walk-distance stride without granting a send.

seq.SeqCursor always advances by 1. segment_class / slice_pin
(other body) own a named [start, end) cut. byte_class /
length_pin (other body) own whole-payload length. offset_class
/ range_pin (unpublished / other body) own a linear offset+span.
scan_class / walk_pin and cursor_class / advance_pin
(unpublished / other body) are different modules and are not
recreated here.

This module is the stride witness: unit (exact 1) or skip
(exact int > 1). Missing stride is UNKNOWN (None), not FALSE.
A present-but-wrong type fails closed. Timeout is UNKNOWN and
does not prove a writer.

admit is a START. HALT refuses it. classify / observe continue
under HALT. Classification never grants a send and never
promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, receipts, and typed_event.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

UNIT = "unit"
SKIP = "skip"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({UNIT, SKIP})

ADMIT = "admit"
CLASSIFY = "classify"
OBSERVE = "observe"

INTENTS = frozenset({ADMIT, CLASSIFY, OBSERVE})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A stride classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_admit() -> bool:
    """Structurally True. admit is a START; HALT refuses it."""
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
    """Structurally False. A recorded stride is not an external effect."""
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


def replaces_seq_cursor() -> bool:
    """Structurally False. SeqCursor stays the +1 witness."""
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


def _require_stride(stride: object) -> int:
    if type(stride) is not int:
        raise FailClosedError(f"stride must be an exact int: {stride!r}")
    if stride < 1:
        raise FailClosedError(f"stride must be >= 1: {stride!r}")
    return stride


def _require_from_index(from_index: object) -> int:
    if type(from_index) is not int:
        raise FailClosedError(
            f"from_index must be an exact int: {from_index!r}")
    if from_index < 0:
        raise FailClosedError(f"from_index must be >= 0: {from_index!r}")
    return from_index


def classify_intent(value: object) -> str:
    """admit / classify / observe or UNKNOWN.

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


def classify_family(
    stride: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """unit / skip, or None when missing or timed out.

    Missing stride is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. stride must be exact int >= 1.
    bool is not an int here. 0 is not a stride.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if stride is None:
        return None
    distance = _require_stride(stride)
    if distance == 1:
        return UNIT
    return SKIP


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class StrideBind:
    """One intent + family + stride + from_index + next_index + slot.

    Frozen so a later write cannot silently retcon the recorded
    step into send_authorized.
    """

    intent: str
    family: str
    stride: int
    from_index: int
    next_index: int
    slot: str


def bind_stride(
    intent: object,
    stride: object,
    *,
    from_index: object,
    slot: object,
) -> StrideBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(stride, timeout=False)
    if family is None:
        raise FailClosedError("stride missing — UNKNOWN is not a bind")
    distance = _require_stride(stride)
    origin = _require_from_index(from_index)
    key = _require_slot(slot)
    return StrideBind(
        intent=klass,
        family=family,
        stride=distance,
        from_index=origin,
        next_index=origin + distance,
        slot=key,
    )


def try_bind(
    intent: object,
    stride: object,
    *,
    from_index: object,
    slot: object,
) -> Optional[StrideBind]:
    """Missing intent, stride, from_index, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or stride is None
        or from_index is None
        or slot is None
    ):
        return None
    return bind_stride(
        intent, stride, from_index=from_index, slot=slot)


def admit_stride(
    intent: object,
    stride: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or stride is UNKNOWN (None), not False.
    classify / observe continue under HALT. admit is refused
    when halted. Timeout is UNKNOWN (None) and does not prove
    a writer. A send name never reaches True — it fails closed
    at classify. halted / timeout must be exact bools.
    skip is a family, not a send, and does not invent False
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
    family = classify_family(stride, timeout=False)
    if family is None:
        return None
    if klass == ADMIT:
        return not halted
    return True
