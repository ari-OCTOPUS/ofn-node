"""Claim-type class — OBSERVATION, INFERENCE, or UNKNOWN.

An observation requires a non-empty evidence list and may not rest
on agent_reported or timeout alone. Missing evidence is UNKNOWN,
not FALSE. Agent-reported is not independently verified: that
input classifies as INFERENCE, never OBSERVATION.

campaign_envelope_ready, send_authorized, and quote_sent are sealed
names, not claim types. Classification never grants a send.

Not wired into run_store.py. Distinct from report mint/verify
(another open change). HALT stops STARTS, not classification.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

OBSERVATION = "OBSERVATION"
INFERENCE = "INFERENCE"
UNKNOWN = "UNKNOWN"

_CLAIM_TYPES = frozenset({OBSERVATION, INFERENCE, UNKNOWN})
_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})
_AGENT_REPORTED = frozenset({"agent_reported", "agent_report_only"})
_TIMEOUT = frozenset({"timeout", "timeout_unknown"})


def grants_send() -> bool:
    """A claim-type class never authorizes a send. Structurally False."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def agent_reported_is_verified() -> bool:
    """Structurally False. Agent-reported is not independently verified."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Classification is not filesystem immutability."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def _refuse_sealed(value: object) -> None:
    if not isinstance(value, str):
        return
    folded = value.strip().lower().replace("-", "_")
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in _SEALED
    ):
        raise FailClosedError(
            f"claim names a sealed send/ready state: {value!r}")


def _evidence_tags(evidence: object) -> Optional[tuple]:
    """None evidence is UNKNOWN (caller handles). Empty is empty.
    Non-iterable / bool fail closed. Sealed tags refuse.
    """
    if evidence is None:
        return None
    if type(evidence) is bool or isinstance(evidence, (str, bytes)):
        raise FailClosedError(f"evidence must be a sequence: {evidence!r}")
    if not isinstance(evidence, (list, tuple)):
        raise FailClosedError(f"evidence must be a sequence: {evidence!r}")
    tags = []
    for item in evidence:
        _refuse_sealed(item)
        if not isinstance(item, str) or not item.strip():
            raise FailClosedError(f"evidence tag must be a non-empty str: {item!r}")
        tags.append(item.strip().lower().replace("-", "_"))
    return tuple(tags)


def classify_claim(claim_type: object, evidence: object = None) -> str:
    """Classify one supplied claim.

    None claim_type → UNKNOWN. None evidence with a named type is
    UNKNOWN (no witness), not FALSE. Timeout in evidence → UNKNOWN.
    Agent-reported evidence cannot produce OBSERVATION. An explicit
    OBSERVATION with empty evidence fails closed (observation
    requires a witness — that is a shape error, not a missing one).
    """
    if claim_type is None and evidence is None:
        return UNKNOWN
    if claim_type is None:
        return UNKNOWN
    if type(claim_type) is not str:
        raise FailClosedError(f"claim_type must be a str or None: {claim_type!r}")
    _refuse_sealed(claim_type)
    folded = claim_type.strip().upper().replace("-", "_")
    if not folded:
        raise FailClosedError("claim_type is empty")
    if folded not in _CLAIM_TYPES:
        raise FailClosedError(f"unknown claim_type: {claim_type!r}")

    tags = _evidence_tags(evidence)
    if tags is None:
        return UNKNOWN
    if any(t in _TIMEOUT for t in tags):
        return UNKNOWN
    if folded == OBSERVATION:
        if not tags:
            raise FailClosedError(
                "OBSERVATION requires evidence — empty is not a witness")
        if any(t in _AGENT_REPORTED for t in tags):
            raise FailClosedError(
                "agent_reported cannot produce OBSERVATION")
        return OBSERVATION
    if folded == INFERENCE:
        return INFERENCE
    return UNKNOWN


def as_bool(classified: object) -> bool:
    """Refuse UNKNOWN as a boolean. True only for OBSERVATION.

    INFERENCE is not False — it is not a negative witness. Callers
    that need the three-way answer use classify_claim.
    """
    if classified == UNKNOWN:
        raise FailClosedError("UNKNOWN is not FALSE and not a bool")
    if classified == OBSERVATION:
        return True
    if classified == INFERENCE:
        raise FailClosedError(
            "INFERENCE is not independently verified — not a bool")
    raise FailClosedError(f"unclassified value is not a bool: {classified!r}")
