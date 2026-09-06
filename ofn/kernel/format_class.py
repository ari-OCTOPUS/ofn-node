"""Format class — kernel-pure identifier-shape admission.

``envelope.py`` validates a run_id and fail-closes. ``event_id.py``
validates an event_id and fail-closes. ``receipt_bind`` fail-closes a
forged digest. This module is the complementary witness: may a
caller-supplied string be *classified* as a known family shape
without minting, validating-as-grant, or writing the store?

``classify`` is a START. HALT refuses it. ``inspect`` is not a
START — HALT does not block it. Malformed or missing is UNKNOWN,
not FALSE. A sealed send/ready name is never a format fit.

``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not mint.

Not wired into the run store. Classifying a shape is not
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.
Ready is not authorized.

Kernel purity: typing + dataclasses + re (via envelope / event_id).
No json, no clock, no I/O. This file must not name a business or
product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import RUN_ID_RE, SHA256_HEX_RE
from .errors import FailClosedError
from .event_id import EVENT_ID_RE
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
FAMILIES = frozenset({"run_id", "event_id", "digest"})
INTENTS = frozenset({"classify", "inspect"})
STATUSES = frozenset({"FORMAT_FIT", "UNKNOWN"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_active",
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
    """A format class never authorizes a send. Structurally False."""
    return False


def halt_blocks_inspect() -> bool:
    """Structurally False. HALT stops STARTS, not inspect."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This classifies."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A format verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a shape is not an external effect."""
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


def classify_format(
    *,
    family: object,
    value: object,
    timed_out: object = False,
) -> str:
    """Classify a caller-supplied string against one closed family.

    Timeout outranks the bytes: UNKNOWN, not FALSE, not a race.
    Missing / non-str / empty / sealed / mismatch → UNKNOWN.
    Unknown family fail-closes — that is not a shape verdict.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be an exact bool: {timed_out!r}")
    family_name = _require_member(family, what="family", allowed=FAMILIES)
    if timed_out:
        return "UNKNOWN"
    if _is_sealed(value) or _is_sealed(family_name):
        return "UNKNOWN"
    if not isinstance(value, str) or not value.strip():
        return "UNKNOWN"
    text = value.strip()
    if family_name == "run_id" and RUN_ID_RE.match(text):
        return "FORMAT_FIT"
    if family_name == "event_id" and EVENT_ID_RE.match(text):
        return "FORMAT_FIT"
    if family_name == "digest" and SHA256_HEX_RE.match(text):
        return "FORMAT_FIT"
    return "UNKNOWN"


@dataclass(frozen=True)
class FormatDecision:
    """The format-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    status: str
    intended: str
    family: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "FormatDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a format class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown format status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.family not in FAMILIES:
            raise FailClosedError(
                f"unknown or missing family: {self.family!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed format must not carry a reason: {self.reason!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.family) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "FormatDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_format(
    *,
    intended: object,
    family: object,
    value: object,
    halted: object = False,
    timed_out: object = False,
) -> FormatDecision:
    """May this format action hit this family and value?

    ``intended`` and ``family`` are required names. Unknown names
    fail closed — UNKNOWN is not FALSE and is not admitted as a fit.

    ``halted`` and ``timed_out`` must be exact bools. Timeout
    forces status UNKNOWN. It does not classify a race.

    ``classify`` is a START: HALT refuses it. ``inspect`` continues.
    Sealed send/ready names refuse (``sealed_effect``).

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_family = _require_name(family, what="family")
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_intent) or _is_sealed(raw_family) or _is_sealed(value):
        return FormatDecision(
            allowed=False,
            reason="sealed_effect",
            status="UNKNOWN",
            intended="inspect" if raw_intent not in INTENTS else raw_intent,
            family="digest" if raw_family not in FAMILIES else raw_family,
            timed_out=timed_out,
        )

    intent_name = _require_member(raw_intent, what="intended", allowed=INTENTS)
    family_name = _require_member(raw_family, what="family", allowed=FAMILIES)

    if intent_name == "classify" and halted:
        return FormatDecision(
            allowed=False,
            reason="halt_active",
            status="UNKNOWN",
            intended=intent_name,
            family=family_name,
            timed_out=timed_out,
        )

    status = classify_format(
        family=family_name, value=value, timed_out=timed_out)
    return FormatDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent_name,
        family=family_name,
        timed_out=timed_out,
    )
