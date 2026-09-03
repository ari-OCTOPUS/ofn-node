"""Census class — kernel-pure worktree inventory admission.

A census row is a classification, not a prune and not a send.
``observe`` is admitted for a known vocabulary so inventory can
continue while the owner is absent. ``write`` is admitted only
when the row is VERIFIED and idle. ``prune`` is never admitted.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not classify a sibling as SUSPECTED. Activity ``unknown``
is UNKNOWN, not FALSE and not idle.

Disk absence on this host is ``body_not_on_this_host``, never
``body_missing``. The wrong label fails closed.

A sealed send/ready name is never a path and never a label.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

HALT stops STARTS. This module has no halt parameter: classifying
a row is not a run start.

Not wired into the run store (that file is owned by an open change).

Admitting an observe or a verified write is not
``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
INTENTS = frozenset({"observe", "write", "prune"})
DISK_LABELS = frozenset({"none", "body_not_on_this_host"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "unknown_activity",
    "suspected_concurrent",
    "prune_forbidden",
    "body_not_on_this_host",
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
    """A census class never authorizes a send. Structurally False."""
    return False


def halt_blocks_census() -> bool:
    """Structurally False. HALT stops STARTS, not inventory."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A census row is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def prunes_worktree() -> bool:
    """Structurally False. Inventory does not prune."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a row is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def body_missing_is_valid_label() -> bool:
    """Structurally False. The valid absence label is body_not_on_this_host."""
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
    """Derive the census status. Timeout outranks activity.

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


@dataclass(frozen=True)
class CensusDecision:
    """The census-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    status: str
    path: str
    intended: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "CensusDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a census class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown census status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(self, "path", _require_name(self.path, what="path"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed census must not carry a reason: {self.reason!r}")
            if self.intended == "prune":
                raise FailClosedError(
                    "CensusDecision cannot allow prune")
            if self.intended == "write" and self.status != "VERIFIED":
                raise FailClosedError(
                    "CensusDecision cannot allow a write unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.path):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "CensusDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_census(
    *,
    path: object,
    activity: object,
    intended: object,
    timed_out: object = False,
    disk_label: object = "none",
) -> CensusDecision:
    """May this worktree row be observed, written, or pruned?

    ``path``, ``activity``, and ``intended`` are required names.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as idle.

    ``timed_out`` must be an exact bool. True forces status
    UNKNOWN. It does not classify the row as SUSPECTED.

    ``disk_label`` is a closed vocabulary. ``body_missing`` is
    not a member — the valid absence token is
    ``body_not_on_this_host``. A write against that label is
    refused; an observe is admitted.

    ``prune`` is always refused.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    path_name = _require_name(path, what="path")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    intent = _require_member(intended, what="intended", allowed=INTENTS)
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    label = _require_member(
        disk_label, what="disk_label", allowed=DISK_LABELS)

    if _is_sealed(path_name):
        return CensusDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            path=path_name,
            intended=intent,
            timed_out=timed_out,
        )

    status = classify_status(activity=activity_name, timed_out=timed_out)

    if intent == "prune":
        return CensusDecision(
            allowed=False,
            reason="prune_forbidden",
            status=status,
            path=path_name,
            intended=intent,
            timed_out=timed_out,
        )

    if intent == "observe":
        return CensusDecision(
            allowed=True,
            reason=None,
            status=status,
            path=path_name,
            intended=intent,
            timed_out=timed_out,
        )

    # intent == write
    if label == "body_not_on_this_host":
        return CensusDecision(
            allowed=False,
            reason="body_not_on_this_host",
            status=status,
            path=path_name,
            intended=intent,
            timed_out=timed_out,
        )
    if status == "UNKNOWN":
        return CensusDecision(
            allowed=False,
            reason="unknown_activity",
            status=status,
            path=path_name,
            intended=intent,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return CensusDecision(
            allowed=False,
            reason="suspected_concurrent",
            status=status,
            path=path_name,
            intended=intent,
            timed_out=timed_out,
        )
    return CensusDecision(
        allowed=True,
        reason=None,
        status=status,
        path=path_name,
        intended=intent,
        timed_out=timed_out,
    )
