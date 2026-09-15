"""Version class — kernel-pure typed-envelope version admission.

``create_envelope`` (envelope.py) and ``admit_envelope``
(envelope_class.py) already require exact int ``1``. This module
is a third witness that talks *only* about the version number:
may a supplied schema version be classified, and may it be
admitted as the run's schema?

``admit`` is a START. HALT refuses it. ``classify`` is not a
START — HALT does not block it. This module does not mint a
run_id, does not rewrite ``SUPPORTED_VERSION``, and does not
write a ledger.

A sealed send/ready name is never a version and never an
intent. ``campaign_envelope_ready`` is structurally distinct
from ``send_authorized``; both are refused as ``sealed_effect``.

Missing version is UNKNOWN, not 0 and not FALSE. Bool / str /
float fail closed — ``int(True)`` is not a schema version.
Any other exact int is ``UNKNOWN_VERSION``, not FALSE.

Timeout is UNKNOWN. It does not prove concurrent writing and
it does not admit.

Not wired into the run store. Classifying or admitting a
version is not ``send_authorized``, ``quote_sent``, or
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
INTENTS = frozenset({"classify", "admit"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
VERSION_CLASSES = frozenset({"SUPPORTED", "UNKNOWN_VERSION", "UNKNOWN"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_active",
    "unknown_version",
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
    """A version class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not classify."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This classifies."""
    return False


def rewrites_supported_version() -> bool:
    """Structurally False. Supported stays exact int 1."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A version verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_version_is_false() -> bool:
    """Structurally False. UNKNOWN_VERSION is a class, not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a version is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def copies_envelope_class() -> bool:
    """Structurally False. This witness does not import envelope_class."""
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
    """Derive the version-row status. Timeout outranks activity.

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


def classify_version(value: object) -> str:
    """Name one supplied schema version. Missing is UNKNOWN, not 0.

    Exact int ``1`` is SUPPORTED. Any other exact int is
    UNKNOWN_VERSION — a class, not FALSE. Bool / str / float fail
    closed. A sealed send/ready name is not a version.
    """
    if value is None:
        return "UNKNOWN"
    if _is_sealed(value):
        raise FailClosedError(
            f"version names a sealed send/ready state: {value!r}")
    if type(value) is not int:
        raise FailClosedError(
            f"version must be an exact int or None: {value!r}")
    if value == SUPPORTED_VERSION:
        return "SUPPORTED"
    return "UNKNOWN_VERSION"


@dataclass(frozen=True)
class VersionDecision:
    """The version-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    status: str
    intended: str
    version_class: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "VersionDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a version class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown version status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.version_class not in VERSION_CLASSES:
            raise FailClosedError(
                f"unknown version_class is not a refusal and not a grant: "
                f"{self.version_class!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed version must not carry a reason: {self.reason!r}")
            if self.intended == "admit" and self.status != "VERIFIED":
                raise FailClosedError(
                    "VersionDecision cannot allow an admit unless VERIFIED")
            if self.intended == "admit" and self.version_class != "SUPPORTED":
                raise FailClosedError(
                    "VersionDecision cannot allow an admit unless SUPPORTED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "VersionDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_version(
    *,
    intended: object,
    version: object,
    activity: object = "idle",
    halted: object = False,
    timed_out: object = False,
) -> VersionDecision:
    """May this schema version be classified or admitted?

    ``intended`` is required. Unknown names fail closed — UNKNOWN
    is not FALSE and is not admitted as idle.

    ``version`` may be ``None`` (UNKNOWN) or exact int. Bool / str
    / float fail closed. Exact int ``1`` is SUPPORTED. Any other
    exact int is UNKNOWN_VERSION.

    ``halted`` and ``timed_out`` must be exact bools. HALT refuses
    ``admit`` only. Timeout forces status UNKNOWN and refuses
    admit; it does not classify the row as SUSPECTED.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")

    if _is_sealed(raw_intent) or _is_sealed(version):
        return VersionDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            intended=raw_intent if raw_intent in INTENTS else "classify",
            version_class=classify_version(None) if _is_sealed(version) else (
                classify_version(version) if version is None or type(version) is int
                else "UNKNOWN"
            ),
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    klass = classify_version(version)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if intent == "classify":
        return VersionDecision(
            allowed=True,
            reason=None,
            status=status,
            intended=intent,
            version_class=klass,
            timed_out=timed_out,
        )

    # intent == admit (START)
    if klass != "SUPPORTED":
        return VersionDecision(
            allowed=False,
            reason="unknown_version",
            status=status,
            intended=intent,
            version_class=klass,
            timed_out=timed_out,
        )
    if halted:
        return VersionDecision(
            allowed=False,
            reason="halt_active",
            status=status,
            intended=intent,
            version_class=klass,
            timed_out=timed_out,
        )
    if status == "UNKNOWN":
        return VersionDecision(
            allowed=False,
            reason="unknown_activity",
            status=status,
            intended=intent,
            version_class=klass,
            timed_out=timed_out,
        )
    if status == "SUSPECTED":
        return VersionDecision(
            allowed=False,
            reason="suspected_concurrent",
            status=status,
            intended=intent,
            version_class=klass,
            timed_out=timed_out,
        )
    return VersionDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        version_class=klass,
        timed_out=timed_out,
    )
