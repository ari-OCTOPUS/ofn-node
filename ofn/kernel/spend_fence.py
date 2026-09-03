"""Spend fence — a token FIT cannot become send_authorized.

``token_class`` records both ceiling verdicts. This fence is
the wall: a dual ``FIT`` is still not a send. ``promote_send``
and ``quote`` are never admitted. ``observe`` is admitted so
the owner-absent operator can keep classifying.

A later disarm/hold supersedes an older authorization claim.
This fence never grants a send. Missing is UNKNOWN (None),
not FALSE. Timeout does not prove a writer.

``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as sealed promotion
targets. ``quote_sent`` is a sealed external effect.

Distinct from ``send_fence`` (campaign-ready wall),
``token_ceiling``, ``budget_class``, and ``token_class``.
Not wired into the run store. HALT stops STARTS, not this
fence.

Kernel purity: typing + dataclasses. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .token_class import (
    VERDICTS,
    _is_sealed,
    _require_exact_bool,
    _require_member,
    _require_name,
    classify_status,
)

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"observe", "promote_send", "quote"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "promote_send_forbidden",
    "quote_forbidden",
    "unknown_activity",
    "suspected_concurrent",
})


def grants_send() -> bool:
    """A spend fence never authorizes a send. Structurally False."""
    return False


def halt_blocks_fence() -> bool:
    """Structurally False. HALT stops STARTS, not this fence."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A fence verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def fit_is_send() -> bool:
    """Structurally False. A dual FIT is not send_authorized."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Observing a FIT is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


@dataclass(frozen=True)
class SpendDecision:
    """The fence verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent
    default cannot masquerade as an authorization: ``allowed``
    and ``grants_send`` are both recorded, and the constructor
    refuses ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    verdict: str
    status: str
    intended: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "SpendDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a spend fence is not a send")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        if self.verdict not in VERDICTS:
            raise FailClosedError(
                f"unknown spend verdict is not a refusal and not a grant: "
                f"{self.verdict!r}")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown spend status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed spend fence must not carry a reason: "
                    f"{self.reason!r}")
            if self.intended != "observe":
                raise FailClosedError(
                    "SpendDecision cannot allow promote_send or quote")
            if self.status != "VERIFIED":
                raise FailClosedError(
                    "SpendDecision cannot allow an observe unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.intended) or _is_sealed(self.verdict):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "SpendDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_spend(
    *,
    intended: object,
    activity: object,
    verdict: object,
    timed_out: object = False,
) -> SpendDecision:
    """May this token verdict be observed, promoted, or quoted?

    ``intended``, ``activity``, and ``verdict`` are required
    names. Unknown names fail closed — UNKNOWN is not FALSE
    and is not admitted as idle.

    ``timed_out`` must be an exact bool. True forces status
    UNKNOWN. It does not classify the row as SUSPECTED.

    ``promote_send`` and ``quote`` are always refused, including
    when ``verdict`` is ``FIT``. ``observe`` is admitted only
    when VERIFIED. A sealed send/ready name is never an intent
    and never a verdict.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    raw_verdict = _require_name(verdict, what="verdict")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_intent) or _is_sealed(raw_verdict):
        raise FailClosedError(
            "spend names a sealed send/ready state: "
            f"intended={raw_intent!r} verdict={raw_verdict!r}")

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    verdict_name = _require_member(
        raw_verdict, what="verdict", allowed=VERDICTS)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if intent == "promote_send":
        return SpendDecision(
            allowed=False,
            reason="promote_send_forbidden",
            verdict=verdict_name,
            status=status,
            intended=intent,
            timed_out=timed_out,
        )
    if intent == "quote":
        return SpendDecision(
            allowed=False,
            reason="quote_forbidden",
            verdict=verdict_name,
            status=status,
            intended=intent,
            timed_out=timed_out,
        )

    if status == "UNKNOWN":
        return SpendDecision(
            allowed=False,
            reason="unknown_activity",
            verdict=verdict_name,
            status=status,
            intended=intent,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return SpendDecision(
            allowed=False,
            reason="suspected_concurrent",
            verdict=verdict_name,
            status=status,
            intended=intent,
            timed_out=timed_out,
        )
    return SpendDecision(
        allowed=True,
        reason=None,
        verdict=verdict_name,
        status=status,
        intended=intent,
        timed_out=timed_out,
    )


# Imported by tests that lock the helper surface. Not a send knob.
require_exact_bool = _require_exact_bool
