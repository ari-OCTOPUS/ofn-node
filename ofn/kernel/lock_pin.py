"""Lock-pin — admit a freeze-class kind without rewriting the lock.

LF_MATCH pins as frozen_ok. CRLF_CHECKOUT is a known checkout
artefact: not a source edit, not FALSE, and not frozen_ok.
UNKNOWN stays unknown. MISMATCH fail-closes — a content edit
is not a pin.

A pin never updates a lock file (that would be I/O and would
silence the second witness). The caller already classified.

``campaign_envelope_ready`` is structurally distinct from
``send_authorized``. Both fail closed as sealed names.

Not wired into the run store. HALT stops STARTS, not a pin.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import FailClosedError
from .freeze_class import (
    CRLF_CHECKOUT,
    KINDS,
    LF_MATCH,
    MISMATCH,
    UNKNOWN,
    _fold,
    _refuse_sealed,
)

REFUSAL_REASONS = frozenset({"mismatch", "sealed_effect"})


def grants_send() -> bool:
    """A lock pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def crlf_is_source_edit() -> bool:
    """Structurally False. CRLF checkout is not a contract edit."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A pin is not a rename of authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Proposal is not execution."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Not wired into the run store."""
    return False


def rewrites_lock() -> bool:
    """Structurally False. The pin does not rewrite the lock file."""
    return False


@dataclass(frozen=True)
class LockPin:
    """Admission of a freeze kind. ``grants_send`` is False."""

    kind: str
    frozen_ok: bool
    artefact: bool
    unknown: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "LockPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pin is not a send")
        if self.kind not in KINDS:
            raise FailClosedError(
                f"unknown freeze kind is not a negative witness: {self.kind!r}")
        if self.kind == MISMATCH:
            raise FailClosedError(
                "mismatch is a content edit — lock pin refuses, "
                "not a negative witness")
        if self.frozen_ok and self.kind != LF_MATCH:
            raise FailClosedError(
                "frozen_ok is only for LF_MATCH")
        if self.artefact and self.kind != CRLF_CHECKOUT:
            raise FailClosedError(
                "artefact is only for CRLF_CHECKOUT")
        if self.unknown and self.kind != UNKNOWN:
            raise FailClosedError(
                "unknown flag is only for UNKNOWN")


def pin_lock(kind: object) -> LockPin:
    """Admit a classified kind. MISMATCH fail-closes.

    Signature is sealed: no send, no halt, no rewrite, no immutable.
    """
    if isinstance(kind, bool) or not isinstance(kind, str):
        raise FailClosedError(f"kind must be a name: {kind!r}")
    text = _fold(kind)
    _refuse_sealed(text, what="kind")
    if text not in {_fold(k) for k in KINDS}:
        raise FailClosedError(
            f"unknown freeze kind is not a negative witness: {kind!r}")
    folded = {
        "lf_match": LF_MATCH,
        "crlf_checkout": CRLF_CHECKOUT,
        "mismatch": MISMATCH,
        "unknown": UNKNOWN,
    }[text]
    if folded == MISMATCH:
        raise FailClosedError(
            "mismatch is a content edit — lock pin refuses, "
            "not a negative witness")
    return LockPin(
        kind=folded,
        frozen_ok=(folded == LF_MATCH),
        artefact=(folded == CRLF_CHECKOUT),
        unknown=(folded == UNKNOWN),
        grants_send=False,
    )
