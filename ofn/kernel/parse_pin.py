"""Parse pin — first field-split of a FORMAT_FIT identifier.

``format_class`` classifies a shape. This module is the complementary
pin: record a FIRST parse of a classified fit into ``stem`` +
``body``. A second parse of the same (family, value) is
``already_parsed``. Peek never writes.

``parse`` is a START. HALT refuses it. ``peek`` is not a START —
HALT does not block it. A string that is not FORMAT_FIT cannot be
pinned (``not_fit``). Timeout is UNKNOWN. It does not prove
concurrent writing and it does not mint.

A sealed send/ready name is never a parse. ``campaign_envelope_ready``
is structurally distinct from ``send_authorized``; both are refused
as ``sealed_effect``.

Not wired into the run store. Pinning a parse is not
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.
Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .format_class import (
    FAMILIES,
    classify_format,
    classify_timeout,
)

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"parse", "peek"})
STATUSES = frozenset({"PARSED", "UNKNOWN"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_active",
    "already_parsed",
    "not_fit",
    "unknown_shape",
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
    """A parse pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_peek() -> bool:
    """Structurally False. HALT stops STARTS, not peek."""
    return False


def mints_run_id() -> bool:
    """Structurally False. Parsing does not mint."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A parse pin is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Pinning a parse is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def already_parsed_is_first() -> bool:
    """Structurally False. A second parse is not the first pin."""
    return False


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


def split_fit(*, family: str, value: str) -> tuple[str, str]:
    """Split a FORMAT_FIT string. Caller must have classified first.

    ``digest`` has no stem. ``run_id`` / ``event_id`` split on the
    first hyphen. Unknown family fail-closes.
    """
    family_name = _require_member(family, what="family", allowed=FAMILIES)
    text = _require_name(value, what="value")
    if family_name == "digest":
        return "", text
    stem, _sep, body = text.partition("-")
    if not _sep or not body:
        raise FailClosedError(
            f"FORMAT_FIT {family_name} refused to split: {text!r}")
    return stem, body


@dataclass(frozen=True)
class ParsePin:
    """The first-parse pin. ``grants_send`` is structurally False.

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
    stem: str
    body: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "ParsePin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a parse pin is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown parse status is not a refusal and not a grant: "
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
        if type(self.stem) is not str or type(self.body) is not str:
            raise FailClosedError("stem and body must be str")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed parse must not carry a reason: {self.reason!r}")
            if self.intended == "parse" and self.status != "PARSED":
                raise FailClosedError(
                    "ParsePin cannot allow a parse unless PARSED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.family) or _is_sealed(self.intended) or _is_sealed(self.stem) or _is_sealed(self.body):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "ParsePin cannot grant or mis-label a sealed "
                    "send/ready name")


def pin_parse(
    *,
    intended: object,
    family: object,
    value: object,
    prior_parsed: object = False,
    halted: object = False,
    timed_out: object = False,
) -> ParsePin:
    """May this parse action pin stem+body for this family and value?

    ``intended`` and ``family`` are required names. Unknown names
    fail closed — UNKNOWN is not FALSE and is not a first parse.

    ``prior_parsed``, ``halted``, and ``timed_out`` must be exact
    bools. Timeout forces status UNKNOWN. It does not classify a
    race and it does not count as ``already_parsed``.

    ``parse`` is a START: HALT refuses it. ``peek`` continues.
    ``prior_parsed=True`` refuses as ``already_parsed``.
    A non-fit string refuses as ``not_fit``.
    Sealed send/ready names refuse (``sealed_effect``).

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_family = _require_name(family, what="family")
    if type(prior_parsed) is not bool:
        raise FailClosedError(
            f"prior_parsed must be an exact bool: {prior_parsed!r}")
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_intent) or _is_sealed(raw_family) or _is_sealed(value):
        return ParsePin(
            allowed=False,
            reason="sealed_effect",
            status="UNKNOWN",
            intended=raw_intent if raw_intent in INTENTS else "peek",
            family=raw_family if raw_family in FAMILIES else "digest",
            stem="",
            body="",
            timed_out=timed_out,
        )

    intent_name = _require_member(raw_intent, what="intended", allowed=INTENTS)
    family_name = _require_member(raw_family, what="family", allowed=FAMILIES)

    if intent_name == "parse" and halted:
        return ParsePin(
            allowed=False,
            reason="halt_active",
            status="UNKNOWN",
            intended=intent_name,
            family=family_name,
            stem="",
            body="",
            timed_out=timed_out,
        )

    if timed_out:
        return ParsePin(
            allowed=intent_name == "peek",
            reason=None if intent_name == "peek" else "unknown_shape",
            status="UNKNOWN",
            intended=intent_name,
            family=family_name,
            stem="",
            body="",
            timed_out=True,
        )

    if prior_parsed:
        return ParsePin(
            allowed=False,
            reason="already_parsed",
            status="UNKNOWN",
            intended=intent_name,
            family=family_name,
            stem="",
            body="",
            timed_out=False,
        )

    shape = classify_format(family=family_name, value=value, timed_out=False)
    if shape != "FORMAT_FIT":
        return ParsePin(
            allowed=False,
            reason="not_fit",
            status="UNKNOWN",
            intended=intent_name,
            family=family_name,
            stem="",
            body="",
            timed_out=False,
        )

    text = _require_name(value, what="value")
    stem, body = split_fit(family=family_name, value=text)
    if intent_name == "peek":
        return ParsePin(
            allowed=True,
            reason=None,
            status="UNKNOWN",
            intended=intent_name,
            family=family_name,
            stem=stem,
            body=body,
            timed_out=False,
        )
    return ParsePin(
        allowed=True,
        reason=None,
        status="PARSED",
        intended=intent_name,
        family=family_name,
        stem=stem,
        body=body,
        timed_out=False,
    )


# Re-export so chaos tests can name the timeout rule from one pin module.
timeout_is_unknown = classify_timeout
