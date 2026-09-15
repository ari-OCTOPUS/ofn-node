"""Classify a caller-supplied action as an inspect / classify / start.

This is a classification, not campaign_bind, not send_fence, and
not later_hold / scoped_authz. It does not mint a run_id, does
not write a ledger, and does not admit a send.

inspect / classify / start are the only actions. Missing is
UNKNOWN (None), not FALSE. A present-but-wrong type fails
closed. Sealed send/ready names are never an action and
never a run_id.

campaign_envelope_ready is structurally distinct from
send_authorized. Classification never grants a send and
never promotes ready to authorized.

Not wired into run_store.py. HALT stops STARTS, not a
classify. admit_scope refuses start when halted; inspect
and classify continue.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import RUN_ID_RE, is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

INSPECT = "inspect"
CLASSIFY = "classify"
START = "start"
UNKNOWN = "UNKNOWN"

ACTIONS = frozenset({INSPECT, CLASSIFY, START})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A scope classify never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_inspect() -> bool:
    """Structurally False. inspect continues under HALT."""
    return False


def halt_blocks_start() -> bool:
    """Structurally True. start is a START; HALT refuses it."""
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
    """Structurally False. A recorded pair is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
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


def classify_action(value: object) -> str:
    """inspect / classify / start or UNKNOWN.

    None → UNKNOWN (no witness). bool/int/float/bytes fail closed.
    Empty / unknown / sealed names fail closed. UNKNOWN is not FALSE.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"action must be a str or None: {value!r}")
    _refuse_sealed(value, what="action")
    text = value.strip()
    if not text:
        raise FailClosedError("action is empty")
    folded = _fold(text)
    if folded in ACTIONS:
        return folded
    raise FailClosedError(
        f"unknown action is not a refusal and not a grant: {value!r}")


def _require_run_id(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"run_id must be a str: {value!r}")
    _refuse_sealed(value, what="run_id")
    text = value.strip()
    if not text:
        raise FailClosedError("run_id is empty")
    if RUN_ID_RE.match(text) is None:
        raise FailClosedError(f"run_id is malformed: {value!r}")
    return text


@dataclass(frozen=True)
class ScopeBind:
    """One action + run_id pair. Frozen so a later write cannot
    silently retcon the recorded action into send_authorized.
    """

    action: str
    run_id: str
    action_class: str


def bind_scope(action: object, run_id: object) -> ScopeBind:
    """Require both sides. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_action(action)
    if klass == UNKNOWN:
        raise FailClosedError("action missing — UNKNOWN is not a bind")
    rid = _require_run_id(run_id)
    if type(action) is not str:
        raise FailClosedError(f"action must be a str: {action!r}")
    return ScopeBind(action=klass, run_id=rid, action_class=klass)


def try_bind(action: object, run_id: object) -> Optional[ScopeBind]:
    """Missing either side is UNKNOWN (None). Malformed fails closed.

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default action.
    """
    if action is None or run_id is None:
        return None
    return bind_scope(action, run_id)


def admit_scope(action: object, *, halted: bool = False) -> Optional[bool]:
    """True when the action may proceed.

    Missing is UNKNOWN (None), not False. inspect / classify
    continue under HALT. start is refused when halted. A send
    name never reaches True — it fails closed at classify.
    halted must be an exact bool; a missing/unknown halt is
    not treated as running.
    """
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    klass = classify_action(action)
    if klass == UNKNOWN:
        return None
    if klass == START:
        return not halted
    return True


def pair_matches(
    action: object,
    run_id: object,
    expected_action: object,
) -> Optional[bool]:
    """True when the bound action equals the expected action.

    Missing either bind side is UNKNOWN (None), not False.
    A bind that exists but names a different action is False —
    that is a measured disagreement, not a missing witness.
    Missing expected_action is UNKNOWN (None).
    """
    bound = try_bind(action, run_id)
    if bound is None:
        return None
    expected = classify_action(expected_action)
    if expected == UNKNOWN:
        return None
    return bound.action == expected
