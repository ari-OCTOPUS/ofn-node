"""Slot class — kernel-pure RunStore slot occupancy admission.

``adapters.run_store.RunStore`` owns the JSONL file. ``store_class``
classifies append/replay/reopen/rewrite. This module is a fourth
witness: may a named run slot be occupied, released, or inspected?

A slot is occupancy of one ``run_id``. Occupying a slot is a START:
HALT refuses it. Release and inspect are not STARTS — HALT does
not block them. ``steal`` is never admitted; another body cannot
take a slot.

A second occupy against an already-occupied slot is refused
(``already_occupied``). Release of an empty slot is refused
(``empty_slot``). A sealed send/ready name is never a run_id and
never an intent. ``campaign_envelope_ready`` is structurally
distinct from ``send_authorized``; both are refused as
``sealed_effect``.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not occupy.

Not wired into the run store. Admitting a release or inspect is
not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized. Occupying
a slot is not a persist and not a send.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"occupy", "release", "inspect", "steal"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
OCCUPANCIES = frozenset({"empty", "held", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_start",
    "already_occupied",
    "empty_slot",
    "steal_forbidden",
    "malformed_id",
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
    """A slot class never authorizes a send. Structurally False."""
    return False


def halt_blocks_release() -> bool:
    """Structurally False. HALT stops STARTS, not release/inspect."""
    return False


def occupy_is_persist() -> bool:
    """Structurally False. Occupying a slot does not append a ledger row."""
    return False


def occupy_is_write() -> bool:
    """Structurally False. Occupancy is not a durable write."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A slot verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a slot is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def steals_slot() -> bool:
    """Structurally False. Steal is never admitted."""
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
    """Derive the slot-row status. Timeout outranks activity.

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
class SlotDecision:
    """The slot-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    status: str
    intended: str
    run_id: str
    occupancy: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "SlotDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a slot class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown slot status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.occupancy not in OCCUPANCIES:
            raise FailClosedError(
                f"unknown occupancy is not a refusal and not a grant: "
                f"{self.occupancy!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(self, "run_id", _require_name(self.run_id, what="run_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed slot must not carry a reason: {self.reason!r}")
            if self.intended == "occupy" and self.status != "VERIFIED":
                raise FailClosedError(
                    "SlotDecision cannot allow an occupy unless VERIFIED")
            if self.intended == "steal":
                raise FailClosedError(
                    "SlotDecision cannot allow steal")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.run_id) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "SlotDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_slot(
    *,
    intended: object,
    run_id: object,
    occupancy: object = "empty",
    activity: object = "idle",
    halted: object = False,
    timed_out: object = False,
) -> SlotDecision:
    """May this run slot be occupied, released, or inspected?

    ``intended`` and ``run_id`` are required. Unknown names fail
    closed — UNKNOWN is not FALSE and is not admitted as idle.

    ``halted`` and ``timed_out`` must be exact bools. HALT refuses
    ``occupy`` only. Timeout forces status UNKNOWN and refuses
    occupy; it does not classify the row as SUSPECTED.

    ``steal`` is always refused. Signature is sealed: no ``resend``,
    no ``send_authorized``. Tests lock the parameter list; the
    kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_run = _require_name(run_id, what="run_id")
    occupancy_name = _require_member(
        occupancy, what="occupancy", allowed=OCCUPANCIES)
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_intent) or _is_sealed(raw_run):
        return SlotDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            intended=raw_intent if raw_intent in INTENTS else "inspect",
            run_id=raw_run,
            occupancy=occupancy_name,
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if RUN_ID_RE.match(raw_run) is None:
        return SlotDecision(
            allowed=False,
            reason="malformed_id",
            status=status,
            intended=intent,
            run_id=raw_run,
            occupancy=occupancy_name,
            timed_out=timed_out,
        )

    if intent == "steal":
        return SlotDecision(
            allowed=False,
            reason="steal_forbidden",
            status=status,
            intended=intent,
            run_id=raw_run,
            occupancy=occupancy_name,
            timed_out=timed_out,
        )

    if intent == "occupy" and halted:
        return SlotDecision(
            allowed=False,
            reason="halt_start",
            status=status,
            intended=intent,
            run_id=raw_run,
            occupancy=occupancy_name,
            timed_out=timed_out,
        )

    if intent == "occupy" and occupancy_name == "held":
        return SlotDecision(
            allowed=False,
            reason="already_occupied",
            status=status,
            intended=intent,
            run_id=raw_run,
            occupancy=occupancy_name,
            timed_out=timed_out,
        )

    if intent == "release" and occupancy_name == "empty":
        return SlotDecision(
            allowed=False,
            reason="empty_slot",
            status=status,
            intended=intent,
            run_id=raw_run,
            occupancy=occupancy_name,
            timed_out=timed_out,
        )

    if intent == "occupy":
        if occupancy_name == "unknown":
            return SlotDecision(
                allowed=False,
                reason="unknown_activity",
                status="UNKNOWN",
                intended=intent,
                run_id=raw_run,
                occupancy=occupancy_name,
                timed_out=timed_out,
            )
        if status == "UNKNOWN":
            return SlotDecision(
                allowed=False,
                reason="unknown_activity",
                status=status,
                intended=intent,
                run_id=raw_run,
                occupancy=occupancy_name,
                timed_out=timed_out,
            )
        if status == "SUSPECTED":
            return SlotDecision(
                allowed=False,
                reason="suspected_concurrent",
                status=status,
                intended=intent,
                run_id=raw_run,
                occupancy=occupancy_name,
                timed_out=timed_out,
            )

    # release / inspect of a known occupancy, or a VERIFIED occupy of empty
    return SlotDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        run_id=raw_run,
        occupancy=occupancy_name,
        timed_out=timed_out,
    )
