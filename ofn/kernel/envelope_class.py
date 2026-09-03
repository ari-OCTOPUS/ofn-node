"""Envelope class — kernel-pure TaskEnvelope mint/validate/replay admission.

``create_envelope`` (envelope.py) is the factory. This module is the
third witness: may a proposed mint, a validate of an already-minted
envelope, or a replay of a recorded envelope proceed?

``mint`` is a START. HALT refuses it. ``validate`` and ``replay`` are
not STARTS — HALT does not block them. This module does not mint a
run_id and does not write a ledger.

A sealed send/ready name is never a run_id and never an intent.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not mint.

Unknown version is not FALSE and is not a grant — it fails closed
or is refused as ``unknown_version``. Version must be exact int 1.

Not wired into the run store. Admitting a validate or replay is not
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.
Ready is not authorized.

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
INTENTS = frozenset({"mint", "validate", "replay"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_active",
    "unknown_version",
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

SUPPORTED_VERSION = 1


def grants_send() -> bool:
    """An envelope class never authorizes a send. Structurally False."""
    return False


def halt_blocks_validate() -> bool:
    """Structurally False. HALT stops STARTS, not validate/replay."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This classifies."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. An envelope verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying an envelope is not an external effect."""
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


def classify_status(*, activity: str, timed_out: bool) -> str:
    """Derive the envelope-row status. Timeout outranks activity.

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
class EnvelopeDecision:
    """The envelope-admission verdict. ``grants_send`` is structurally False.

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
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "EnvelopeDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — an envelope class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown envelope status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(self, "run_id", _require_name(self.run_id, what="run_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed envelope must not carry a reason: {self.reason!r}")
            if self.intended == "mint" and self.status != "VERIFIED":
                raise FailClosedError(
                    "EnvelopeDecision cannot allow a mint unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.run_id) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "EnvelopeDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_envelope(
    *,
    intended: object,
    version: object,
    run_id: object,
    activity: object = "idle",
    halted: object = False,
    timed_out: object = False,
) -> EnvelopeDecision:
    """May this envelope be minted, validated, or replayed?

    ``intended``, ``version``, and ``run_id`` are required.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as idle.

    ``version`` must be exact int ``1``. Bool/str/float fail closed.
    Any other int is refused as ``unknown_version``.

    ``halted`` and ``timed_out`` must be exact bools. HALT refuses
    ``mint`` only. Timeout forces status UNKNOWN and refuses mint;
    it does not classify the row as SUSPECTED.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_run = _require_name(run_id, what="run_id")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    if type(version) is not int:
        raise FailClosedError(
            f"version must be an exact int: {version!r}")

    if _is_sealed(raw_intent) or _is_sealed(raw_run):
        return EnvelopeDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            intended=raw_intent if raw_intent in INTENTS else "validate",
            run_id=raw_run,
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if version != SUPPORTED_VERSION:
        return EnvelopeDecision(
            allowed=False,
            reason="unknown_version",
            status=status,
            intended=intent,
            run_id=raw_run,
            timed_out=timed_out,
        )

    if RUN_ID_RE.match(raw_run) is None:
        return EnvelopeDecision(
            allowed=False,
            reason="malformed_id",
            status=status,
            intended=intent,
            run_id=raw_run,
            timed_out=timed_out,
        )

    if intent == "mint" and halted:
        return EnvelopeDecision(
            allowed=False,
            reason="halt_active",
            status=status,
            intended=intent,
            run_id=raw_run,
            timed_out=timed_out,
        )

    if intent == "mint":
        if status == "UNKNOWN":
            return EnvelopeDecision(
                allowed=False,
                reason="unknown_activity",
                status=status,
                intended=intent,
                run_id=raw_run,
                timed_out=timed_out,
            )
        if status == "SUSPECTED":
            return EnvelopeDecision(
                allowed=False,
                reason="suspected_concurrent",
                status=status,
                intended=intent,
                run_id=raw_run,
                timed_out=timed_out,
            )

    # validate / replay, or a VERIFIED mint
    return EnvelopeDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        run_id=raw_run,
        timed_out=timed_out,
    )
