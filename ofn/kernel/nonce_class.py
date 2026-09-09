"""Nonce class — kernel-pure one-shot token admission.

``event_id`` mints ``evt-`` identities. ``dedup`` tracks ``(kind, ref)``.
``idempotency`` hashes an envelope contract. This module is the fourth
witness: may a caller-supplied one-shot token be presented for a
named intent?

``admit`` is a START. HALT refuses it. ``replay_check`` is not a
START — HALT does not block it. This module does not consume the
token and does not write a ledger. Consumption is ``once_pin``.

A sealed send/ready name is never a nonce and never a run_id.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not consume.

Unknown format is not FALSE and is not a grant — it is refused as
``malformed_nonce``. Format is ``nce-`` + sixteen lowercase hex.

Not wired into the run store. Admitting a replay_check is not
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.
Ready is not authorized.

Kernel purity: typing + dataclasses + re. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"admit", "replay_check"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_active",
    "malformed_nonce",
    "malformed_id",
    "unknown_activity",
    "suspected_concurrent",
})

NONCE_RE = re.compile(r"^nce-[a-f0-9]{16}$")

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A nonce class never authorizes a send. Structurally False."""
    return False


def halt_blocks_replay_check() -> bool:
    """Structurally False. HALT stops STARTS, not replay_check."""
    return False


def consumes_nonce() -> bool:
    """Structurally False. Classification does not burn the token."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A nonce verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a nonce is not an external effect."""
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


def require_nonce(value: object, *, what: str = "nonce") -> str:
    """Validate a caller-supplied one-shot token. Fail closed otherwise."""
    name = _require_name(value, what=what)
    if _is_sealed(name):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {name!r}")
    if NONCE_RE.match(name) is None:
        raise FailClosedError(f"{what} not caller-shaped: {name!r}")
    return name


def classify_status(*, activity: str, timed_out: bool) -> str:
    """Derive the nonce-row status. Timeout outranks activity.

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
class NonceDecision:
    """The nonce-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    status: str
    intended: str
    nonce: str
    run_id: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "NonceDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a nonce class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown nonce status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(self, "nonce", _require_name(self.nonce, what="nonce"))
        object.__setattr__(self, "run_id", _require_name(self.run_id, what="run_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed nonce must not carry a reason: {self.reason!r}")
            if self.intended == "admit" and self.status != "VERIFIED":
                raise FailClosedError(
                    "NonceDecision cannot allow an admit unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.nonce) or _is_sealed(self.run_id) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "NonceDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_nonce(
    *,
    intended: object,
    nonce: object,
    run_id: object,
    activity: object = "idle",
    halted: object = False,
    timed_out: object = False,
) -> NonceDecision:
    """May this one-shot token be presented for admit or replay_check?

    ``intended``, ``nonce``, and ``run_id`` are required.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as idle.

    ``halted`` and ``timed_out`` must be exact bools. HALT refuses
    ``admit`` only. Timeout forces status UNKNOWN and refuses admit;
    it does not classify the row as SUSPECTED.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_nonce = _require_name(nonce, what="nonce")
    raw_run = _require_name(run_id, what="run_id")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_intent) or _is_sealed(raw_nonce) or _is_sealed(raw_run):
        return NonceDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            intended=raw_intent if raw_intent in INTENTS else "replay_check",
            nonce=raw_nonce,
            run_id=raw_run,
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if NONCE_RE.match(raw_nonce) is None:
        return NonceDecision(
            allowed=False,
            reason="malformed_nonce",
            status=status,
            intended=intent,
            nonce=raw_nonce,
            run_id=raw_run,
            timed_out=timed_out,
        )

    if RUN_ID_RE.match(raw_run) is None:
        return NonceDecision(
            allowed=False,
            reason="malformed_id",
            status=status,
            intended=intent,
            nonce=raw_nonce,
            run_id=raw_run,
            timed_out=timed_out,
        )

    if intent == "admit" and halted:
        return NonceDecision(
            allowed=False,
            reason="halt_active",
            status=status,
            intended=intent,
            nonce=raw_nonce,
            run_id=raw_run,
            timed_out=timed_out,
        )

    if intent == "admit":
        if status == "UNKNOWN":
            return NonceDecision(
                allowed=False,
                reason="unknown_activity",
                status=status,
                intended=intent,
                nonce=raw_nonce,
                run_id=raw_run,
                timed_out=timed_out,
            )
        if status == "SUSPECTED":
            return NonceDecision(
                allowed=False,
                reason="suspected_concurrent",
                status=status,
                intended=intent,
                nonce=raw_nonce,
                run_id=raw_run,
                timed_out=timed_out,
            )

    return NonceDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        nonce=raw_nonce,
        run_id=raw_run,
        timed_out=timed_out,
    )
