"""Journal class — kernel-pure sidecar and log-file admission.

Opening or fsyncing a wal / shm / events_jsonl / sqlite_db
artifact is admitted so durability work can continue. Unlink
and truncate of those artifacts are refused: a -wal or -shm
sidecar is never deleted by hand, and the event log is
append-only.

``chmod_recursive_root`` is refused. Mode changes are measured
per path, never walked from a backup or store root.

Timeout is UNKNOWN. It does not prove concurrent writing.
Activity ``unknown`` is UNKNOWN, not FALSE and not idle.

A sealed send/ready name is never an artifact and never an
intent. ``campaign_envelope_ready`` is structurally distinct
from ``send_authorized``; both are refused as ``sealed_effect``.

Not wired into the run store. HALT stops STARTS, not
classification. Admitting an open or fsync is not a send.

Kernel purity: typing + dataclasses. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
ARTIFACTS = frozenset({"wal", "shm", "events_jsonl", "sqlite_db"})
INTENTS = frozenset({
    "open", "fsync", "unlink", "truncate", "chmod_recursive_root",
})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "unknown_activity",
    "suspected_concurrent",
    "unlink_forbidden",
    "truncate_forbidden",
    "recursive_chmod_forbidden",
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
    """A journal class never authorizes a send. Structurally False."""
    return False


def halt_blocks_journal() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A journal verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def deletes_wal_shm() -> bool:
    """Structurally False. Sidecars are never unlinked by this class."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a journal row is not an external effect."""
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
    """Derive the journal-row status. Timeout outranks activity.

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
class JournalDecision:
    """The journal-admission verdict. ``grants_send`` is structurally False."""

    allowed: bool
    reason: Optional[str]
    status: str
    artifact: str
    intended: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "JournalDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a journal class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown journal status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.artifact not in ARTIFACTS:
            raise FailClosedError(
                f"unknown or missing artifact: {self.artifact!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed journal must not carry a reason: {self.reason!r}")
            if self.intended in {"unlink", "truncate", "chmod_recursive_root"}:
                raise FailClosedError(
                    "JournalDecision cannot allow unlink/truncate/recursive chmod")
            if self.intended in {"open", "fsync"} and self.status != "VERIFIED":
                raise FailClosedError(
                    "JournalDecision cannot allow open/fsync unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.artifact) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "JournalDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_journal(
    *,
    artifact: object,
    intended: object,
    activity: object,
    timed_out: object = False,
) -> JournalDecision:
    """May this journal artifact be opened, synced, or destroyed?

    ``artifact``, ``intended``, and ``activity`` are required names.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as idle.

    ``timed_out`` must be an exact bool. True forces status
    UNKNOWN. It does not classify the row as SUSPECTED.

    ``unlink`` / ``truncate`` / ``chmod_recursive_root`` are always
    refused. ``open`` / ``fsync`` are admitted only when VERIFIED.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    raw_artifact = _require_name(artifact, what="artifact")
    raw_intent = _require_name(intended, what="intended")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_artifact) or _is_sealed(raw_intent):
        # Sealed tokens are not members of ARTIFACTS/INTENTS. Refuse
        # as sealed_effect without constructing a decision that
        # would fail the closed-vocabulary constructor.
        raise FailClosedError(
            "journal names a sealed send/ready state: "
            f"artifact={raw_artifact!r} intended={raw_intent!r}")

    artifact_name = _require_member(
        raw_artifact, what="artifact", allowed=ARTIFACTS)
    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)

    status = classify_status(activity=activity_name, timed_out=timed_out)

    if intent == "unlink":
        return JournalDecision(
            allowed=False,
            reason="unlink_forbidden",
            status=status,
            artifact=artifact_name,
            intended=intent,
            timed_out=timed_out,
        )
    if intent == "truncate":
        return JournalDecision(
            allowed=False,
            reason="truncate_forbidden",
            status=status,
            artifact=artifact_name,
            intended=intent,
            timed_out=timed_out,
        )
    if intent == "chmod_recursive_root":
        return JournalDecision(
            allowed=False,
            reason="recursive_chmod_forbidden",
            status=status,
            artifact=artifact_name,
            intended=intent,
            timed_out=timed_out,
        )

    # intent in {open, fsync}
    if status == "UNKNOWN":
        return JournalDecision(
            allowed=False,
            reason="unknown_activity",
            status=status,
            artifact=artifact_name,
            intended=intent,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return JournalDecision(
            allowed=False,
            reason="suspected_concurrent",
            status=status,
            artifact=artifact_name,
            intended=intent,
            timed_out=timed_out,
        )
    return JournalDecision(
        allowed=True,
        reason=None,
        status=status,
        artifact=artifact_name,
        intended=intent,
        timed_out=timed_out,
    )
