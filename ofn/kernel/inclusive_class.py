"""Classify one bound's inclusion without granting a send.

above/below (#231) owns a one-plane compare with no inclusion
kind. inside/outside (other body) owns two bounds. offset/range
(other body) owns interval values. deadline_window owns time.
hysteresis_class owns a two-threshold band. sign/magnitude
(other body) owns polarity of one signed int.

This module is the inclusion witness: inclusive / exclusive
on one exact-int bound. Missing value, bound, or kind is
UNKNOWN (None), not FALSE. A measured 0 is ON or OUT, never
UNKNOWN. A present-but-wrong type fails closed. Timeout is
UNKNOWN and does not prove a writer.

sample is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a
send and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and above/below.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

INCLUSIVE = "inclusive"
EXCLUSIVE = "exclusive"
UNKNOWN = "UNKNOWN"

KINDS = frozenset({INCLUSIVE, EXCLUSIVE})

BELOW = "below"
ON = "on"
ABOVE = "above"
OUT = "out"

FAMILIES = frozenset({BELOW, ON, ABOVE, OUT})

SAMPLE = "sample"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({SAMPLE, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An inclusion classifier never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. An inclusion class does not re-arm outbound."""
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


def halt_blocks_sample() -> bool:
    """Structurally True. sample is a START; HALT refuses it."""
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
    """Structurally False. A recorded inclusion is not an external effect."""
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


def measured_zero_is_unknown() -> bool:
    """Structurally False. A measured 0 is ON or OUT, never UNKNOWN."""
    return False


def exclusive_on_bound_is_on() -> bool:
    """Structurally False. Exclusive + equal is OUT, not ON."""
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


def _require_int(value: object, *, what: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{what} must be an exact int: {value!r}")
    return value


def classify_intent(value: object) -> str:
    """sample / classify / observe / inspect or UNKNOWN.

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
    """inclusive / exclusive or UNKNOWN.

    None → UNKNOWN (no witness). bool/int/float/bytes fail closed.
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


def classify_family(
    value: object,
    *,
    bound: object,
    kind: object,
    timeout: object = False,
) -> Optional[str]:
    """below / on / above / out, or None when missing or timed out.

    Missing value, bound, or kind is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. value and bound must be
    exact ints (bool is not an int here). A measured 0 is a
    family, never UNKNOWN. Exclusive + equal is OUT, not ON.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if value is None or bound is None or kind is None:
        return None
    klass = classify_kind(kind)
    if klass == UNKNOWN:
        return None
    measured = _require_int(value, what="value")
    edge = _require_int(bound, what="bound")
    if measured < edge:
        return BELOW
    if measured > edge:
        return ABOVE
    if klass == INCLUSIVE:
        return ON
    return OUT


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class InclusiveBind:
    """One intent + kind + family + value + bound + slot.

    Frozen so a later write cannot silently retcon the recorded
    inclusion into send_authorized.
    """

    intent: str
    kind: str
    family: str
    value: int
    bound: int
    slot: str


def bind_inclusive(
    intent: object,
    value: object,
    *,
    bound: object,
    kind: object,
    slot: object,
) -> InclusiveBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    inclusion = classify_kind(kind)
    if inclusion == UNKNOWN:
        raise FailClosedError("kind missing — UNKNOWN is not a bind")
    family = classify_family(value, bound=bound, kind=kind, timeout=False)
    if family is None:
        raise FailClosedError("value or bound missing — UNKNOWN is not a bind")
    measured = _require_int(value, what="value")
    edge = _require_int(bound, what="bound")
    key = _require_slot(slot)
    return InclusiveBind(
        intent=klass,
        kind=inclusion,
        family=family,
        value=measured,
        bound=edge,
        slot=key,
    )


def try_bind(
    intent: object,
    value: object,
    *,
    bound: object,
    kind: object,
    slot: object,
) -> Optional[InclusiveBind]:
    """Missing intent, value, bound, kind, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or value is None
        or bound is None
        or kind is None
        or slot is None
    ):
        return None
    return bind_inclusive(
        intent, value, bound=bound, kind=kind, slot=slot)


def admit_inclusive(
    intent: object,
    value: object,
    *,
    bound: object,
    kind: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, value, bound, or kind is UNKNOWN (None), not
    False. classify / observe / inspect continue under HALT.
    sample is refused when halted. Timeout is UNKNOWN (None) and
    does not prove a writer. A send name never reaches True — it
    fails closed at classify. halted / timeout must be exact bools.
    Exclusive OUT is a family, not a send, and does not invent
    False for classify / observe / inspect.
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
    family = classify_family(value, bound=bound, kind=kind, timeout=False)
    if family is None:
        return None
    if klass == SAMPLE:
        return not halted
    return True
