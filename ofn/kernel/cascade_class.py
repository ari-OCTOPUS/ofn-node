"""Classify halt-propagation scope without granting a send.

halt.py answers "is the switch on?". halt_ops answers which
operations may proceed. halt_latch answers assert versus clear.
This module is the propagation witness: a declared scope plus a
child count. ISOLATED means the halt stays on this node.
CASCADE means it may fan out to bound children.

Children do not promote. An isolated declaration with children
present stays isolated. A cascade declaration with zero children
cannot fan out and classifies as isolated. Missing either side
is UNKNOWN (None), not FALSE. A present-but-wrong type fails
closed. Timeout is UNKNOWN and does not prove a writer.

record is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a stop.
Not wired into run_store.py. Distinct from halt.py, halt_ops,
halt_latch, quorum_class, later_hold, and scoped_authz.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

ISOLATED = "isolated"
CASCADE = "cascade"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({ISOLATED, CASCADE})

RECORD = "record"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({RECORD, CLASSIFY, OBSERVE, INSPECT})

SCOPES = frozenset({ISOLATED, CASCADE})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A cascade classifier never authorizes a send. Structurally False."""
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


def halt_blocks_record() -> bool:
    """Structurally True. record is a START; HALT refuses it."""
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
    """Structurally False. A recorded scope is not an external effect."""
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


def cascade_is_authorized() -> bool:
    """Structurally False. cascade is a family, not send_authorized."""
    return False


def isolated_is_false() -> bool:
    """Structurally False. isolated is a family, not FALSE."""
    return False


def children_do_not_promote() -> bool:
    """Structurally True. Children cannot retcon isolated into cascade."""
    return True


def zero_children_cannot_cascade() -> bool:
    """Structurally True. Cascade with zero children cannot fan out."""
    return True


def rearms_send() -> bool:
    """Structurally False. A classify never re-arms a send."""
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


def _require_scope(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"scope must be a str: {value!r}")
    _refuse_sealed(value, what="scope")
    text = value.strip()
    if not text:
        raise FailClosedError("scope is empty")
    folded = _fold(text)
    if folded not in SCOPES:
        raise FailClosedError(
            f"unknown scope is not a refusal and not a grant: {value!r}")
    return folded


def _require_child_count(value: object) -> int:
    if type(value) is not int:
        raise FailClosedError(
            f"child_count must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(f"child_count must be >= 0: {value!r}")
    return value


def classify_intent(value: object) -> str:
    """record / classify / observe / inspect or UNKNOWN.

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


def classify_propagation(
    scope: object,
    child_count: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """isolated / cascade, or None when missing or timed out.

    Missing scope or child_count is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. scope must be isolated
    or cascade. child_count must be exact int >= 0. bool is not
    an int here.

    Isolated stays isolated even when children exist. Cascade
    with zero children cannot fan out and classifies isolated.
    This is a propagation witness, not is_halted and not which
    operation may proceed.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if scope is None or child_count is None:
        return None
    declared = _require_scope(scope)
    children = _require_child_count(child_count)
    if declared == ISOLATED:
        return ISOLATED
    if children >= 1:
        return CASCADE
    return ISOLATED


def _require_stop(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"stop must be a str: {value!r}")
    _refuse_sealed(value, what="stop")
    text = value.strip()
    if not text:
        raise FailClosedError("stop is empty")
    return text


@dataclass(frozen=True)
class CascadeBind:
    """One intent + family + declared scope + child_count + stop.

    Frozen so a later write cannot silently retcon isolated into
    cascade or a recorded scope into send_authorized.
    """

    intent: str
    family: str
    scope: str
    child_count: int
    stop: str


def bind_cascade(
    intent: object,
    scope: object,
    child_count: object,
    *,
    stop: object,
) -> CascadeBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_propagation(scope, child_count, timeout=False)
    if family is None:
        raise FailClosedError(
            "scope or child_count missing — UNKNOWN is not a bind")
    declared = _require_scope(scope)
    children = _require_child_count(child_count)
    key = _require_stop(stop)
    return CascadeBind(
        intent=klass,
        family=family,
        scope=declared,
        child_count=children,
        stop=key,
    )


def try_bind(
    intent: object,
    scope: object,
    child_count: object,
    *,
    stop: object,
) -> Optional[CascadeBind]:
    """Missing intent, scope, child_count, or stop is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or scope is None
        or child_count is None
        or stop is None
    ):
        return None
    return bind_cascade(intent, scope, child_count, stop=stop)


def admit_cascade(
    intent: object,
    scope: object,
    child_count: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, scope, or child_count is UNKNOWN (None), not
    False. classify / observe / inspect continue under HALT.
    record is refused when halted. Timeout is UNKNOWN (None) and
    does not prove a writer. A send name never reaches True — it
    fails closed at classify. halted / timeout must be exact
    bools. Cascade family is a family, not a send, and does not
    invent False for classify / observe / inspect.
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
    family = classify_propagation(scope, child_count, timeout=False)
    if family is None:
        return None
    if klass == RECORD:
        return not halted
    return True
