"""Ref class — kernel-pure BUDGET_DEBIT.ref shape admission.

``typed_event`` accepts any non-empty non-sealed string as ``ref``.
``event_id`` mints and indexes ``evt-`` identities. ``settlement``
looks up a receipt id. This module is the complementary witness
for *ref shape only*: is this value a VERIFIED event_id, UNKNOWN
(missing), or a shape error?

A ref is classified without reading the store and without hashing
bytes. Classification is not filesystem immutability and is not a
send. Missing is UNKNOWN (None), not FALSE and not an empty id.

A sealed send/ready name is never a ref.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.
``PROPOSAL_CREATED`` is not an EXECUTION_RECEIPT id and is refused
as ``proposal_not_receipt``. A kind name is not a ref.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not invent a ref.

Not wired into the run store. Admitting a VERIFIED shape is not
``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

HALT stops STARTS. This module has no halt parameter: classifying
a ref is not a run start.

Kernel purity: dataclasses + typing + re (via event_id). No I/O,
no clock, no now(), no hashlib of a body.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .event_id import EVENT_ID_RE
from .errors import FailClosedError
from .events import (
    EXECUTION_RECEIPT,
    PROPOSAL_CREATED,
    is_forbidden_effect_name,
)

# Closed vocabularies. Widen only with a test.
CLASSES = frozenset({"VERIFIED", "UNKNOWN"})
REFUSAL_REASONS = frozenset({"sealed_effect", "proposal_not_receipt"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

_KIND_NAMES = frozenset({
    EXECUTION_RECEIPT,
    PROPOSAL_CREATED,
    "BUDGET_DEBIT",
    "RUN_CREATED",
    "RUN_CLOSED",
    "RUN_REJECTED",
    "CLAIM_CREATED",
    "POLICY_DECISION",
    "TOOL_INVOKED",
})


def grants_send() -> bool:
    """A ref class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not a classify."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_ref_is_empty() -> bool:
    """Structurally False. Missing ref is UNKNOWN, not ''."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A shape class is not chattr +i."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal name is not a receipt ref."""
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
    """Structurally False. Shape admission does not hash a body."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A classify does not consume a key."""
    return False


def second_debit_is_first() -> bool:
    """Structurally False. One verdict → one budget effect."""
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


def _is_proposal_name(name: object) -> bool:
    if type(name) is not str:
        return False
    return _fold(name) == _fold(PROPOSAL_CREATED)


def classify_ref(value: object) -> Optional[str]:
    """VERIFIED or UNKNOWN (None). Missing is UNKNOWN, not FALSE.

    A sealed send/ready name is not a ref class. A proposal kind
    name is not a receipt ref. A present non-event-id string fails
    closed (shape error), not UNKNOWN.
    """
    if value is None:
        return None
    if type(value) is not str:
        raise FailClosedError(f"ref must be a str or None: {value!r}")
    if not value.strip():
        raise FailClosedError("ref is empty")
    if _is_sealed(value):
        raise FailClosedError(
            f"ref names a sealed send/ready state: {value!r} — "
            "ready is not authorized")
    if _is_proposal_name(value):
        raise FailClosedError(
            f"ref names a proposal, not a receipt: {value!r} — "
            "proposal is not execution")
    if value in _KIND_NAMES:
        raise FailClosedError(
            f"ref names a spine kind, not an event_id: {value!r}")
    if not EVENT_ID_RE.match(value):
        raise FailClosedError(
            f"ref must be evt- + 16 lowercase hex: {value!r}")
    return "VERIFIED"


@dataclass(frozen=True)
class RefDecision:
    """The ref-shape verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    ref_class: str
    ref: Optional[str]
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "RefDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a ref class is not a send")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be exact bool: {self.timed_out!r}")
        if self.ref_class not in CLASSES:
            raise FailClosedError(
                f"unknown ref class: {self.ref_class!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed ref must not carry a reason: {self.reason!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if self.ref is not None:
            if type(self.ref) is not str:
                raise FailClosedError(
                    f"ref must be a str or None: {self.ref!r}")
            if _is_sealed(self.ref) and (
                    self.allowed or self.reason != "sealed_effect"):
                raise FailClosedError(
                    "RefDecision cannot grant or mis-label a sealed "
                    "send/ready name")
            if _is_proposal_name(self.ref) and (
                    self.allowed or self.reason != "proposal_not_receipt"):
                raise FailClosedError(
                    "RefDecision cannot grant or mis-label a proposal name")
            if (
                not _is_sealed(self.ref)
                and not _is_proposal_name(self.ref)
                and not EVENT_ID_RE.match(self.ref)
            ):
                raise FailClosedError(
                    f"recorded ref must be evt- + 16 lowercase hex: "
                    f"{self.ref!r}")
        if self.allowed and self.ref is not None:
            if self.ref_class == "VERIFIED" and self.timed_out:
                raise FailClosedError(
                    "timed-out classify cannot be VERIFIED")
        if self.ref_class == "VERIFIED" and self.ref is None:
            raise FailClosedError("VERIFIED requires a recorded ref")
        if self.ref is not None and _is_sealed(self.ref):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "sealed name may appear only as a sealed_effect subject")
        if self.ref is not None and _is_proposal_name(self.ref):
            if self.allowed or self.reason != "proposal_not_receipt":
                raise FailClosedError(
                    "proposal name may appear only as a "
                    "proposal_not_receipt subject")


def admit_ref(
    value: object,
    *,
    timed_out: bool = False,
) -> RefDecision:
    """May this value be recorded as a BUDGET_DEBIT.ref shape?

    Missing is UNKNOWN and admitted (so inventory can continue).
    A sealed send/ready name is a known refusal (``sealed_effect``).
    A proposal kind name is a known refusal (``proposal_not_receipt``).
    A present non-event-id string fails closed — UNKNOWN is not FALSE
    and is not a forged id.

    Timeout forces UNKNOWN and does not prove concurrent writing.
    A valid event_id under timeout stays recorded; the class is UNKNOWN.

    Signature is sealed: no ``halt``, no ``send_authorized``, no
    ``resend``, no ``prior_debit``. Tests lock the parameter list.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be exact bool: {timed_out!r}")

    if _is_sealed(value):
        if type(value) is not str:
            raise FailClosedError(f"sealed ref must be a str: {value!r}")
        return RefDecision(
            allowed=False,
            reason="sealed_effect",
            ref_class="UNKNOWN",
            ref=value,
            timed_out=timed_out,
        )

    if _is_proposal_name(value):
        if type(value) is not str:
            raise FailClosedError(f"proposal ref must be a str: {value!r}")
        return RefDecision(
            allowed=False,
            reason="proposal_not_receipt",
            ref_class="UNKNOWN",
            ref=value,
            timed_out=timed_out,
        )

    if value is None:
        return RefDecision(
            allowed=True,
            reason=None,
            ref_class="UNKNOWN",
            ref=None,
            timed_out=timed_out,
        )

    klass = classify_ref(value)
    if klass is None:
        return RefDecision(
            allowed=True,
            reason=None,
            ref_class="UNKNOWN",
            ref=None,
            timed_out=timed_out,
        )
    if timed_out:
        return RefDecision(
            allowed=True,
            reason=None,
            ref_class="UNKNOWN",
            ref=value if type(value) is str else None,
            timed_out=True,
        )
    return RefDecision(
        allowed=True,
        reason=None,
        ref_class="VERIFIED",
        ref=value if type(value) is str else None,
        timed_out=False,
    )


def try_classify(value: object) -> Optional[str]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    return classify_ref(value)
