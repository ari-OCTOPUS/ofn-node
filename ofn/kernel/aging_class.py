"""Classify age_ticks vs decay_after without granting a send.

stale_class / fresh_pin (other body) own observed-vs-expected
freshness of a value. lease_class / renew_pin (other body) own
a bound token plus an expire window. ttl_class / expire_pin
(unpublished / other body) own time-to-live remaining.
compact_class / retain_pin (unpublished / other body) own
retain-count vs total-count. keepalive / heartbeat (other
bodies) own idle/miss witnesses. deadline_window owns an
absolute deadline. This module is none of those.

This module is the age-threshold witness: fresh / due / decayed.
Missing age or decay_after is UNKNOWN (None), not FALSE.
A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer.

decay is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and stale_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

FRESH = "fresh"
DUE = "due"
DECAYED = "decayed"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({FRESH, DUE, DECAYED})

DECAY = "decay"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({DECAY, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An aging classifier never authorizes a send. Structurally False."""
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


def halt_blocks_decay() -> bool:
    """Structurally True. decay is a START; HALT refuses it."""
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
    """Structurally False. A recorded age is not an external effect."""
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


def age_is_zero() -> bool:
    """Structurally False. Missing age is UNKNOWN, not 0."""
    return False


def fresh_is_authorized() -> bool:
    """Structurally False. A fresh family is not send_authorized."""
    return False


def due_is_send() -> bool:
    """Structurally False. Due is a threshold witness, not a send."""
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


def _require_age(age_ticks: object) -> int:
    if type(age_ticks) is not int:
        raise FailClosedError(f"age_ticks must be an exact int: {age_ticks!r}")
    if age_ticks < 0:
        raise FailClosedError(f"age_ticks must be >= 0: {age_ticks!r}")
    return age_ticks


def _require_decay_after(decay_after: object) -> int:
    if type(decay_after) is not int:
        raise FailClosedError(
            f"decay_after must be an exact int: {decay_after!r}")
    if decay_after < 1:
        raise FailClosedError(f"decay_after must be >= 1: {decay_after!r}")
    return decay_after


def classify_intent(value: object) -> str:
    """decay / classify / observe / inspect or UNKNOWN.

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
    age_ticks: object,
    *,
    decay_after: object,
    timeout: object = False,
) -> Optional[str]:
    """fresh / due / decayed, or None when missing or timed out.

    Missing age_ticks or decay_after is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. age_ticks must be exact int >= 0.
    decay_after must be exact int >= 1. bool is not an int here.
    This is age-vs-threshold, not observed-vs-expected freshness
    and not a lease expire window.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if age_ticks is None or decay_after is None:
        return None
    age = _require_age(age_ticks)
    after = _require_decay_after(decay_after)
    if age < after:
        return FRESH
    if age == after:
        return DUE
    return DECAYED


def remaining_of(
    age_ticks: object,
    *,
    decay_after: object,
    timeout: object = False,
) -> Optional[int]:
    """Ticks until due, or 0 when due/decayed, or None when missing.

    None is UNKNOWN, not 0 and not FALSE. A decayed remaining is 0,
    not a negative borrow.
    """
    family = classify_family(
        age_ticks, decay_after=decay_after, timeout=timeout)
    if family is None:
        return None
    age = _require_age(age_ticks)
    after = _require_decay_after(decay_after)
    if age >= after:
        return 0
    return after - age


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class AgingBind:
    """One intent + family + age + decay_after + remaining + slot.

    Frozen so a later write cannot silently retcon the recorded
    age into send_authorized.
    """

    intent: str
    family: str
    age_ticks: int
    decay_after: int
    remaining: int
    slot: str


def bind_aging(
    intent: object,
    age_ticks: object,
    *,
    decay_after: object,
    slot: object,
) -> AgingBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(age_ticks, decay_after=decay_after, timeout=False)
    if family is None:
        raise FailClosedError(
            "age_ticks or decay_after missing — UNKNOWN is not a bind")
    age = _require_age(age_ticks)
    after = _require_decay_after(decay_after)
    key = _require_slot(slot)
    remain = remaining_of(age, decay_after=after, timeout=False)
    if remain is None:
        raise FailClosedError("remaining missing — UNKNOWN is not a bind")
    return AgingBind(
        intent=klass,
        family=family,
        age_ticks=age,
        decay_after=after,
        remaining=remain,
        slot=key,
    )


def try_bind(
    intent: object,
    age_ticks: object,
    *,
    decay_after: object,
    slot: object,
) -> Optional[AgingBind]:
    """Missing intent, age, decay_after, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or age_ticks is None
        or decay_after is None
        or slot is None
    ):
        return None
    return bind_aging(
        intent, age_ticks, decay_after=decay_after, slot=slot)


def admit_aging(
    intent: object,
    age_ticks: object,
    *,
    decay_after: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, age, or decay_after is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. decay is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    A fresh family is a witness, not a send, and does not invent
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
    family = classify_family(
        age_ticks, decay_after=decay_after, timeout=False)
    if family is None:
        return None
    if klass == DECAY:
        return not halted
    return True
