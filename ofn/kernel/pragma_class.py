"""Pragma class — kernel-pure durability-setting admission.

``journal_mode=WAL`` is admitted. DELETE / TRUNCATE / PERSIST /
MEMORY / OFF are refused. ``synchronous=FULL`` is admitted.
EXTRA is admitted because it is stricter than FULL. NORMAL and
OFF are refused: WAL plus NORMAL is not durable across power
loss, and OFF drops the durability the store exists to keep.

Unknown pragma names classify as UNKNOWN and fail closed on
apply. UNKNOWN is not FALSE and is not a grant.

A sealed send/ready name is never a pragma name and never a
value. ``campaign_envelope_ready`` is structurally distinct
from ``send_authorized``; both are refused as ``sealed_effect``.

Not wired into the run store. HALT stops STARTS, not
classification. Admitting WAL+FULL is not a send.

Kernel purity: typing + dataclasses. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
PRAGMA_NAMES = frozenset({"journal_mode", "synchronous"})
JOURNAL_MODES = frozenset({
    "WAL", "DELETE", "TRUNCATE", "PERSIST", "MEMORY", "OFF",
})
SYNC_MODES = frozenset({"FULL", "EXTRA", "NORMAL", "OFF"})
ADMITTED_JOURNAL = frozenset({"WAL"})
ADMITTED_SYNC = frozenset({"FULL", "EXTRA"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "unknown_pragma",
    "journal_not_wal",
    "sync_not_full",
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
    """A pragma class never authorizes a send. Structurally False."""
    return False


def halt_blocks_pragma() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pragma verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def admits_normal_sync() -> bool:
    """Structurally False. NORMAL is not durable under WAL."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a pragma is not an external effect."""
    return False


def classify_unknown_pragma() -> str:
    """An unknown pragma name is UNKNOWN, not FALSE and not a grant."""
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


@dataclass(frozen=True)
class PragmaDecision:
    """The pragma-admission verdict. ``grants_send`` is structurally False."""

    allowed: bool
    reason: Optional[str]
    name: str
    value: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "PragmaDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pragma class is not a send")
        object.__setattr__(self, "name", _require_name(self.name, what="name"))
        object.__setattr__(self, "value", _require_name(self.value, what="value"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed pragma must not carry a reason: {self.reason!r}")
            if self.name == "journal_mode" and self.value not in ADMITTED_JOURNAL:
                raise FailClosedError(
                    "PragmaDecision cannot allow a non-WAL journal_mode")
            if self.name == "synchronous" and self.value not in ADMITTED_SYNC:
                raise FailClosedError(
                    "PragmaDecision cannot allow a non-FULL/EXTRA synchronous")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.name) or _is_sealed(self.value):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "PragmaDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_pragma(*, name: object, value: object) -> PragmaDecision:
    """May this durability pragma be applied?

    ``name`` and ``value`` are required names. Bool and empty fail
    closed. A sealed send/ready token in either field is
    ``sealed_effect``.

    An unknown pragma name is UNKNOWN — apply is refused, and the
    refusal is not a claim that the name is FALSE.

    ``journal_mode`` admits only WAL. ``synchronous`` admits FULL
    and EXTRA. NORMAL is refused.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    name_s = _require_name(name, what="name")
    value_s = _require_name(value, what="value")

    if _is_sealed(name_s) or _is_sealed(value_s):
        return PragmaDecision(
            allowed=False,
            reason="sealed_effect",
            name=name_s,
            value=value_s,
        )

    if name_s not in PRAGMA_NAMES:
        return PragmaDecision(
            allowed=False,
            reason="unknown_pragma",
            name=name_s,
            value=value_s,
        )

    if name_s == "journal_mode":
        if value_s not in JOURNAL_MODES:
            raise FailClosedError(
                f"unknown journal_mode is not a refusal and not a grant: "
                f"{value_s!r}")
        if value_s in ADMITTED_JOURNAL:
            return PragmaDecision(
                allowed=True,
                reason=None,
                name=name_s,
                value=value_s,
            )
        return PragmaDecision(
            allowed=False,
            reason="journal_not_wal",
            name=name_s,
            value=value_s,
        )

    # name_s == synchronous
    if value_s not in SYNC_MODES:
        raise FailClosedError(
            f"unknown synchronous is not a refusal and not a grant: "
            f"{value_s!r}")
    if value_s in ADMITTED_SYNC:
        return PragmaDecision(
            allowed=True,
            reason=None,
            name=name_s,
            value=value_s,
        )
    return PragmaDecision(
        allowed=False,
        reason="sync_not_full",
        name=name_s,
        value=value_s,
    )
