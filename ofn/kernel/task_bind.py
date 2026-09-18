"""Bind a supplied TaskEnvelope intent to a run_id shape.

This is a bind, not the factory in envelope.py and not
envelope_class.admit_envelope. It does not mint a run_id,
does not write a ledger, and does not admit a mint.

mint / validate / replay are the only intents. Missing is
UNKNOWN (None), not FALSE. A present-but-wrong type fails
closed. Sealed send/ready names are never an intent and
never a run_id.

campaign_envelope_ready is structurally distinct from
send_authorized. Classification never grants a send and
never promotes ready to authorized.

Not wired into run_store.py. HALT stops STARTS, not a bind.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import RUN_ID_RE, is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

MINT = "mint"
VALIDATE = "validate"
REPLAY = "replay"
UNKNOWN = "UNKNOWN"

INTENTS = frozenset({MINT, VALIDATE, REPLAY})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A task bind never authorizes a send. Structurally False."""
    return False


def halt_blocks_bind() -> bool:
    """Structurally False. HALT stops STARTS, not this bind."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This binds."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A bind is not filesystem immutability."""
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


def classify_intent(value: object) -> str:
    """mint / validate / replay or UNKNOWN.

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
    raise FailClosedError(f"unknown intent is not a refusal and not a grant: {value!r}")


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
class TaskBind:
    """One intent + run_id pair. Frozen so a later write cannot
    silently retcon the recorded intent into send_authorized.
    """

    intent: str
    run_id: str
    intent_class: str


def bind_task(intent: object, run_id: object) -> TaskBind:
    """Require both sides. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    rid = _require_run_id(run_id)
    if type(intent) is not str:
        raise FailClosedError(f"intent must be a str: {intent!r}")
    return TaskBind(intent=klass, run_id=rid, intent_class=klass)


def try_bind(intent: object, run_id: object) -> Optional[TaskBind]:
    """Missing either side is UNKNOWN (None). Malformed fails closed.

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default intent.
    """
    if intent is None or run_id is None:
        return None
    return bind_task(intent, run_id)


def pair_matches(
    intent: object,
    run_id: object,
    expected_intent: object,
) -> Optional[bool]:
    """True when the bound intent equals the expected intent.

    Missing either bind side is UNKNOWN (None), not False.
    A bind that exists but names a different intent is False —
    that is a measured disagreement, not a missing witness.
    Missing expected_intent is UNKNOWN (None).
    """
    bound = try_bind(intent, run_id)
    if bound is None:
        return None
    expected = classify_intent(expected_intent)
    if expected == UNKNOWN:
        return None
    return bound.intent == expected
