"""Classify leftover after integer division without granting a send.

byte_class (other body) owns payload length families.
stride_class / step_pin (other body) own step size.
align_class / pad_pin (other body) own pad-to-alignment.
offset_class / range_pin (other body) own interval bounds.
payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the leftover witness: exact / partial.
Missing length or stride is UNKNOWN (None), not FALSE.
A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer.

consume is a START. HALT refuses it. classify / observe
continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and byte_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

EXACT = "exact"
PARTIAL = "partial"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EXACT, PARTIAL})

CONSUME = "consume"
CLASSIFY = "classify"
OBSERVE = "observe"

INTENTS = frozenset({CONSUME, CLASSIFY, OBSERVE})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A remainder classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_consume() -> bool:
    """Structurally True. consume is a START; HALT refuses it."""
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
    """Structurally False. A recorded leftover is not an external effect."""
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


def leftover_is_zero() -> bool:
    """Structurally False. Missing leftover is UNKNOWN, not 0."""
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


def _require_stride(stride: object) -> int:
    if type(stride) is not int:
        raise FailClosedError(f"stride must be an exact int: {stride!r}")
    if stride < 1:
        raise FailClosedError(f"stride must be >= 1: {stride!r}")
    return stride


def classify_intent(value: object) -> str:
    """consume / classify / observe or UNKNOWN.

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
    stride: object,
    timeout: object = False,
) -> Optional[str]:
    """exact / partial, or None when missing or timed out.

    Missing length or stride is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. length must be exact int >= 0.
    stride must be exact int >= 1. bool is not an int here.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if length is None or stride is None:
        return None
    size = _require_length(length)
    step = _require_stride(stride)
    leftover = size % step
    if leftover == 0:
        return EXACT
    return PARTIAL


def leftover_of(
    length: object,
    *,
    stride: object,
    timeout: object = False,
) -> Optional[int]:
    """Return length % stride, or None when missing or timed out.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails closed.
    """
    if classify_family(length, stride=stride, timeout=timeout) is None:
        return None
    return _require_length(length) % _require_stride(stride)


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class RemainderBind:
    """One intent + family + leftover + length + stride + slot.

    Frozen so a later write cannot silently retcon the recorded
    leftover into send_authorized.
    """

    intent: str
    family: str
    leftover: int
    length: int
    stride: int
    slot: str


def bind_remainder(
    intent: object,
    length: object,
    *,
    stride: object,
    slot: object,
) -> RemainderBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(length, stride=stride, timeout=False)
    if family is None:
        raise FailClosedError("length or stride missing — UNKNOWN is not a bind")
    size = _require_length(length)
    step = _require_stride(stride)
    key = _require_slot(slot)
    leftover = size % step
    return RemainderBind(
        intent=klass,
        family=family,
        leftover=leftover,
        length=size,
        stride=step,
        slot=key,
    )


def try_bind(
    intent: object,
    length: object,
    *,
    stride: object,
    slot: object,
) -> Optional[RemainderBind]:
    """Missing intent, length, stride, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or length is None or stride is None or slot is None:
        return None
    return bind_remainder(intent, length, stride=stride, slot=slot)


def admit_remainder(
    intent: object,
    length: object,
    *,
    stride: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, length, or stride is UNKNOWN (None), not False.
    classify / observe continue under HALT. consume is refused
    when halted. Timeout is UNKNOWN (None) and does not prove
    a writer. A send name never reaches True — it fails closed
    at classify. halted / timeout must be exact bools.
    Partial leftover is a family, not a send, and does not invent
    False for classify / observe.
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
    family = classify_family(length, stride=stride, timeout=False)
    if family is None:
        return None
    if klass == CONSUME:
        return not halted
    return True
