"""Classify head / tail / interior of a counted sequence without granting a send.

watermark_class / high_pin (other body) own newest-observed high water.
cursor_class / advance_pin (other body) own cursor vs next.
checkpoint_class / mark_pin (other body) own observed_seq vs mark_seq.
seq.py is stateful (gap == replay) and is not recreated here.
carve_class / extract_pin (other body) own cut_at + guest vs host length.
remainder_class / leftover_pin own leftover after divide.
offset_class / range_pin (other body) own interval bounds.
prefix_class / stem_pin (other body) own string prefixes.
payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the end witness: empty / single / head / tail /
interior / past. Missing length or index is UNKNOWN (None),
not FALSE. A present-but-wrong type fails closed. Timeout is
UNKNOWN and does not prove a writer.

take is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and watermark_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

EMPTY = "empty"
SINGLE = "single"
HEAD = "head"
TAIL = "tail"
INTERIOR = "interior"
PAST = "past"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EMPTY, SINGLE, HEAD, TAIL, INTERIOR, PAST})

TAKE = "take"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({TAKE, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A head classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_inspect() -> bool:
    """Structurally False. inspect continues under HALT."""
    return False


def halt_blocks_take() -> bool:
    """Structurally True. take is a START; HALT refuses it."""
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
    """Structurally False. A recorded end is not an external effect."""
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


def empty_is_zero() -> bool:
    """Structurally False. Missing length is UNKNOWN, not 0."""
    return False


def head_is_authorized() -> bool:
    """Structurally False. A head family is not send_authorized."""
    return False


def tail_is_send() -> bool:
    """Structurally False. A tail family is not a send."""
    return False


def past_is_false() -> bool:
    """Structurally False. past is a family, not FALSE."""
    return False


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


def _require_length(length: object) -> int:
    if type(length) is not int:
        raise FailClosedError(f"length must be an exact int: {length!r}")
    if length < 0:
        raise FailClosedError(f"length must be >= 0: {length!r}")
    return length


def _require_index(index: object) -> int:
    if type(index) is not int:
        raise FailClosedError(f"index must be an exact int: {index!r}")
    if index < 0:
        raise FailClosedError(f"index must be >= 0: {index!r}")
    return index


def classify_intent(value: object) -> str:
    """take / classify / observe / inspect or UNKNOWN.

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
    length: object,
    *,
    index: object,
    timeout: object = False,
) -> Optional[str]:
    """empty / single / head / tail / interior / past, or None.

    Missing length or index is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. length and index must
    be exact int >= 0. bool is not an int here.

    length == 0 and index == 0 is empty (no item). length == 0
    and index > 0 is past. length == 1 and index == 0 is single
    (one item is both ends; not head-only and not tail-only).
    index >= length (when length > 0) is past, recorded not granted.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if length is None or index is None:
        return None
    size = _require_length(length)
    pos = _require_index(index)
    if size == 0:
        if pos == 0:
            return EMPTY
        return PAST
    if pos >= size:
        return PAST
    if size == 1:
        return SINGLE
    if pos == 0:
        return HEAD
    if pos == size - 1:
        return TAIL
    return INTERIOR


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class HeadBind:
    """One intent + family + length + index + slot.

    Frozen so a later write cannot silently retcon the recorded
    end into send_authorized.
    """

    intent: str
    family: str
    length: int
    index: int
    slot: str


def bind_head(
    intent: object,
    length: object,
    *,
    index: object,
    slot: object,
) -> HeadBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(length, index=index, timeout=False)
    if family is None:
        raise FailClosedError("length or index missing — UNKNOWN is not a bind")
    size = _require_length(length)
    pos = _require_index(index)
    key = _require_slot(slot)
    return HeadBind(
        intent=klass,
        family=family,
        length=size,
        index=pos,
        slot=key,
    )


def try_bind(
    intent: object,
    length: object,
    *,
    index: object,
    slot: object,
) -> Optional[HeadBind]:
    """Missing intent, length, index, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or length is None or index is None or slot is None:
        return None
    return bind_head(intent, length, index=index, slot=slot)


def admit_head(
    intent: object,
    length: object,
    *,
    index: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, length, or index is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. take is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    past / empty / interior are families, not a send, and do
    not invent False for classify / observe / inspect.
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
    family = classify_family(length, index=index, timeout=False)
    if family is None:
        return None
    if klass == TAKE:
        return not halted
    return True
