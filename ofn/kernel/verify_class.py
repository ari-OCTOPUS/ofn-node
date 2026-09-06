"""Verify class — independent verification requires a second witness.

A report cannot verify itself. An agent report cannot be the
witness for another report. A timeout is UNKNOWN, not a
verification and not proof of concurrent writing. A proposal note
is not execution.

``verified=True`` only when the witness kind is in the closed
direct-witness vocabulary and the witness id is distinct from the
reporter. Even then this module does not grant a send.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused.

HALT stops STARTS. This classifier has no halt parameter: an
in-flight report must still be verifiable so recovery does not
need the owner.

Not wired into the run store (that file is owned by another
change).

A verification is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name, payload_forbidden_effect
from .report_class import ReportDecision

# Closed witness vocabulary. Widen only with a test.
WITNESS_KINDS = frozenset({
    "direct_observation",
    "artifact_ref",
})

# Known refused witness kinds. These are a refusal, not an unknown.
REFUSED_WITNESS = frozenset({
    "agent_report",
    "measurement_note",
    "proposal_note",
    "timeout",
})

# Known refusals. Unknown names fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({
    "self_verify",
    "not_independent",
    "timeout_unknown",
    "proposal_is_not_execution",
    "report_not_admitted",
    "sealed_effect",
    "smuggled_effect",
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A verification never authorizes a send. Structurally False."""
    return False


def halt_blocks_verify() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A verification is not chattr +i."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. A timeout is not a second writer."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal_note is not an execution."""
    return False


def report_is_verification() -> bool:
    """Structurally False. Agent-reported is not independently verified."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


@dataclass(frozen=True)
class VerifyDecision:
    """The independent-verification verdict.

    ``verified`` and ``independently_verified`` must agree.
    ``grants_send`` is structurally False — a second witness is
    not a send authorization.
    """

    verified: bool
    reason: Optional[str]
    witness_kind: str
    witness_id: str
    independently_verified: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "VerifyDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a verification is not a send")
        if self.verified != self.independently_verified:
            raise FailClosedError(
                "verified and independently_verified must agree — "
                "a silent split is a defect")
        if self.verified:
            if self.reason is not None:
                raise FailClosedError(
                    f"verified decision must not carry a reason: {self.reason!r}")
            if self.witness_kind not in WITNESS_KINDS:
                raise FailClosedError(
                    f"verified witness kind is not direct: {self.witness_kind!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        object.__setattr__(
            self, "witness_kind", _require_name(self.witness_kind, what="witness_kind"))
        object.__setattr__(
            self, "witness_id", _require_name(self.witness_id, what="witness_id"))
        if _is_sealed(self.witness_kind) or _is_sealed(self.witness_id):
            if self.verified or self.reason != "sealed_effect":
                raise FailClosedError(
                    "VerifyDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def verify_report(
    report: object,
    *,
    witness_id: object,
    witness_kind: object,
    witness_ref: object,
    payload: Optional[Mapping[str, object]] = None,
) -> VerifyDecision:
    """May this report be independently verified by this witness?

    ``report`` must be an admitted ``ReportDecision``. A refused or
    foreign report fails closed — UNKNOWN is not FALSE.

    ``witness_id``, ``witness_kind``, and ``witness_ref`` are
    required names. Unknown witness kinds fail closed. A sealed
    send/ready name is a known refusal (``sealed_effect``).

    Same-id witness is ``self_verify``. An agent-report witness is
    ``not_independent``. A timeout is ``timeout_unknown`` — not
    concurrent writing. A proposal note is
    ``proposal_is_not_execution``.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    if not isinstance(report, ReportDecision):
        raise FailClosedError(
            f"verify_report requires a ReportDecision: {type(report)!r}")

    wid = _require_name(witness_id, what="witness_id")
    wkind = _require_name(witness_kind, what="witness_kind")
    wref = _require_name(witness_ref, what="witness_ref")

    if _is_sealed(wid) or _is_sealed(wkind) or _is_sealed(wref):
        return VerifyDecision(
            verified=False,
            reason="sealed_effect",
            witness_kind=wkind,
            witness_id=wid,
            independently_verified=False,
        )

    if payload is not None:
        if isinstance(payload, (str, bytes, bytearray)) or not isinstance(payload, Mapping):
            raise FailClosedError(f"payload must be a mapping: {payload!r}")
        smuggled = payload_forbidden_effect(payload)
        if smuggled is not None:
            return VerifyDecision(
                verified=False,
                reason="smuggled_effect",
                witness_kind=wkind,
                witness_id=wid,
                independently_verified=False,
            )

    if not report.admitted:
        return VerifyDecision(
            verified=False,
            reason="report_not_admitted",
            witness_kind=wkind,
            witness_id=wid,
            independently_verified=False,
        )

    if wid == report.reporter:
        return VerifyDecision(
            verified=False,
            reason="self_verify",
            witness_kind=wkind,
            witness_id=wid,
            independently_verified=False,
        )

    if wkind == "timeout":
        return VerifyDecision(
            verified=False,
            reason="timeout_unknown",
            witness_kind=wkind,
            witness_id=wid,
            independently_verified=False,
        )

    if wkind == "proposal_note":
        return VerifyDecision(
            verified=False,
            reason="proposal_is_not_execution",
            witness_kind=wkind,
            witness_id=wid,
            independently_verified=False,
        )

    if wkind in {"agent_report", "measurement_note"}:
        return VerifyDecision(
            verified=False,
            reason="not_independent",
            witness_kind=wkind,
            witness_id=wid,
            independently_verified=False,
        )

    if wkind not in WITNESS_KINDS:
        raise FailClosedError(
            f"unknown witness kind is not a refusal and not a grant: "
            f"{wkind!r} — UNKNOWN is not FALSE")

    return VerifyDecision(
        verified=True,
        reason=None,
        witness_kind=wkind,
        witness_id=wid,
        independently_verified=True,
    )
