"""Classify queue depth against a shed threshold without granting a send.

capacity_class / room_pin (other body, #209) own occupancy vs a hard
limit (empty / has_room / full / over_cap). overflow_class / carry_pin
(other body, #205) own used+add vs capacity. remainder_class /
leftover_pin (#204) own leftover after integer division. rate_class /
throttle_pin (unpublished / other body) own events-per-window.
cascade_class / stop_pin (#219) own downstream halt. watermark (other
body) is a different module and is not recreated here.

This module is the backlog witness: below / at / over a declared
shed threshold. Missing depth or threshold is UNKNOWN (None), not
FALSE. A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer.

shed is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send and never
promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and capacity_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

BELOW = "below"
AT = "at"
OVER = "over"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({BELOW, AT, OVER})

SHED = "shed"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({SHED, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A backlog classifier never authorizes a send. Structurally False."""
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


def halt_blocks_shed() -> bool:
    """Structurally True. shed is a START; HALT refuses it."""
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
    """Structurally False. A recorded backlog is not an external effect."""
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


def room_is_zero() -> bool:
    """Structurally False. Missing room is UNKNOWN, not 0."""
    return False


def over_is_negative() -> bool:
    """Structurally False. Over-threshold room is UNKNOWN, not a negative."""
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


def _require_depth(depth: object) -> int:
    if type(depth) is not int:
        raise FailClosedError(f"depth must be an exact int: {depth!r}")
    if depth < 0:
        raise FailClosedError(f"depth must be >= 0: {depth!r}")
    return depth


def _require_threshold(threshold: object) -> int:
    if type(threshold) is not int:
        raise FailClosedError(f"threshold must be an exact int: {threshold!r}")
    if threshold < 1:
        raise FailClosedError(f"threshold must be >= 1: {threshold!r}")
    return threshold


def classify_intent(value: object) -> str:
    """shed / classify / observe / inspect or UNKNOWN.

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
    depth: object,
    *,
    threshold: object,
    timeout: object = False,
) -> Optional[str]:
    """below / at / over, or None when missing or timed out.

    Missing depth or threshold is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. depth must be exact int >= 0.
    threshold must be exact int >= 1. bool is not an int here.
    This is occupancy vs a shed line, not used+add overflow and not
    leftover-after-divide.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if depth is None or threshold is None:
        return None
    queued = _require_depth(depth)
    line = _require_threshold(threshold)
    if queued < line:
        return BELOW
    if queued == line:
        return AT
    return OVER


def room_to_shed(
    depth: object,
    *,
    threshold: object,
    timeout: object = False,
) -> Optional[int]:
    """Return threshold - depth when below or at, else None.

    Over-threshold remaining room is UNKNOWN (None), not a negative
    borrow. None is UNKNOWN, not 0 and not FALSE. Present-but-bad
    fails closed.
    """
    family = classify_family(depth, threshold=threshold, timeout=timeout)
    if family is None:
        return None
    if family == OVER:
        return None
    return _require_threshold(threshold) - _require_depth(depth)


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class BacklogBind:
    """One intent + family + depth + threshold + slot.

    Frozen so a later write cannot silently retcon the recorded
    backlog into send_authorized.
    """

    intent: str
    family: str
    depth: int
    threshold: int
    slot: str


def bind_backlog(
    intent: object,
    depth: object,
    *,
    threshold: object,
    slot: object,
) -> BacklogBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(depth, threshold=threshold, timeout=False)
    if family is None:
        raise FailClosedError(
            "depth or threshold missing — UNKNOWN is not a bind")
    queued = _require_depth(depth)
    line = _require_threshold(threshold)
    key = _require_slot(slot)
    return BacklogBind(
        intent=klass,
        family=family,
        depth=queued,
        threshold=line,
        slot=key,
    )


def try_bind(
    intent: object,
    depth: object,
    *,
    threshold: object,
    slot: object,
) -> Optional[BacklogBind]:
    """Missing intent, depth, threshold, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or depth is None or threshold is None or slot is None:
        return None
    return bind_backlog(intent, depth, threshold=threshold, slot=slot)


def admit_backlog(
    intent: object,
    depth: object,
    *,
    threshold: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, depth, or threshold is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. shed is refused
    when halted. Timeout is UNKNOWN (None) and does not prove
    a writer. A send name never reaches True — it fails closed
    at classify. halted / timeout must be exact bools.
    Over-threshold is a family, not a send, and does not invent
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
    family = classify_family(depth, threshold=threshold, timeout=False)
    if family is None:
        return None
    if klass == SHED:
        return not halted
    return True
