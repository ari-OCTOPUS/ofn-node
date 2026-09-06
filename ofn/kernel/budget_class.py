"""Budget class — kernel-pure token-spend admission.

``observe`` is admitted so a ceiling can be read while the owner
is absent. ``debit`` is admitted only when the row is VERIFIED
and the request fits the remaining tokens. A zero ceiling
authorizes only a zero request. ``credit`` is refused: this
class does not mint tokens. ``grant_send`` is refused: a budget
fit is not a send.

Unknown or non-int token fields fail closed. Missing is not
zero when the field is present and unreadable. Timeout is
UNKNOWN. It does not prove concurrent spending.

A sealed send/ready name is never an intent and never a
surface. ``campaign_envelope_ready`` is structurally distinct
from ``send_authorized``; both are refused as ``sealed_effect``.

Not wired into the run store (that file is owned by an open
change) and not a rewrite of ``token_ceiling``. HALT stops
STARTS, not classification. Admitting a debit is not
``send_authorized``.

Kernel purity: typing + dataclasses. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"observe", "debit", "credit", "grant_send"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
SURFACES = frozenset({"run_budget", "node_quota"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "unknown_activity",
    "suspected_concurrent",
    "credit_forbidden",
    "grant_send_forbidden",
    "ceiling_exhausted",
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
    """A budget class never authorizes a send. Structurally False."""
    return False


def halt_blocks_budget() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A budget verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def unknown_tokens_are_zero() -> bool:
    """Structurally False. An unreadable token field is not zero."""
    return False


def mints_credit() -> bool:
    """Structurally False. This class does not mint tokens."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a debit is not an external effect."""
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


def _require_tokens(value: object, *, what: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FailClosedError(
            f"{what} must be a non-negative int: {value!r}")
    return value


def classify_status(*, activity: str, timed_out: bool) -> str:
    """Derive the budget-row status. Timeout outranks activity.

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


def request_fits(*, ceiling: int, already: int, request: int) -> bool:
    """The envelope rule, without needing the envelope object.

    Zero ceiling authorizes only a zero request. Unknown or
    negative values are the caller's problem — this helper
    assumes ``_require_tokens`` already ran.
    """
    if ceiling == 0:
        return request == 0
    return already + request <= ceiling


@dataclass(frozen=True)
class BudgetDecision:
    """The budget-admission verdict. ``grants_send`` is structurally False."""

    allowed: bool
    reason: Optional[str]
    status: str
    intended: str
    surface: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "BudgetDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a budget class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown budget status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.surface not in SURFACES:
            raise FailClosedError(
                f"unknown or missing surface: {self.surface!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed budget must not carry a reason: {self.reason!r}")
            if self.intended in {"credit", "grant_send"}:
                raise FailClosedError(
                    "BudgetDecision cannot allow credit or grant_send")
            if self.intended in {"observe", "debit"} and self.status != "VERIFIED":
                raise FailClosedError(
                    "BudgetDecision cannot allow observe/debit unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.intended) or _is_sealed(self.surface):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "BudgetDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_budget(
    *,
    intended: object,
    activity: object,
    surface: object = "run_budget",
    ceiling: object = 0,
    already: object = 0,
    request: object = 0,
    timed_out: object = False,
) -> BudgetDecision:
    """May this budget surface be observed or debited?

    ``intended``, ``activity``, and ``surface`` are required names.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as idle.

    ``ceiling``, ``already``, and ``request`` must be non-negative
    ints. Bool and missing-as-None fail closed. A present
    unreadable value is not treated as zero.

    ``timed_out`` must be an exact bool. True forces status
    UNKNOWN. It does not classify the row as SUSPECTED.

    ``credit`` and ``grant_send`` are always refused. ``observe``
    and ``debit`` are admitted only when VERIFIED. A debit that
    does not fit the remaining tokens is ``ceiling_exhausted``.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_surface = _require_name(surface, what="surface")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    ceiling_n = _require_tokens(ceiling, what="ceiling")
    already_n = _require_tokens(already, what="already")
    request_n = _require_tokens(request, what="request")

    if _is_sealed(raw_intent) or _is_sealed(raw_surface):
        raise FailClosedError(
            "budget names a sealed send/ready state: "
            f"intended={raw_intent!r} surface={raw_surface!r}")

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    surface_name = _require_member(
        raw_surface, what="surface", allowed=SURFACES)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if intent == "credit":
        return BudgetDecision(
            allowed=False,
            reason="credit_forbidden",
            status=status,
            intended=intent,
            surface=surface_name,
            timed_out=timed_out,
        )
    if intent == "grant_send":
        return BudgetDecision(
            allowed=False,
            reason="grant_send_forbidden",
            status=status,
            intended=intent,
            surface=surface_name,
            timed_out=timed_out,
        )

    # intent in {observe, debit}
    if status == "UNKNOWN":
        return BudgetDecision(
            allowed=False,
            reason="unknown_activity",
            status=status,
            intended=intent,
            surface=surface_name,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return BudgetDecision(
            allowed=False,
            reason="suspected_concurrent",
            status=status,
            intended=intent,
            surface=surface_name,
            timed_out=timed_out,
        )
    if intent == "debit" and not request_fits(
            ceiling=ceiling_n, already=already_n, request=request_n):
        return BudgetDecision(
            allowed=False,
            reason="ceiling_exhausted",
            status=status,
            intended=intent,
            surface=surface_name,
            timed_out=timed_out,
        )
    return BudgetDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        surface=surface_name,
        timed_out=timed_out,
    )
