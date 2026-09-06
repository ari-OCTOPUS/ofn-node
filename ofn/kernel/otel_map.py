"""Event-kind → telemetry span mapping (contract only).

A mapping is not an export. This module names spans and attributes for
the nine-kind run vocabulary; it imports no exporter, no network stack,
and no third-party SDK. Emitting a span is an adapter decision that this
file cannot make.

``send_authorized`` and ``quote_sent`` are not span names and are not in
the map. A ready campaign envelope does not become a send span.

Kernel purity: constants and lookup only.
"""

from __future__ import annotations

from typing import Mapping, Optional

from .errors import FailClosedError

# The nine-kind vocabulary (string-equal to the P1 events module). Kept
# here so this contract can land on a body that does not yet carry
# events.py; a later merge can import the names instead of restating them.
RUN_CREATED = "RUN_CREATED"
CLAIM_CREATED = "CLAIM_CREATED"
PROPOSAL_CREATED = "PROPOSAL_CREATED"
POLICY_DECISION = "POLICY_DECISION"
TOOL_INVOKED = "TOOL_INVOKED"
EXECUTION_RECEIPT = "EXECUTION_RECEIPT"
BUDGET_DEBIT = "BUDGET_DEBIT"
RUN_CLOSED = "RUN_CLOSED"
RUN_REJECTED = "RUN_REJECTED"

EVENT_KINDS = frozenset({
    RUN_CREATED, CLAIM_CREATED, PROPOSAL_CREATED, POLICY_DECISION,
    TOOL_INVOKED, EXECUTION_RECEIPT, BUDGET_DEBIT, RUN_CLOSED, RUN_REJECTED,
})

# Stable span names. Dots, not slashes; no vendor product names.
SPAN_BY_KIND: Mapping[str, str] = {
    RUN_CREATED: "run.created",
    CLAIM_CREATED: "claim.created",
    PROPOSAL_CREATED: "proposal.created",
    POLICY_DECISION: "policy.decision",
    TOOL_INVOKED: "tool.invoked",
    EXECUTION_RECEIPT: "execution.receipt",
    BUDGET_DEBIT: "budget.debit",
    RUN_CLOSED: "run.closed",
    RUN_REJECTED: "run.rejected",
}

# Attributes an exporter MAY copy. None of these is a send authorization.
ATTRIBUTE_KEYS: Mapping[str, str] = {
    "run_id": "run.id",
    "event_id": "event.id",
    "kind": "event.kind",
    "seq": "event.seq",
    "ref": "event.ref",
    "risk_tier": "run.risk_tier",
    "authority_level": "run.authority_level",
}

# States that must never appear as a span name or as an implied effect.
# Presence here is the structural pin: ready ≠ authorized.
NON_EXPORTABLE_STATES = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def span_name(kind: str) -> str:
    """Look up the span name. Unknown kinds fail closed — an unmapped
    event is not silently dropped into a generic span."""
    if kind not in SPAN_BY_KIND:
        raise FailClosedError(f"no span mapping for event kind: {kind!r}")
    return SPAN_BY_KIND[kind]


def is_exportable_state(state: str) -> bool:
    """Ready, authorized, and sent are not exportable effects.

    Returning False is the contract. This function never returns True
    for a send or ready state, and never invents a span for them.
    """
    if not isinstance(state, str) or not state.strip():
        raise FailClosedError(f"state must be a non-empty name: {state!r}")
    return False if state in NON_EXPORTABLE_STATES else state in EVENT_KINDS


def attribute_key(field: str) -> Optional[str]:
    """Translate a record field to a telemetry attribute key, or None
    if the field is not in the allow-list (unknown fields are omitted,
    not forwarded — forwarding is how PII leaks)."""
    return ATTRIBUTE_KEYS.get(field)
