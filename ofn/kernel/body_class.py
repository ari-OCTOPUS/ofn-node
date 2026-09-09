"""Body class — kernel-pure this-host presence admission.

``census_class`` grades a worktree census row. ``artifact_ref`` cites
a path plus digest without embedding a body. ``worktree`` inventory
tools live outside the kernel. This module is the third witness for
*presence class only*: is this body ON_THIS_HOST, NOT_ON_THIS_HOST,
or UNKNOWN?

A one-vantage disk miss is ``body_not_on_this_host``, never
``body_missing``. ``body_missing`` is a system-wide claim and
requires a second node. This classifier refuses that promotion.

A sealed send/ready name is never a body location.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not invent a body.

Not wired into the run store. Admitting a presence class is not
``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

HALT stops STARTS. This module has no halt parameter: classifying
a body is not a run start.

Kernel purity: dataclasses + typing. No I/O, no clock, no now(),
no hashlib of a body.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
CLASSES = frozenset({"ON_THIS_HOST", "NOT_ON_THIS_HOST", "UNKNOWN"})
REFUSAL_REASONS = frozenset({"sealed_effect", "missing_claim"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

_ON_THIS_HOST = frozenset({
    "on_this_host",
    "present_here",
})

_NOT_ON_THIS_HOST = frozenset({
    "not_on_this_host",
    "body_not_on_this_host",
    "absent_here",
})

_MISSING_CLAIM = frozenset({
    "body_missing",
    "missing",
    "gone",
})


def grants_send() -> bool:
    """A body class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not a classify."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_body_is_missing() -> bool:
    """Structurally False. UNKNOWN is not body_missing."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A presence class is not chattr +i."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a body is not an external effect."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This classifier is not wired into the store."""
    return False


def copies_canonical() -> bool:
    """Structurally False. A class does not copy a canonical document."""
    return False


def hashes_body() -> bool:
    """Structurally False. Presence admission does not hash a body."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A classify does not consume a key."""
    return False


def one_host_proves_missing() -> bool:
    """Structurally False. One vantage cannot mint body_missing."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if type(name) is not str:
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold(name) in {s.replace("-", "_") for s in _SEALED}


def _is_missing_claim(name: object) -> bool:
    if type(name) is not str:
        return False
    return _fold(name) in _MISSING_CLAIM


def classify_body(location: object) -> Optional[str]:
    """ON_THIS_HOST, NOT_ON_THIS_HOST, or UNKNOWN (None).

    Missing is UNKNOWN, not FALSE and not body_missing.
    A sealed send/ready name is not a body class.
    A one-vantage ``body_missing`` claim fails closed.
    Present-but-unknown tokens fail closed (shape error).
    """
    if location is None:
        return None
    if type(location) is not str:
        raise FailClosedError(
            f"body location must be a str or None: {location!r}")
    if not location.strip():
        raise FailClosedError("body location is empty")
    if _is_sealed(location):
        raise FailClosedError(
            f"body location names a sealed send/ready state: {location!r} — "
            "ready is not authorized")
    folded = _fold(location)
    if folded in _MISSING_CLAIM:
        raise FailClosedError(
            f"one vantage cannot mint body_missing: {location!r}")
    if folded in _ON_THIS_HOST:
        return "ON_THIS_HOST"
    if folded in _NOT_ON_THIS_HOST:
        return "NOT_ON_THIS_HOST"
    raise FailClosedError(
        f"body location is not a closed token: {location!r}")


@dataclass(frozen=True)
class BodyDecision:
    """The presence-class verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    body_class: str
    location: Optional[str]
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "BodyDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a body class is not a send")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be exact bool: {self.timed_out!r}")
        if self.body_class not in CLASSES:
            raise FailClosedError(
                f"unknown body class: {self.body_class!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed body must not carry a reason: {self.reason!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if self.location is not None:
            if type(self.location) is not str:
                raise FailClosedError(
                    f"location must be a str or None: {self.location!r}")
            if _is_sealed(self.location) and (
                    self.allowed or self.reason != "sealed_effect"):
                raise FailClosedError(
                    "BodyDecision cannot grant or mis-label a sealed "
                    "send/ready name")
            if _is_missing_claim(self.location) and (
                    self.allowed or self.reason != "missing_claim"):
                raise FailClosedError(
                    "body_missing may appear only as a missing_claim subject")
        if self.allowed and self.location is not None:
            if self.body_class in {"ON_THIS_HOST", "NOT_ON_THIS_HOST"}:
                if self.timed_out:
                    raise FailClosedError(
                        "timed-out classify cannot be a located class")
        if self.body_class == "ON_THIS_HOST" and self.location is None:
            raise FailClosedError("ON_THIS_HOST requires a recorded location")
        if self.body_class == "NOT_ON_THIS_HOST" and self.location is None:
            raise FailClosedError(
                "NOT_ON_THIS_HOST requires a recorded location")
        if self.location is not None and _is_sealed(self.location):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "sealed name may appear only as a sealed_effect subject")


def admit_body(
    location: object,
    *,
    timed_out: bool = False,
) -> BodyDecision:
    """May this value be recorded as a this-host presence class?

    Missing is UNKNOWN and admitted (so inventory can continue).
    A sealed send/ready name is a known refusal (``sealed_effect``).
    A one-vantage ``body_missing`` claim is a known refusal
    (``missing_claim``). A present unknown token fails closed —
    UNKNOWN is not FALSE and is not a forged location.

    Timeout forces UNKNOWN and does not prove concurrent writing.
    A valid token under timeout stays recorded; the class is UNKNOWN.

    Signature is sealed: no ``halt``, no ``send_authorized``, no
    ``resend``. Tests lock the parameter list.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be exact bool: {timed_out!r}")

    if _is_sealed(location):
        if type(location) is not str:
            raise FailClosedError(f"sealed location must be a str: {location!r}")
        return BodyDecision(
            allowed=False,
            reason="sealed_effect",
            body_class="UNKNOWN",
            location=location,
            timed_out=timed_out,
        )

    if _is_missing_claim(location):
        if type(location) is not str:
            raise FailClosedError(
                f"missing-claim location must be a str: {location!r}")
        return BodyDecision(
            allowed=False,
            reason="missing_claim",
            body_class="UNKNOWN",
            location=location,
            timed_out=timed_out,
        )

    if location is None:
        return BodyDecision(
            allowed=True,
            reason=None,
            body_class="UNKNOWN",
            location=None,
            timed_out=timed_out,
        )

    klass = classify_body(location)
    if klass is None:
        return BodyDecision(
            allowed=True,
            reason=None,
            body_class="UNKNOWN",
            location=None,
            timed_out=timed_out,
        )
    if timed_out:
        return BodyDecision(
            allowed=True,
            reason=None,
            body_class="UNKNOWN",
            location=location if type(location) is str else None,
            timed_out=True,
        )
    return BodyDecision(
        allowed=True,
        reason=None,
        body_class=klass,
        location=location if type(location) is str else None,
        timed_out=False,
    )


def try_classify(location: object) -> Optional[str]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    return classify_body(location)
