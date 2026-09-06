"""Report class — kernel-pure typed agent report.

An agent report is a claim about what an agent said. Existing is
not independent verification. A second, distinct witness is
required before anything is called a verification — that lives in
``verify_class``.

Proposal notes are not execution. Measurement notes are not a
send. ``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused.

HALT stops STARTS. This classifier has no halt parameter:
classification is collection-only and must still run so recovery
does not need the owner.

Not wired into the run store (that file is owned by another
change).

Admitting a report is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name, payload_forbidden_effect

# Closed report vocabulary. Widen only with a test.
REPORT_KINDS = frozenset({
    "agent_report",
    "measurement_note",
    "proposal_note",
})

# Known refusals. Unknown kinds fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "smuggled_effect",
})

SCOPES = frozenset({"this_host_only"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A report never authorizes a send. Structurally False."""
    return False


def halt_blocks_report() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A report is not chattr +i."""
    return False


def report_is_verified() -> bool:
    """Structurally False. Agent-reported is not independently verified."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal_note is not an execution."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def default_scope() -> str:
    return "this_host_only"


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
class ReportDecision:
    """The report-admission verdict.

    Two independent claims live on the same object so a silent
    default cannot masquerade as verification or a send:
    ``admitted`` / ``independently_verified`` / ``grants_send`` are
    all recorded, and the constructor refuses the last two as True.
    """

    admitted: bool
    reason: Optional[str]
    kind: str
    reporter: str
    subject: str
    independently_verified: bool = False
    grants_send: bool = False
    scope: str = "this_host_only"

    def __post_init__(self) -> None:
        if self.independently_verified:
            raise FailClosedError(
                "ReportDecision cannot mark a report independently "
                "verified — agent-reported is not independently verified")
        if self.grants_send:
            raise FailClosedError(
                "ReportDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a report is not a send")
        if self.scope != "this_host_only":
            raise FailClosedError(
                f"a report cannot promote scope {self.scope!r} — "
                "default is this_host_only")
        if self.admitted:
            if self.reason is not None:
                raise FailClosedError(
                    f"admitted report must not carry a reason: {self.reason!r}")
            if self.kind not in REPORT_KINDS:
                raise FailClosedError(
                    f"admitted report kind is unknown: {self.kind!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        object.__setattr__(self, "kind", _require_name(self.kind, what="kind"))
        object.__setattr__(self, "reporter", _require_name(self.reporter, what="reporter"))
        object.__setattr__(self, "subject", _require_name(self.subject, what="subject"))
        if _is_sealed(self.kind) or _is_sealed(self.reporter) or _is_sealed(self.subject):
            if self.admitted or self.reason != "sealed_effect":
                raise FailClosedError(
                    "ReportDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def mint_report(
    *,
    kind: object,
    reporter: object,
    subject: object,
    payload: Optional[Mapping[str, object]] = None,
) -> ReportDecision:
    """Admit one typed report. Admission is not verification.

    ``kind``, ``reporter``, and ``subject`` are required names.
    Unknown kinds fail closed — UNKNOWN is not FALSE and is not
    admitted. A sealed send/ready name is a known refusal
    (``sealed_effect``), not an unknown.

    ``payload`` is optional. When supplied it must be a mapping.
    A smuggled sealed name is a known refusal (``smuggled_effect``).

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    kind_name = _require_name(kind, what="kind")
    reporter_name = _require_name(reporter, what="reporter")
    subject_name = _require_name(subject, what="subject")

    if _is_sealed(kind_name) or _is_sealed(reporter_name) or _is_sealed(subject_name):
        return ReportDecision(
            admitted=False,
            reason="sealed_effect",
            kind=kind_name,
            reporter=reporter_name,
            subject=subject_name,
        )

    if kind_name not in REPORT_KINDS:
        raise FailClosedError(
            f"unknown report kind is not a refusal and not a grant: "
            f"{kind_name!r} — UNKNOWN is not FALSE")

    if payload is not None:
        if isinstance(payload, (str, bytes, bytearray)) or not isinstance(payload, Mapping):
            raise FailClosedError(f"payload must be a mapping: {payload!r}")
        smuggled = payload_forbidden_effect(payload)
        if smuggled is not None:
            return ReportDecision(
                admitted=False,
                reason="smuggled_effect",
                kind=kind_name,
                reporter=reporter_name,
                subject=subject_name,
            )

    return ReportDecision(
        admitted=True,
        reason=None,
        kind=kind_name,
        reporter=reporter_name,
        subject=subject_name,
    )
