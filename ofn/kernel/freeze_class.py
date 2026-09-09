"""Freeze-class — classify a lock digest against observed bytes.

A freeze lock is LF-canonical. A Windows CRLF checkout is a known
artefact, not a source edit and not FALSE. A content mismatch
fail-closes. Missing or timed-out digest is UNKNOWN, not FALSE.

The caller supplies hex digests. This module does not open a path
and does not hash a body — hashing a file would be I/O.

Distinct from flag_freeze (runtime flags), contract_pin
(architecture citation), and the agents/ brain_schema file lock
(owned by the GAP-066 change).

A sealed send/ready name is never a digest.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both fail closed as sealed names.

Not wired into the run store. HALT stops STARTS. Classification
is not a run start.

Kernel purity: dataclasses + re + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import SHA256_HEX_RE, is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

LF_MATCH = "LF_MATCH"
CRLF_CHECKOUT = "CRLF_CHECKOUT"
MISMATCH = "MISMATCH"
UNKNOWN = "UNKNOWN"

KINDS = frozenset({LF_MATCH, CRLF_CHECKOUT, MISMATCH, UNKNOWN})

# Closed intent vocabulary. Classification is not a send.
INTENTS = frozenset({"classify", "observe"})


def grants_send() -> bool:
    """A freeze class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
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
    """Structurally False. A classify is not a rename of authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classify is not filesystem immutability."""
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


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or is_sealed_tool_name(folded)
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "ready is not authorized")


def require_sha256(value: object, *, what: str = "sha256") -> str:
    """Full 64-char lowercase hex. Short prefixes fail closed."""
    if isinstance(value, bool) or not isinstance(value, str):
        raise FailClosedError(f"{what} must be a sha256 hex digest: {value!r}")
    text = value.strip().lower()
    _refuse_sealed(text, what=what)
    if not SHA256_HEX_RE.match(text):
        raise FailClosedError(
            f"{what} must be a full 64-char sha256 hex digest: {value!r}")
    return text


def require_optional_sha256(
    value: object, *, what: str = "sha256"
) -> Optional[str]:
    """None is UNKNOWN, not empty. Empty string fails closed."""
    if value is None:
        return None
    return require_sha256(value, what=what)


@dataclass(frozen=True)
class FreezeClass:
    """A classified lock comparison. ``grants_send`` is False."""

    kind: str
    observed: Optional[str]
    lock: Optional[str]
    known_crlf: Optional[str]
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "FreezeClass cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a classify is not a send")
        if self.kind not in KINDS:
            raise FailClosedError(
                f"unknown freeze kind is not a negative witness: {self.kind!r}")
        object.__setattr__(
            self, "observed", require_optional_sha256(
                self.observed, what="observed"))
        object.__setattr__(
            self, "lock", require_optional_sha256(self.lock, what="lock"))
        object.__setattr__(
            self, "known_crlf", require_optional_sha256(
                self.known_crlf, what="known_crlf"))


def classify_digest(
    *,
    observed: object = None,
    lock: object = None,
    known_crlf: object = None,
    error: object = None,
    intent: object = "classify",
) -> FreezeClass:
    """Classify observed vs lock. Timeout/error forces UNKNOWN.

    ``intent`` is classify or observe. Both continue under HALT
    (this function has no halt parameter). Sealed names fail closed.
    """
    if isinstance(intent, bool) or not isinstance(intent, str):
        raise FailClosedError(f"intent must be a name: {intent!r}")
    folded_intent = _fold(intent)
    _refuse_sealed(folded_intent, what="intent")
    if folded_intent not in INTENTS:
        raise FailClosedError(
            f"unknown intent is not a refusal class and not a grant: "
            f"{intent!r}")

    if error is not None:
        return FreezeClass(
            kind=UNKNOWN,
            observed=None,
            lock=None,
            known_crlf=None,
            grants_send=False,
        )

    if observed is None or lock is None:
        return FreezeClass(
            kind=UNKNOWN,
            observed=require_optional_sha256(observed, what="observed"),
            lock=require_optional_sha256(lock, what="lock"),
            known_crlf=require_optional_sha256(known_crlf, what="known_crlf"),
            grants_send=False,
        )

    obs = require_sha256(observed, what="observed")
    loc = require_sha256(lock, what="lock")
    crlf = require_optional_sha256(known_crlf, what="known_crlf")

    if obs == loc:
        kind = LF_MATCH
    elif crlf is not None and obs == crlf and obs != loc:
        kind = CRLF_CHECKOUT
    else:
        kind = MISMATCH

    return FreezeClass(
        kind=kind,
        observed=obs,
        lock=loc,
        known_crlf=crlf,
        grants_send=False,
    )
