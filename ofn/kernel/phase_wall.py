"""Phase wall — kernel-pure wall between ready and authorized.

``campaign_envelope_ready`` is a named revenue-path phase. It is not
``send_authorized`` and it is not ``quote_sent``. Classifying or
advancing to ready is admitted. Advancing to a send name is refused.

A later hold outranks an older authorization: a send-band name under
``later_hold`` is refused as ``later_hold``, not granted. Ready stays
admitted while held.

Unknown phase names fail closed — UNKNOWN is not FALSE and is not a
send. Sealed send names are a known refusal (``sealed_effect``), not
an unknown.

HALT stops STARTS. This module has no halt parameter: a phase
decision is not a run start.

Not wired into the run store (that file is owned by an open change).

Admitting ready is not ``send_authorized`` and not ``quote_sent``.
Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError

# Closed band vocabulary. Widen only with a test.
BANDS = frozenset({"ready", "send"})

# Closed intent vocabulary. "1" / True / "true" are UNKNOWN, not advance.
INTENTS = frozenset({"classify", "advance"})

# Known refusals. Unknown names fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({"sealed_effect", "later_hold"})

_READY = frozenset({
    "campaign_envelope_ready",
    "quote_drafted",
    "campaign-envelope-ready",
    "quote-drafted",
})

_SEND = frozenset({
    "send_authorized",
    "quote_sent",
    "send-authorized",
    "quote-sent",
})


def grants_send() -> bool:
    """A phase wall never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A wall cannot re-arm a later hold."""
    return False


def halt_blocks_phase() -> bool:
    """Structurally False. HALT stops STARTS, not phase classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Admission is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming a phase is not an external effect."""
    return False


def ready_equals_authorized() -> bool:
    """Structurally False. The two names are not aliases."""
    return False


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def classify_band(name: object) -> str:
    """Return the phase band, or fail closed.

    Unknown names are not classified as send and are not FALSE.
    A send-band name is a known band (then refused on admit), not
    an unknown.
    """
    phase = _require_name(name, what="phase")
    folded = _fold(phase)
    ready_fold = {_fold(n) for n in _READY}
    send_fold = {_fold(n) for n in _SEND}
    if folded in ready_fold:
        return "ready"
    if folded in send_fold:
        return "send"
    raise FailClosedError(
        f"unknown phase name is not a refusal and not a grant: {phase!r}")


@dataclass(frozen=True)
class PhaseDecision:
    """The phase-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``. Ready and authorized stay different names.
    """

    allowed: bool
    reason: Optional[str]
    band: str
    name: str
    intended: str
    later_hold: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "PhaseDecision cannot grant send_authorized / quote_sent — "
                "a phase wall is not a send")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.later_hold) is not bool:
            raise FailClosedError(
                f"later_hold must be an exact bool: {self.later_hold!r}")
        if self.band not in BANDS:
            raise FailClosedError(
                f"unknown band is not a grant: {self.band!r}")
        object.__setattr__(self, "name", _require_name(self.name, what="phase"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed phase must not carry a reason: {self.reason!r}")
            if self.band != "ready":
                raise FailClosedError(
                    "PhaseDecision cannot allow a send-band name")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
            if self.band == "ready":
                raise FailClosedError(
                    "PhaseDecision cannot refuse a ready-band name — "
                    "ready is held, not sealed")


def admit_phase(
    *,
    name: object,
    intended: object,
    later_hold: object = False,
) -> PhaseDecision:
    """May this phase name be classified or advanced?

    ``name`` and ``intended`` are required. Unknown names and unknown
    intents fail closed — UNKNOWN is not FALSE and is not admitted.

    ``later_hold`` must be an exact bool. A send-band name under a
    later hold is ``later_hold``; without it, ``sealed_effect``.
    Ready-band names stay admitted either way.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    phase = _require_name(name, what="phase")
    if isinstance(intended, bool) or not isinstance(intended, str):
        raise FailClosedError(f"intended must be a name: {intended!r}")
    intent = intended.strip()
    if intent not in INTENTS:
        raise FailClosedError(
            f"unknown intended is not a refusal and not a grant: {intended!r}")
    if type(later_hold) is not bool:
        raise FailClosedError(
            f"later_hold must be an exact bool: {later_hold!r}")

    band = classify_band(phase)
    if band == "send":
        reason = "later_hold" if later_hold else "sealed_effect"
        return PhaseDecision(
            allowed=False,
            reason=reason,
            band=band,
            name=phase,
            intended=intent,
            later_hold=later_hold,
        )
    return PhaseDecision(
        allowed=True,
        reason=None,
        band=band,
        name=phase,
        intended=intent,
        later_hold=later_hold,
    )
