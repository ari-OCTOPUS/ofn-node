"""Classify elapsed vs due_after + linger_after without granting a send.

stale_class / fresh_pin (other body) own observed-vs-expected
freshness of a value. lease_class / renew_pin (other body) own
a bound token plus an expire window. aging_class / decay_pin
(other body) own age_ticks vs a single decay_after threshold.
ttl_class / expire_pin (unpublished / other body) own
time-to-live remaining. deadline_window owns an absolute
deadline. horizon_cutoff (other body) owns a hard cut.
This module is none of those.

This module is the two-threshold linger witness: live / grace /
lapsed. After due_after the record is still live-for-linger
until due_after + linger_after, then it lapses. Missing
elapsed, due_after, or linger_after is UNKNOWN (None), not
FALSE. A present-but-wrong type fails closed. Timeout is
UNKNOWN and does not prove a writer.

linger is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, stale_class, and aging_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

LIVE = "live"
GRACE = "grace"
LAPSED = "lapsed"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({LIVE, GRACE, LAPSED})

LINGER = "linger"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({LINGER, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A grace classifier never authorizes a send. Structurally False."""
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


def halt_blocks_linger() -> bool:
    """Structurally True. linger is a START; HALT refuses it."""
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
    """Structurally False. A recorded linger is not an external effect."""
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


def elapsed_is_zero() -> bool:
    """Structurally False. Missing elapsed is UNKNOWN, not 0."""
    return False


def live_is_authorized() -> bool:
    """Structurally False. A live family is not send_authorized."""
    return False


def grace_is_send() -> bool:
    """Structurally False. Grace is a linger witness, not a send."""
    return False


def lapsed_is_false() -> bool:
    """Structurally False. Lapsed is a known family, not FALSE."""
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


def _require_elapsed(elapsed_ticks: object) -> int:
    if type(elapsed_ticks) is not int:
        raise FailClosedError(
            f"elapsed_ticks must be an exact int: {elapsed_ticks!r}")
    if elapsed_ticks < 0:
        raise FailClosedError(f"elapsed_ticks must be >= 0: {elapsed_ticks!r}")
    return elapsed_ticks


def _require_due_after(due_after: object) -> int:
    if type(due_after) is not int:
        raise FailClosedError(
            f"due_after must be an exact int: {due_after!r}")
    if due_after < 1:
        raise FailClosedError(f"due_after must be >= 1: {due_after!r}")
    return due_after


def _require_linger_after(linger_after: object) -> int:
    if type(linger_after) is not int:
        raise FailClosedError(
            f"linger_after must be an exact int: {linger_after!r}")
    if linger_after < 1:
        raise FailClosedError(f"linger_after must be >= 1: {linger_after!r}")
    return linger_after


def classify_intent(value: object) -> str:
    """linger / classify / observe / inspect or UNKNOWN.

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
    elapsed_ticks: object,
    *,
    due_after: object,
    linger_after: object,
    timeout: object = False,
) -> Optional[str]:
    """live / grace / lapsed, or None when missing or timed out.

    Missing elapsed_ticks, due_after, or linger_after is UNKNOWN
    (None), not FALSE. Timeout is UNKNOWN (None) and does not
    prove a writer. Present-but-bad still fails closed.
    elapsed_ticks must be exact int >= 0. due_after and
    linger_after must be exact int >= 1. bool is not an int here.

    live: elapsed < due_after
    grace: due_after <= elapsed < due_after + linger_after
    lapsed: elapsed >= due_after + linger_after

    This is a two-threshold linger window, not age-vs-one-threshold
    and not a lease expire window.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if elapsed_ticks is None or due_after is None or linger_after is None:
        return None
    elapsed = _require_elapsed(elapsed_ticks)
    due = _require_due_after(due_after)
    linger = _require_linger_after(linger_after)
    close = due + linger
    if elapsed < due:
        return LIVE
    if elapsed < close:
        return GRACE
    return LAPSED


