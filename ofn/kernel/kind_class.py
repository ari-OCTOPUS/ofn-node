"""Classify a spine kind into a closed role without granting a send.

kind_graph owns succession. events.make_event owns the factory.
typed_event owns record shape. halt_ops owns operation names.
This module is the role witness: start / inflight / close / reject
/ proposal / debit.

Missing is UNKNOWN (None), not FALSE. Classification never grants
a send and never promotes campaign_envelope_ready to authorized.

PROPOSAL_CREATED is proposal, not execution. RUN_CREATED is a
START label only — this classifier does not mint. BUDGET_DEBIT
is debit (one verdict → one budget effect), not a send.

Sealed send/ready names fail closed. Distinct from kind_graph,
typed_event, halt_ops, store_class, and envelope_class. Not
wired into run_store.py. HALT stops STARTS, not this classifier.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import (
    BUDGET_DEBIT,
    CLAIM_CREATED,
    EVENT_KINDS,
    EXECUTION_RECEIPT,
    POLICY_DECISION,
    PROPOSAL_CREATED,
    RUN_CLOSED,
    RUN_CREATED,
    RUN_REJECTED,
    TOOL_INVOKED,
    is_forbidden_effect_name,
)

START = "start"
INFLIGHT = "inflight"
CLOSE = "close"
REJECT = "reject"
PROPOSAL = "proposal"
DEBIT = "debit"

ROLES = frozenset({START, INFLIGHT, CLOSE, REJECT, PROPOSAL, DEBIT})

KIND_ROLES = {
    RUN_CREATED: START,
    CLAIM_CREATED: INFLIGHT,
    POLICY_DECISION: INFLIGHT,
    TOOL_INVOKED: INFLIGHT,
    EXECUTION_RECEIPT: INFLIGHT,
    BUDGET_DEBIT: DEBIT,
    RUN_CLOSED: CLOSE,
    RUN_REJECTED: REJECT,
    PROPOSAL_CREATED: PROPOSAL,
}

_SEND = frozenset({
    "send_authorized",
    "quote_sent",
    "send-authorized",
    "quote-sent",
})
_READY = frozenset({
    "campaign_envelope_ready",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A kind classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classifier."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A classifier is not a rename of authorized."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal role is not an execution."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classifier is not filesystem immutability."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Not wired into the run store."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This classifies."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_send_name(value: str, *, what: str) -> None:
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {s.replace("-", "_") for s in _SEND}
        or folded in {s.replace("-", "_") for s in _READY}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "a kind role is not authorized")


def classify_role(
    kind: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """Role label, or None when kind is missing or timed out.

    Missing kind is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if kind is None:
        return None
    if type(kind) is not str:
        raise FailClosedError(f"kind must be a str or None: {kind!r}")
    if not kind.strip():
        raise FailClosedError("kind is empty")
    _refuse_send_name(kind, what="kind")
    if kind not in EVENT_KINDS:
        raise FailClosedError(f"unknown spine kind: {kind!r}")
    role = KIND_ROLES.get(kind)
    if role is None or role not in ROLES:
        raise FailClosedError(f"kind has no closed role: {kind!r}")
    return role
