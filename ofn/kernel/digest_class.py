"""Digest class — kernel-pure receipt-digest shape admission.

``receipt_bind`` binds a TYPED EXECUTION_RECEIPT to a 64-hex digest.
``receipts`` hashes field hashes into a receipt identity.
``hash_chain`` hashes ``prev_hash || body``. This module is the
third witness for *digest shape only*: is this value VERIFIED,
UNKNOWN (missing), or a shape error?

A digest is classified without reading a body and without hashing
bytes. Classification is not filesystem immutability and is not a
send. Missing is UNKNOWN (None), not FALSE and not an empty hex.

A sealed send/ready name is never a digest.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not invent a digest.

Not wired into the run store. Admitting a VERIFIED shape is not
``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

HALT stops STARTS. This module has no halt parameter: classifying
a digest is not a run start.

Kernel purity: dataclasses + typing + re (via envelope). No I/O,
no clock, no now(), no hashlib of a body.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import SHA256_HEX_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
CLASSES = frozenset({"VERIFIED", "UNKNOWN"})
REFUSAL_REASONS = frozenset({"sealed_effect"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A digest class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not a classify."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_digest_is_empty() -> bool:
    """Structurally False. Missing digest is UNKNOWN, not ''."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A shape class is not chattr +i."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a digest is not an external effect."""
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


def classify_digest(value: object) -> Optional[str]:
    """VERIFIED or UNKNOWN (None). Missing is UNKNOWN, not FALSE.

    A sealed send/ready name is not a digest class. A present
    non-hex string fails closed (shape error), not UNKNOWN.
    """
    if value is None:
        return None
    if type(value) is not str:
        raise FailClosedError(f"digest must be a str or None: {value!r}")
    if not value.strip():
        raise FailClosedError("digest is empty")
    if _is_sealed(value):
        raise FailClosedError(
            f"digest names a sealed send/ready state: {value!r} — "
            "ready is not authorized")
    if not SHA256_HEX_RE.match(value):
        raise FailClosedError(
            f"digest must be 64 lowercase hex: {value!r}")
    return "VERIFIED"


@dataclass(frozen=True)
class DigestDecision:
    """The digest-shape verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    digest_class: str
    digest: Optional[str]
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "DigestDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a digest class is not a send")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be exact bool: {self.timed_out!r}")
        if self.digest_class not in CLASSES:
            raise FailClosedError(
                f"unknown digest class: {self.digest_class!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed digest must not carry a reason: {self.reason!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if self.digest is not None:
            if type(self.digest) is not str:
                raise FailClosedError(
                    f"digest must be a str or None: {self.digest!r}")
            if _is_sealed(self.digest) and (
                    self.allowed or self.reason != "sealed_effect"):
                raise FailClosedError(
                    "DigestDecision cannot grant or mis-label a sealed "
                    "send/ready name")
            if not _is_sealed(self.digest) and not SHA256_HEX_RE.match(
                    self.digest):
                raise FailClosedError(
                    f"recorded digest must be 64 lowercase hex: "
                    f"{self.digest!r}")
        if self.allowed and self.digest is not None:
            if self.digest_class == "VERIFIED" and self.timed_out:
                raise FailClosedError(
                    "timed-out classify cannot be VERIFIED")
        if self.digest_class == "VERIFIED" and self.digest is None:
            raise FailClosedError("VERIFIED requires a recorded digest")
        if self.digest is not None and _is_sealed(self.digest):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "sealed name may appear only as a sealed_effect subject")


def admit_digest(
    value: object,
    *,
    timed_out: bool = False,
) -> DigestDecision:
    """May this value be recorded as a digest shape?

    Missing is UNKNOWN and admitted (so inventory can continue).
    A sealed send/ready name is a known refusal (``sealed_effect``).
    A present non-hex string fails closed — UNKNOWN is not FALSE
    and is not a forged hex.

    Timeout forces UNKNOWN and does not prove concurrent writing.
    A valid hex under timeout stays recorded; the class is UNKNOWN.

    Signature is sealed: no ``halt``, no ``send_authorized``, no
    ``resend``. Tests lock the parameter list.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be exact bool: {timed_out!r}")

    if _is_sealed(value):
        if type(value) is not str:
            raise FailClosedError(f"sealed digest must be a str: {value!r}")
        return DigestDecision(
            allowed=False,
            reason="sealed_effect",
            digest_class="UNKNOWN",
            digest=value,
            timed_out=timed_out,
        )

    if value is None:
        return DigestDecision(
            allowed=True,
            reason=None,
            digest_class="UNKNOWN",
            digest=None,
            timed_out=timed_out,
        )

    klass = classify_digest(value)
    if klass is None:
        return DigestDecision(
            allowed=True,
            reason=None,
            digest_class="UNKNOWN",
            digest=None,
            timed_out=timed_out,
        )
    if timed_out:
        return DigestDecision(
            allowed=True,
            reason=None,
            digest_class="UNKNOWN",
            digest=value if type(value) is str else None,
            timed_out=True,
        )
    return DigestDecision(
        allowed=True,
        reason=None,
        digest_class="VERIFIED",
        digest=value if type(value) is str else None,
        timed_out=False,
    )


def try_classify(value: object) -> Optional[str]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    return classify_digest(value)
