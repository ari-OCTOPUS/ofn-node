"""Dual record — every claim needs an independent second record.

A single record is UNWITNESSED, not TRUE. Same source is not a
second record. Disagreement is CONTRADICTED; this module does not
pick a winner. UNKNOWN fields fail closed — they are not FALSE
and they are not TRUE.

A sealed send/ready name is never a topic and never a value.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

HALT stops STARTS. This module has no halt parameter: pairing
records is not a run start.

Not wired into the run store (that file is owned by an open change).

Admitting a witnessed pair is not ``send_authorized``,
``quote_sent``, or ``campaign_envelope_ready``. Ready is not
authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
STATUSES = frozenset({"WITNESSED", "UNWITNESSED", "CONTRADICTED"})
VANTAGES = frozenset({"this_host_only", "loopback", "lan", "remote"})
EVIDENCE_LEVELS = frozenset({"E0", "E1", "E2", "E3", "E4", "E5"})
PAIR_REASONS = frozenset({
    "missing_second",
    "same_source",
    "sealed_effect",
    "contradicted",
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
    """A dual record never authorizes a send. Structurally False."""
    return False


def halt_blocks_pair() -> bool:
    """Structurally False. HALT stops STARTS, not pairing."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pair is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_is_true() -> bool:
    """Structurally False. A missing second record is not TRUE."""
    return False


def picks_winner() -> bool:
    """Structurally False. CONTRADICTED does not resolve."""
    return False


def raises_grade() -> bool:
    """Structurally False. Pairing does not promote E3 to E4."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A witnessed pair is not an external effect."""
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


@dataclass(frozen=True)
class RecordRef:
    """One side of a pair. Not a fact. Not a send.

    ``source_path`` is the independent locus of this record.
    ``value`` is the asserted token (a name, never a secret).
    """

    source_path: str
    vantage: str
    value: str
    evidence_level: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_path",
            _require_name(self.source_path, what="source_path"))
        object.__setattr__(
            self, "vantage",
            _require_member(self.vantage, what="vantage", allowed=VANTAGES))
        object.__setattr__(
            self, "value",
            _require_name(self.value, what="value"))
        object.__setattr__(
            self, "evidence_level",
            _require_member(
                self.evidence_level, what="evidence_level",
                allowed=EVIDENCE_LEVELS))
        if _is_sealed(self.source_path) or _is_sealed(self.value):
            raise FailClosedError(
                "RecordRef cannot carry a sealed send/ready name")


@dataclass(frozen=True)
class DualVerdict:
    """The pairing verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``status`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    status: str
    reason: Optional[str]
    topic: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "DualVerdict cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a dual record is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown pair status is not a refusal and not a grant: "
                f"{self.status!r}")
        object.__setattr__(self, "topic", _require_name(self.topic, what="topic"))
        if self.status == "WITNESSED":
            if self.reason is not None:
                raise FailClosedError(
                    f"witnessed pair must not carry a reason: {self.reason!r}")
        else:
            if self.reason not in PAIR_REASONS:
                raise FailClosedError(
                    f"unknown or missing pair reason: {self.reason!r}")
        if _is_sealed(self.topic):
            if self.status == "WITNESSED" or self.reason != "sealed_effect":
                raise FailClosedError(
                    "DualVerdict cannot grant or mis-label a sealed "
                    "send/ready name")


def pair_records(
    *,
    topic: object,
    record_a: object,
    record_b: object = None,
) -> DualVerdict:
    """Pair two records for one topic.

    ``topic`` and ``record_a`` are required. ``record_b`` may be
    omitted: that is UNWITNESSED (``missing_second``), not TRUE.

    Independence is a different ``source_path``. Same vantage on two
    sources is still a pair. Same source is not a second record.

    Unknown vantage, unknown evidence level, empty names, and bool
    stand-ins fail closed — UNKNOWN is not FALSE.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    topic_name = _require_name(topic, what="topic")

    if _is_sealed(topic_name):
        return DualVerdict(
            status="UNWITNESSED",
            reason="sealed_effect",
            topic=topic_name,
        )

    if not isinstance(record_a, RecordRef):
        raise FailClosedError(
            f"record_a must be a RecordRef: {type(record_a).__name__}")

    if record_b is None:
        return DualVerdict(
            status="UNWITNESSED",
            reason="missing_second",
            topic=topic_name,
        )

    if not isinstance(record_b, RecordRef):
        raise FailClosedError(
            f"record_b must be a RecordRef or None: {type(record_b).__name__}")

    if record_a.source_path == record_b.source_path:
        return DualVerdict(
            status="UNWITNESSED",
            reason="same_source",
            topic=topic_name,
        )

    if record_a.value != record_b.value:
        return DualVerdict(
            status="CONTRADICTED",
            reason="contradicted",
            topic=topic_name,
        )

    return DualVerdict(
        status="WITNESSED",
        reason=None,
        topic=topic_name,
    )
