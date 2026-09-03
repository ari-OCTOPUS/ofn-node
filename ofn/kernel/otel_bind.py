"""OTel bind — kernel-pure span-name admission.

Binding a known spine kind to a span name is admitted so the
architecture contract can continue. Emitting, exporting, or
naming a send is refused. A mapping is not an export.

``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.
Unknown kinds fail closed — an unmapped event is not dropped
into a generic span. Timeout is UNKNOWN. It does not prove
concurrent writing.

Distinct from ``otel_map`` (owned by an open change). This
module restates the nine-kind vocabulary so it can land on a
body that does not carry that file. It does not import an
exporter, a network stack, or a third-party SDK.

Not wired into the run store. HALT stops STARTS, not
classification. Admitting a bind is not a send.

Kernel purity: typing + dataclasses. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from .errors import FailClosedError
from .events import EVENT_KINDS, is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"bind", "export", "emit_send"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "unknown_activity",
    "suspected_concurrent",
    "export_forbidden",
    "emit_send_forbidden",
    "unknown_kind",
})

# Stable span names. Dots, not slashes; no vendor product names.
SPAN_BY_KIND: Mapping[str, str] = {
    "RUN_CREATED": "run.created",
    "CLAIM_CREATED": "claim.created",
    "PROPOSAL_CREATED": "proposal.created",
    "POLICY_DECISION": "policy.decision",
    "TOOL_INVOKED": "tool.invoked",
    "EXECUTION_RECEIPT": "execution.receipt",
    "BUDGET_DEBIT": "budget.debit",
    "RUN_CLOSED": "run.closed",
    "RUN_REJECTED": "run.rejected",
}

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An otel bind never authorizes a send. Structurally False."""
    return False


def halt_blocks_otel() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A bind verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def exports_spans() -> bool:
    """Structurally False. A bind is not an export."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Binding a span name is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold(name) in {_fold(s) for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def _require_member(value: object, *, what: str, allowed: frozenset[str]) -> str:
    name = _require_name(value, what=what)
    if name not in allowed:
        raise FailClosedError(
            f"unknown {what} is not a refusal and not a grant: {name!r}")
    return name


def classify_status(*, activity: str, timed_out: bool) -> str:
    """Derive the bind-row status. Timeout outranks activity.

    A timeout is UNKNOWN even when activity says concurrent.
    That is the load-bearing rule: timeout does not prove a race.
    """
    if timed_out:
        return "UNKNOWN"
    if activity == "unknown":
        return "UNKNOWN"
    if activity == "concurrent":
        return "SUSPECTED"
    if activity == "idle":
        return "VERIFIED"
    raise FailClosedError(
        f"unknown activity is not a refusal and not a grant: {activity!r}")


def span_name(kind: str) -> str:
    """Look up the span name. Unknown kinds fail closed."""
    if kind not in SPAN_BY_KIND:
        raise FailClosedError(f"no span binding for event kind: {kind!r}")
    return SPAN_BY_KIND[kind]


@dataclass(frozen=True)
class OtelDecision:
    """The bind-admission verdict. ``grants_send`` is structurally False."""

    allowed: bool
    reason: Optional[str]
    status: str
    kind: str
    intended: str
    span: Optional[str]
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "OtelDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — an otel bind is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown otel status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(self, "kind", _require_name(self.kind, what="kind"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed otel bind must not carry a reason: {self.reason!r}")
            if self.intended != "bind":
                raise FailClosedError(
                    "OtelDecision cannot allow export or emit_send")
            if self.status != "VERIFIED":
                raise FailClosedError(
                    "OtelDecision cannot allow a bind unless VERIFIED")
            if self.span is None or self.span != span_name(self.kind):
                raise FailClosedError(
                    "allowed otel bind must carry the mapped span name")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
            if self.span is not None:
                raise FailClosedError(
                    "refused otel bind must not carry a span name")
        if _is_sealed(self.kind) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "OtelDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_otel(
    *,
    kind: object,
    intended: object,
    activity: object,
    timed_out: object = False,
) -> OtelDecision:
    """May this event kind be bound to a span name?

    ``kind``, ``intended``, and ``activity`` are required names.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as idle.

    ``timed_out`` must be an exact bool. True forces status
    UNKNOWN. It does not classify the row as SUSPECTED.

    ``export`` and ``emit_send`` are always refused. ``bind`` is
    admitted only when VERIFIED and the kind is in the nine-kind
    spine. A sealed send/ready name is never a kind.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    raw_kind = _require_name(kind, what="kind")
    raw_intent = _require_name(intended, what="intended")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_kind) or _is_sealed(raw_intent):
        raise FailClosedError(
            "otel names a sealed send/ready state: "
            f"kind={raw_kind!r} intended={raw_intent!r}")

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if intent == "export":
        return OtelDecision(
            allowed=False,
            reason="export_forbidden",
            status=status,
            kind=raw_kind,
            intended=intent,
            span=None,
            timed_out=timed_out,
        )
    if intent == "emit_send":
        return OtelDecision(
            allowed=False,
            reason="emit_send_forbidden",
            status=status,
            kind=raw_kind,
            intended=intent,
            span=None,
            timed_out=timed_out,
        )

    if raw_kind not in EVENT_KINDS or raw_kind not in SPAN_BY_KIND:
        return OtelDecision(
            allowed=False,
            reason="unknown_kind",
            status=status,
            kind=raw_kind,
            intended=intent,
            span=None,
            timed_out=timed_out,
        )

    if status == "UNKNOWN":
        return OtelDecision(
            allowed=False,
            reason="unknown_activity",
            status=status,
            kind=raw_kind,
            intended=intent,
            span=None,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return OtelDecision(
            allowed=False,
            reason="suspected_concurrent",
            status=status,
            kind=raw_kind,
            intended=intent,
            span=None,
            timed_out=timed_out,
        )
    return OtelDecision(
        allowed=True,
        reason=None,
        status=status,
        kind=raw_kind,
        intended=intent,
        span=span_name(raw_kind),
        timed_out=timed_out,
    )
