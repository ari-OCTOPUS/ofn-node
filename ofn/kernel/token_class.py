"""Token class — kernel-pure dual-ceiling claim identity.

``token_ceiling`` does the arithmetic. ``budget_class`` admits a
debit against one surface. This module is the third witness:
were *both* ceiling verdicts recorded, and do they agree?

A missing witness fails closed. UNKNOWN is not a fit and is
not zero. Disagreement is ``SPLIT``; this module does not pick
a winner. Timeout is UNKNOWN. It does not prove concurrent
spending.

A sealed send/ready name is never an intent and never a
verdict. ``campaign_envelope_ready`` is structurally distinct
from ``send_authorized``; both are refused as ``sealed_effect``.

``grant_send`` is never admitted. A dual ``FIT`` is not a send.

Not wired into the run store. Distinct from ``token_ceiling``,
``budget_class``, ``callbudget``, and ``quota``. HALT stops
STARTS, not classification.

Kernel purity: typing + dataclasses. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"classify", "grant_send"})
VERDICTS = frozenset({"FIT", "MISS", "SPLIT"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "grant_send_forbidden",
    "unknown_activity",
    "suspected_concurrent",
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
    """A token class never authorizes a send. Structurally False."""
    return False


def halt_blocks_token() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A token claim is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_is_fit() -> bool:
    """Structurally False. A missing witness is not a fit."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def silently_picks_split() -> bool:
    """Structurally False. SPLIT is recorded; no winner is chosen."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a claim is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent spending."""
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


def _require_exact_bool(value: object, *, what: str) -> bool:
    """Exact bool. Missing is not False and is not a fit."""
    if type(value) is not bool:
        raise FailClosedError(
            f"{what} must be an exact bool (unknown is not a fit): {value!r}")
    return value


def classify_status(*, activity: str, timed_out: bool) -> str:
    """Derive the claim-row status. Timeout outranks activity.

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


def classify_verdict(*, per_run: bool, node: bool) -> str:
    """Both witnesses recorded. Disagreement is SPLIT, not a pick."""
    if per_run is True and node is True:
        return "FIT"
    if per_run is False and node is False:
        return "MISS"
    return "SPLIT"


@dataclass(frozen=True)
class TokenClaim:
    """Dual-ceiling claim. ``grants_send`` is structurally False.

    Two independent verdicts live on the same object so a silent
    default cannot masquerade as agreement: ``per_run`` and
    ``node`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    per_run: bool
    node: bool
    verdict: str
    status: str
    intended: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "TokenClaim cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a token class is not a send")
        if type(self.per_run) is not bool:
            raise FailClosedError(
                f"per_run must be an exact bool: {self.per_run!r}")
        if type(self.node) is not bool:
            raise FailClosedError(
                f"node must be an exact bool: {self.node!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        if self.verdict not in VERDICTS:
            raise FailClosedError(
                f"unknown token verdict is not a refusal and not a grant: "
                f"{self.verdict!r}")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown token status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        expected = classify_verdict(per_run=self.per_run, node=self.node)
        if self.verdict != expected:
            raise FailClosedError(
                f"verdict {self.verdict!r} does not match recorded "
                f"per_run={self.per_run!r} node={self.node!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed token claim must not carry a reason: "
                    f"{self.reason!r}")
            if self.intended != "classify":
                raise FailClosedError(
                    "TokenClaim cannot allow grant_send")
            if self.status != "VERIFIED":
                raise FailClosedError(
                    "TokenClaim cannot allow a classify unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.intended) or _is_sealed(self.verdict):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "TokenClaim cannot grant or mis-label a sealed "
                    "send/ready name")


def classify_token(
    *,
    per_run: object,
    node: object,
    intended: object,
    activity: object,
    timed_out: object = False,
) -> TokenClaim:
    """May this dual-ceiling claim be classified?

    ``per_run`` and ``node`` are required exact bools. Missing
    is not False and is not a fit. Both are recorded so a
    silent default cannot masquerade as agreement.

    ``intended`` and ``activity`` are required names. Unknown
    names fail closed — UNKNOWN is not FALSE and is not
    admitted as idle.

    ``timed_out`` must be an exact bool. True forces status
    UNKNOWN. It does not classify the row as SUSPECTED and it
    does not prove concurrent spending.

    ``grant_send`` is always refused. ``classify`` is admitted
    only when VERIFIED. A ``FIT`` verdict still does not grant
    send.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    per_run_fit = _require_exact_bool(per_run, what="per_run")
    node_fit = _require_exact_bool(node, what="node")
    raw_intent = _require_name(intended, what="intended")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_intent):
        raise FailClosedError(
            f"token names a sealed send/ready state: intended={raw_intent!r}")

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    status = classify_status(activity=activity_name, timed_out=timed_out)
    verdict = classify_verdict(per_run=per_run_fit, node=node_fit)

    if intent == "grant_send":
        return TokenClaim(
            allowed=False,
            reason="grant_send_forbidden",
            per_run=per_run_fit,
            node=node_fit,
            verdict=verdict,
            status=status,
            intended=intent,
            timed_out=timed_out,
        )

    if status == "UNKNOWN":
        return TokenClaim(
            allowed=False,
            reason="unknown_activity",
            per_run=per_run_fit,
            node=node_fit,
            verdict=verdict,
            status=status,
            intended=intent,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return TokenClaim(
            allowed=False,
            reason="suspected_concurrent",
            per_run=per_run_fit,
            node=node_fit,
            verdict=verdict,
            status=status,
            intended=intent,
            timed_out=timed_out,
        )
    return TokenClaim(
        allowed=True,
        reason=None,
        per_run=per_run_fit,
        node=node_fit,
        verdict=verdict,
        status=status,
        intended=intent,
        timed_out=timed_out,
    )
