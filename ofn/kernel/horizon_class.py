"""Horizon class — kernel-pure TaskEnvelope validity-horizon admission.

``deadline_window`` answers ``now < deadline`` and treats equal as
closed (False). This module answers a different question: given a
named horizon kind and two caller-supplied epochs, what is the
position, and may an admit proceed?

Positions:

  inside   — now < horizon
  at_edge  — now == horizon  (UNKNOWN, not a grant, not False)
  past     — now > horizon
  unknown  — missing now, missing horizon, or timed_out

``at_edge`` is the load-bearing distinction from deadline_window:
equal is UNKNOWN, not closed-as-False.

``admit`` of ``mint`` when past, at_edge, or unknown is refused.
``admit`` of validate/replay/store_append/receipt_bind when past
is refused as ``past_horizon``; at_edge and unknown refuse as
``unknown_horizon`` (not as past, not as False). ``classify``
always returns a decision and is not a START.

HALT refuses mint admit only. Classify continues under HALT.

A sealed send/ready name is never a horizon kind and never an
intent. ``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not mint. 0 is a measured epoch, not UNKNOWN.

Not wired into the run store. Admitting a classify or a
validate/replay is not ``send_authorized``, ``quote_sent``, or
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
HORIZON_KINDS = frozenset({
    "mint", "validate", "replay", "store_append", "receipt_bind",
})
INTENTS = frozenset({"classify", "admit"})
POSITIONS = frozenset({"inside", "at_edge", "past", "unknown"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_active",
    "past_horizon",
    "unknown_horizon",
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
    """A horizon class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not classify."""
    return False


def halt_blocks_inflight_admit() -> bool:
    """Structurally False. HALT stops mint admit, not validate/replay."""
    return False


def equal_is_closed() -> bool:
    """Structurally False. Equal is at_edge / UNKNOWN, not closed-as-False.

    That is the distinction from deadline_window.window_open.
    """
    return False


def mints_run_id() -> bool:
    """Structurally False. This classifies a horizon; it does not mint."""
    return False


def copies_deadline_window() -> bool:
    """Structurally False. Complementary; does not import deadline_window."""
    return False


def copies_ttl_class() -> bool:
    """Structurally False. Distinct from unpublished ttl_class / expire_pin."""
    return False


def copies_stale_class() -> bool:
    """Structurally False. Distinct from stale_class / fresh_pin."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A horizon verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_epoch_is_zero() -> bool:
    """Structurally False. Missing epoch is UNKNOWN, not 0."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a horizon is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
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


def _require_epoch(value: object, *, what: str) -> Optional[int]:
    """Exact int or None for UNKNOWN. Bool/str/float fail closed.

    ``None`` is UNKNOWN, not 0. ``0`` is a measured epoch.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"{what} must be exact int or None: {value!r}")
    return value


def classify_position(
    *,
    now_epoch_s: Optional[int],
    horizon_epoch_s: Optional[int],
    timed_out: bool,
) -> str:
    """Derive the horizon position. Timeout outranks the comparison.

    A timeout is UNKNOWN even when both epochs are present and
    would otherwise say inside / at_edge / past.
    """
    if timed_out:
        return "unknown"
    if now_epoch_s is None or horizon_epoch_s is None:
        return "unknown"
    if now_epoch_s < horizon_epoch_s:
        return "inside"
    if now_epoch_s == horizon_epoch_s:
        return "at_edge"
    return "past"


def classify_status(*, activity: str, timed_out: bool) -> str:
    """Derive the horizon-row status. Timeout outranks activity.

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
class HorizonDecision:
    """The horizon-admission verdict. ``grants_send`` is structurally False.

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
    position: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "HorizonDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a horizon class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown horizon status is not a refusal and not a grant: "
                f"{self.status!r}")
        sealed_row = _is_sealed(self.kind) or _is_sealed(self.intended)
        if self.intended not in INTENTS and not sealed_row:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.kind not in HORIZON_KINDS and not sealed_row:
            raise FailClosedError(
                f"unknown or missing kind: {self.kind!r}")
        if self.position not in POSITIONS:
            raise FailClosedError(
                f"unknown or missing position: {self.position!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed horizon must not carry a reason: {self.reason!r}")
            if self.intended == "admit" and self.position != "inside":
                raise FailClosedError(
                    "HorizonDecision cannot allow an admit unless inside")
            if self.intended == "admit" and self.status != "VERIFIED":
                raise FailClosedError(
                    "HorizonDecision cannot allow an admit unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.kind) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "HorizonDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_horizon(
    *,
    intended: object,
    kind: object,
    now_epoch_s: object = None,
    horizon_epoch_s: object = None,
    activity: object = "idle",
    halted: object = False,
    timed_out: object = False,
) -> HorizonDecision:
    """May this horizon be classified or admitted?

    ``intended`` and ``kind`` are required names. Unknown names fail
    closed — UNKNOWN is not FALSE and is not admitted as idle.

    ``now_epoch_s`` and ``horizon_epoch_s`` are exact ints or None.
    None is UNKNOWN, not 0. Bool/str/float fail closed.

    ``halted`` and ``timed_out`` must be exact bools. HALT refuses
    ``admit`` of ``mint`` only. Timeout forces position unknown and
    status UNKNOWN; it does not classify the row as SUSPECTED.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_kind = _require_name(kind, what="kind")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    now = _require_epoch(now_epoch_s, what="now_epoch_s")
    horizon = _require_epoch(horizon_epoch_s, what="horizon_epoch_s")

    if _is_sealed(raw_intent) or _is_sealed(raw_kind):
        return HorizonDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            intended=raw_intent,
            kind=raw_kind,
            position=classify_position(
                now_epoch_s=now, horizon_epoch_s=horizon, timed_out=timed_out),
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    kind_name = _require_member(raw_kind, what="kind", allowed=HORIZON_KINDS)
    status = classify_status(activity=activity_name, timed_out=timed_out)
    position = classify_position(
        now_epoch_s=now, horizon_epoch_s=horizon, timed_out=timed_out)

    if intent == "classify":
        return HorizonDecision(
            allowed=True,
            reason=None,
            status=status,
            intended=intent,
            kind=kind_name,
            position=position,
            timed_out=timed_out,
        )

    # intent == admit
    if kind_name == "mint" and halted:
        return HorizonDecision(
            allowed=False,
            reason="halt_active",
            status=status,
            intended=intent,
            kind=kind_name,
            position=position,
            timed_out=timed_out,
        )
    if position == "past":
        return HorizonDecision(
            allowed=False,
            reason="past_horizon",
            status=status,
            intended=intent,
            kind=kind_name,
            position=position,
            timed_out=timed_out,
        )
    if position in {"unknown", "at_edge"}:
        return HorizonDecision(
            allowed=False,
            reason="unknown_horizon",
            status=status,
            intended=intent,
            kind=kind_name,
            position=position,
            timed_out=timed_out,
        )
    if status == "UNKNOWN":
        return HorizonDecision(
            allowed=False,
            reason="unknown_activity",
            status=status,
            intended=intent,
            kind=kind_name,
            position=position,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return HorizonDecision(
            allowed=False,
            reason="suspected_concurrent",
            status=status,
            intended=intent,
            kind=kind_name,
            position=position,
            timed_out=timed_out,
        )
    return HorizonDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        kind=kind_name,
        position=position,
        timed_out=timed_out,
    )
