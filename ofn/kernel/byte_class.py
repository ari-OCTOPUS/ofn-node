"""Classify a payload's byte length without granting a send.

format_class (unpublished / other body) owns identifier shape.
codec_class (other body) owns encoding. utf8_class owns text
decode. payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the length witness: empty / bounded / oversize.
Missing payload is UNKNOWN (None), not FALSE. A present-but-wrong
type fails closed. Timeout is UNKNOWN and does not prove a writer.

measure is a START. HALT refuses it. classify / observe continue
under HALT. Classification never grants a send and never promotes
campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, token_ceiling, scope_class, and window_class.

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
BOUNDED = "bounded"
OVERSIZE = "oversize"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EMPTY, BOUNDED, OVERSIZE})

MEASURE = "measure"
CLASSIFY = "classify"
OBSERVE = "observe"

INTENTS = frozenset({MEASURE, CLASSIFY, OBSERVE})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A byte classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_measure() -> bool:
    """Structurally True. measure is a START; HALT refuses it."""
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
    """Structurally False. A recorded length is not an external effect."""
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


def _require_bound(bound: object) -> int:
    if type(bound) is not int:
        raise FailClosedError(f"bound must be an exact int: {bound!r}")
    if bound < 0:
        raise FailClosedError(f"bound must be >= 0: {bound!r}")
    return bound


def classify_intent(value: object) -> str:
    """measure / classify / observe or UNKNOWN.

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
    payload: object,
    *,
    bound: object,
    timeout: object = False,
) -> Optional[str]:
    """empty / bounded / oversize, or None when missing or timed out.

    Missing payload is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. bound must be exact int >= 0.
    bool is not an int here. str is not bytes — that is a decode lane.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    ceiling = _require_bound(bound)
    if payload is None:
        return None
    if type(payload) is not bytes:
        raise FailClosedError(
            f"payload must be bytes or None: {type(payload).__name__}")
    size = len(payload)
    if size == 0:
        return EMPTY
    if size <= ceiling:
        return BOUNDED
    return OVERSIZE


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class ByteBind:
    """One intent + family + size + bound + slot.

    Frozen so a later write cannot silently retcon the recorded
    length into send_authorized.
    """

    intent: str
    family: str
    size: int
    bound: int
    slot: str


def bind_bytes(
    intent: object,
    payload: object,
    *,
    bound: object,
    slot: object,
) -> ByteBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(payload, bound=bound, timeout=False)
    if family is None:
        raise FailClosedError("payload missing — UNKNOWN is not a bind")
    if type(payload) is not bytes:
        raise FailClosedError(f"payload must be bytes: {payload!r}")
    ceiling = _require_bound(bound)
    key = _require_slot(slot)
    return ByteBind(
        intent=klass,
        family=family,
        size=len(payload),
        bound=ceiling,
        slot=key,
    )


def try_bind(
    intent: object,
    payload: object,
    *,
    bound: object,
    slot: object,
) -> Optional[ByteBind]:
    """Missing intent, payload, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or payload is None or slot is None:
        return None
    return bind_bytes(intent, payload, bound=bound, slot=slot)


def admit_bytes(
    intent: object,
    payload: object,
    *,
    bound: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or payload is UNKNOWN (None), not False.
    classify / observe continue under HALT. measure is refused
    when halted. Timeout is UNKNOWN (None) and does not prove
    a writer. A send name never reaches True — it fails closed
    at classify. halted / timeout must be exact bools.
    Oversize is a family, not a send, and does not invent False
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
    family = classify_family(payload, bound=bound, timeout=False)
    if family is None:
        return None
    if klass == MEASURE:
        return not halted
    return True
