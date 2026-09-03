"""Store class — kernel-pure RunStore append/replay/reopen admission.

``adapters.run_store.RunStore`` owns the JSONL file. This module is
the third witness: may an append, a replay, a reopen, or a rewrite
be classified as admitted?

``rewrite`` is never admitted — the ledger is append-only.
``replay`` and ``reopen`` are read-side recovery and are admitted
for a known kind. ``append`` of ``RUN_CREATED`` is a START: HALT
refuses it. Append of any other known kind is in-flight work and
is not blocked by HALT.

Append after close is refused. A second ``BUDGET_DEBIT`` against
the same prior receipt is refused (one verdict → one budget
effect). A sealed send/ready name is never a kind and never an
intent. ``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not append.

Not wired into the run store. Admitting a replay or an in-flight
append is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import (
    BUDGET_DEBIT,
    EVENT_KINDS,
    RUN_CREATED,
    is_forbidden_effect_name,
)

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"append", "replay", "reopen", "rewrite"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "rewrite_forbidden",
    "append_after_close",
    "second_debit",
    "halt_start",
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
    """A store class never authorizes a send. Structurally False."""
    return False


def halt_blocks_inflight_append() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight appends."""
    return False


def rewrites_ledger() -> bool:
    """Structurally False. Rewrite is never admitted."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A store verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a store row is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A refused append does not burn the key."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
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
    """Derive the store-row status. Timeout outranks activity.

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
class StoreDecision:
    """The store-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    status: str
    intended: str
    kind: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "StoreDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a store class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown store status is not a refusal and not a grant: "
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
                    f"allowed store must not carry a reason: {self.reason!r}")
            if self.intended == "rewrite":
                raise FailClosedError(
                    "StoreDecision cannot allow rewrite")
            if self.intended == "append" and self.status != "VERIFIED":
                raise FailClosedError(
                    "StoreDecision cannot allow an append unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.kind) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "StoreDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_store(
    *,
    intended: object,
    kind: object,
    activity: object = "idle",
    closed: object = False,
    halted: object = False,
    timed_out: object = False,
    prior_debit: object = False,
) -> StoreDecision:
    """May this store action hit this event kind?

    ``intended`` and ``kind`` are required names. Unknown names fail
    closed — UNKNOWN is not FALSE and is not admitted as idle.

    ``closed``, ``halted``, ``timed_out``, and ``prior_debit`` must
    be exact bools. Timeout forces status UNKNOWN. It does not
    classify the row as SUSPECTED.

    ``rewrite`` is always refused. ``append`` after close is refused.
    A second ``BUDGET_DEBIT`` (``prior_debit=True``) is refused.
    HALT refuses only an append of ``RUN_CREATED``.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_kind = _require_name(kind, what="kind")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(closed) is not bool:
        raise FailClosedError(f"closed must be an exact bool: {closed!r}")
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    if type(prior_debit) is not bool:
        raise FailClosedError(
            f"prior_debit must be an exact bool: {prior_debit!r}")

    if _is_sealed(raw_intent) or _is_sealed(raw_kind):
        return StoreDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            intended=raw_intent if raw_intent in INTENTS else "append",
            kind=raw_kind,
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    if raw_kind not in EVENT_KINDS:
        raise FailClosedError(
            f"unknown event kind is not a refusal and not a grant: "
            f"{raw_kind!r}")

    status = classify_status(activity=activity_name, timed_out=timed_out)

    if intent == "rewrite":
        return StoreDecision(
            allowed=False,
            reason="rewrite_forbidden",
            status=status,
            intended=intent,
            kind=raw_kind,
            timed_out=timed_out,
        )

    if intent in {"replay", "reopen"}:
        return StoreDecision(
            allowed=True,
            reason=None,
            status=status,
            intended=intent,
            kind=raw_kind,
            timed_out=timed_out,
        )

    # intent == append
    if closed:
        return StoreDecision(
            allowed=False,
            reason="append_after_close",
            status=status,
            intended=intent,
            kind=raw_kind,
            timed_out=timed_out,
        )
    if raw_kind == BUDGET_DEBIT and prior_debit:
        return StoreDecision(
            allowed=False,
            reason="second_debit",
            status=status,
            intended=intent,
            kind=raw_kind,
            timed_out=timed_out,
        )
    if raw_kind == RUN_CREATED and halted:
        return StoreDecision(
            allowed=False,
            reason="halt_start",
            status=status,
            intended=intent,
            kind=raw_kind,
            timed_out=timed_out,
        )
    if status == "UNKNOWN":
        return StoreDecision(
            allowed=False,
            reason="unknown_activity",
            status=status,
            intended=intent,
            kind=raw_kind,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return StoreDecision(
            allowed=False,
            reason="suspected_concurrent",
            status=status,
            intended=intent,
            kind=raw_kind,
            timed_out=timed_out,
        )
    return StoreDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        kind=raw_kind,
        timed_out=timed_out,
    )