def remaining_of(
    elapsed_ticks: object,
    *,
    due_after: object,
    linger_after: object,
    timeout: object = False,
) -> Optional[int]:
    """Ticks until lapse, or 0 when lapsed, or None when missing.

    None is UNKNOWN, not 0 and not FALSE. A lapsed remaining is 0,
    not a negative borrow. This remaining includes the linger
    window — it is not ticks-until-due.
    """
    family = classify_family(
        elapsed_ticks,
        due_after=due_after,
        linger_after=linger_after,
        timeout=timeout,
    )
    if family is None:
        return None
    elapsed = _require_elapsed(elapsed_ticks)
    due = _require_due_after(due_after)
    linger = _require_linger_after(linger_after)
    close = due + linger
    if elapsed >= close:
        return 0
    return close - elapsed


def until_due_of(
    elapsed_ticks: object,
    *,
    due_after: object,
    linger_after: object,
    timeout: object = False,
) -> Optional[int]:
    """Ticks until due, or 0 when grace/lapsed, or None when missing.

    None is UNKNOWN, not 0. Distinct from remaining_of (until lapse).
    """
    family = classify_family(
        elapsed_ticks,
        due_after=due_after,
        linger_after=linger_after,
        timeout=timeout,
    )
    if family is None:
        return None
    elapsed = _require_elapsed(elapsed_ticks)
    due = _require_due_after(due_after)
    if elapsed >= due:
        return 0
    return due - elapsed


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class GraceBind:
    """One intent + family + elapsed + due + linger + remaining + slot.

    Frozen so a later write cannot silently retcon the recorded
    linger into send_authorized.
    """

    intent: str
    family: str
    elapsed_ticks: int
    due_after: int
    linger_after: int
    remaining: int
    slot: str


def bind_grace(
    intent: object,
    elapsed_ticks: object,
    *,
    due_after: object,
    linger_after: object,
    slot: object,
) -> GraceBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(
        elapsed_ticks,
        due_after=due_after,
        linger_after=linger_after,
        timeout=False,
    )
    if family is None:
        raise FailClosedError(
            "elapsed, due_after, or linger_after missing — "
            "UNKNOWN is not a bind")
    elapsed = _require_elapsed(elapsed_ticks)
    due = _require_due_after(due_after)
    linger = _require_linger_after(linger_after)
    key = _require_slot(slot)
    remain = remaining_of(
        elapsed, due_after=due, linger_after=linger, timeout=False)
    if remain is None:
        raise FailClosedError("remaining missing — UNKNOWN is not a bind")
    return GraceBind(
        intent=klass,
        family=family,
        elapsed_ticks=elapsed,
        due_after=due,
        linger_after=linger,
        remaining=remain,
        slot=key,
    )


def try_bind(
    intent: object,
    elapsed_ticks: object,
    *,
    due_after: object,
    linger_after: object,
    slot: object,
) -> Optional[GraceBind]:
    """Missing intent, elapsed, due, linger, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or elapsed_ticks is None
        or due_after is None
        or linger_after is None
        or slot is None
    ):
        return None
    return bind_grace(
        intent,
        elapsed_ticks,
        due_after=due_after,
        linger_after=linger_after,
        slot=slot,
    )


def admit_grace(
    intent: object,
    elapsed_ticks: object,
    *,
    due_after: object,
    linger_after: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, elapsed, due_after, or linger_after is UNKNOWN
    (None), not False. classify / observe / inspect continue under
    HALT. linger is refused when halted. Timeout is UNKNOWN (None)
    and does not prove a writer. A send name never reaches True —
    it fails closed at classify. halted / timeout must be exact
    bools. A live or grace family is a witness, not a send, and
    does not invent False for classify / observe / inspect.
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
        elapsed_ticks,
        due_after=due_after,
        linger_after=linger_after,
        timeout=False,
    )
    if family is None:
        return None
    if klass == LINGER:
        return not halted
    return True
