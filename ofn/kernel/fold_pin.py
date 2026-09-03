"""Fold pin — pair two classified digests without inventing a third.

A fold is a pairing witness: left and right are already-classified
64-hex digests. This module does not hash their concatenation
(that is ``hash_chain.record_hash``). Same-digest restates.
Different VERIFIED digests pair. Missing either side is UNKNOWN
(None), not FALSE.

A fold never grants a send. ``campaign_envelope_ready`` cannot be
folded into ``send_authorized``. A pairing is not an
``EXECUTION_RECEIPT`` and is not a chain tip.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not invent a third digest.

Not wired into the run store. Pinning a fold is not
``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

HALT stops STARTS. This module has no halt parameter: pinning a
pair is not a run start.

Kernel purity: dataclasses + typing. No hashlib of bodies, no I/O,
no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .digest_class import (
    CLASSES as DIGEST_CLASSES,
    admit_digest,
    classify_digest,
)
from .envelope import SHA256_HEX_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
FOLD_CLASSES = frozenset({"RESTATED", "PAIRED", "UNKNOWN"})
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
    """A fold pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not a pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pairing is not chattr +i."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A pairing is not an external effect."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This pin is not wired into the store."""
    return False


def invents_third_digest() -> bool:
    """Structurally False. A fold records left+right; it does not hash."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A pin does not consume a key."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


def _fold_name(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if type(name) is not str:
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold_name(name) in {s.replace("-", "_") for s in _SEALED}


def classify_fold(left: object, right: object) -> Optional[str]:
    """RESTATED, PAIRED, or UNKNOWN (None). Missing is UNKNOWN.

    Sealed send/ready names fail closed — they are not a fold class.
    Present-but-bad hex still fails closed (shape error).
    """
    if left is None or right is None:
        return None
    left_class = classify_digest(left)
    right_class = classify_digest(right)
    if left_class is None or right_class is None:
        return None
    if left_class not in DIGEST_CLASSES or right_class not in DIGEST_CLASSES:
        raise FailClosedError("digest class drifted")
    if type(left) is not str or type(right) is not str:
        raise FailClosedError("fold sides must be str when classified")
    if left == right:
        return "RESTATED"
    return "PAIRED"


@dataclass(frozen=True)
class FoldPin:
    """One left+right pairing. Frozen so a later write cannot silently
    retcon the pair into send_authorized.
    """

    left: Optional[str]
    right: Optional[str]
    fold_class: str
    allowed: bool
    reason: Optional[str]
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "FoldPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a fold is not a send")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be exact bool: {self.timed_out!r}")
        if self.fold_class not in FOLD_CLASSES:
            raise FailClosedError(
                f"unknown fold class: {self.fold_class!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed fold must not carry a reason: {self.reason!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        for side, label in ((self.left, "left"), (self.right, "right")):
            if side is None:
                continue
            if type(side) is not str:
                raise FailClosedError(f"{label} must be a str or None")
            if _is_sealed(side):
                if self.allowed or self.reason != "sealed_effect":
                    raise FailClosedError(
                        "sealed name may appear only as a sealed_effect "
                        "subject")
            elif not SHA256_HEX_RE.match(side):
                raise FailClosedError(
                    f"{label} must be 64 lowercase hex: {side!r}")
        if self.fold_class == "RESTATED":
            if self.left is None or self.right is None or self.left != self.right:
                raise FailClosedError("RESTATED requires identical sides")
            if self.timed_out:
                raise FailClosedError("timed-out fold cannot be RESTATED")
        if self.fold_class == "PAIRED":
            if self.left is None or self.right is None or self.left == self.right:
                raise FailClosedError("PAIRED requires two different digests")
            if self.timed_out:
                raise FailClosedError("timed-out fold cannot be PAIRED")
        if self.fold_class == "UNKNOWN" and not self.timed_out:
            if (
                self.allowed
                and self.left is not None
                and self.right is not None
                and not _is_sealed(self.left)
                and not _is_sealed(self.right)
            ):
                raise FailClosedError(
                    "two present hex sides cannot be UNKNOWN without timeout")


def pin_fold(
    left: object,
    right: object,
    *,
    timed_out: bool = False,
) -> FoldPin:
    """Pin a pairing of two digest shapes.

    Missing either side is UNKNOWN and admitted. A sealed send/ready
    name on either side is a known refusal (``sealed_effect``).
    Timeout forces UNKNOWN and does not invent a third digest.

    Signature is sealed: no ``halt``, no ``send_authorized``, no
    ``resend``. Tests lock the parameter list.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be exact bool: {timed_out!r}")

    if _is_sealed(left) or _is_sealed(right):
        sealed = left if _is_sealed(left) else right
        if type(sealed) is not str:
            raise FailClosedError(f"sealed fold side must be a str: {sealed!r}")
        left_rec = left if type(left) is str else None
        right_rec = right if type(right) is str else None
        return FoldPin(
            left=left_rec,
            right=right_rec,
            fold_class="UNKNOWN",
            allowed=False,
            reason="sealed_effect",
            timed_out=timed_out,
        )

    left_dec = admit_digest(left, timed_out=False)
    right_dec = admit_digest(right, timed_out=False)
    if not left_dec.allowed or not right_dec.allowed:
        raise FailClosedError("digest side refused — fold is not a send")

    if left is None or right is None:
        return FoldPin(
            left=left_dec.digest,
            right=right_dec.digest,
            fold_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=timed_out,
        )

    if timed_out:
        return FoldPin(
            left=left_dec.digest,
            right=right_dec.digest,
            fold_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=True,
        )

    klass = classify_fold(left, right)
    if klass is None:
        return FoldPin(
            left=left_dec.digest,
            right=right_dec.digest,
            fold_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=False,
        )
    return FoldPin(
        left=left_dec.digest,
        right=right_dec.digest,
        fold_class=klass,
        allowed=True,
        reason=None,
        timed_out=False,
    )


def try_pin(left: object, right: object) -> Optional[FoldPin]:
    """Missing either side is UNKNOWN (None). Present-but-bad fails closed."""
    if left is None or right is None:
        return None
    return pin_fold(left, right)
