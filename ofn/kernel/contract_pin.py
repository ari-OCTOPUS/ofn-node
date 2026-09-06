"""Architecture-contract pin — cite a contract without copying it.

A pin names a closed architecture-contract id, a sha256, a byte
size, and an evidence level. It does not embed the document. A
pin is not a send, not an immutability claim, and not a second
witness of an artifact_ref pointer.

Closed contract vocabulary (same set as arch_bind; widen only
with a test):

  task_envelope, typed_event, run_store, dedup, receipt,
  halt, otel_map, token_budget, worktree_inventory

UNKNOWN size is None, never 0. 0 means the caller measured an
empty body. Missing size is not a measurement.

This module does not open a path. The caller supplies the digest
and the size; the kernel only classifies.

A sealed send/ready name is never a contract id.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both fail closed as sealed names.

Not wired into the run store. Distinct from artifact_ref
(free path) and from arch_bind (surface admission).

HALT stops STARTS. This module has no halt parameter: pinning
a contract is not a run start.

Kernel purity: dataclasses + re + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .arch_bind import CONTRACTS, _is_sealed, _require_name
from .envelope import SHA256_HEX_RE
from .errors import FailClosedError

# Closed evidence-level vocabulary. Widen only with a test.
# A = runtime measurement on this host
# B = git blob
# C = agent-reported (one record, not a pair)
EVIDENCE_LEVELS = frozenset({"A", "B", "C"})

REFUSAL_REASONS = frozenset({"sealed_effect", "embedded_body"})


def grants_send() -> bool:
    """A pin never authorizes a send. Structurally False."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def copies_canonical() -> bool:
    """Structurally False. The pin cites; it does not embed."""
    return False


def unknown_size_is_zero() -> bool:
    """Structurally False. UNKNOWN size is None, not 0."""
    return False


def agent_reported_is_verified() -> bool:
    """Structurally False. Level C is one record, not a pair."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not a contract pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def require_contract(value: object) -> str:
    """Closed contract id. Sealed names and unknowns fail closed."""
    name = _require_name(value, what="contract")
    if _is_sealed(name):
        raise FailClosedError(
            f"contract names a sealed send/ready state: {name!r}")
    if name not in CONTRACTS:
        raise FailClosedError(
            f"unknown contract is not a refusal and not a grant: {name!r}")
    return name


def require_sha256(value: object, *, what: str = "sha256") -> str:
    """Full 64-char lowercase hex. Short prefixes fail closed."""
    if isinstance(value, bool) or not isinstance(value, str):
        raise FailClosedError(f"{what} must be a sha256 hex digest: {value!r}")
    text = value.strip().lower()
    if _is_sealed(text):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {text!r}")
    if not SHA256_HEX_RE.match(text):
        raise FailClosedError(
            f"{what} must be a full 64-char sha256 hex digest: {value!r}")
    return text


def require_byte_size(value: object, *, what: str = "byte_size") -> Optional[int]:
    """Exact non-negative int, or None for UNKNOWN.

    ``None`` is UNKNOWN, not 0. ``True`` / ``1.0`` / ``\"0\"`` fail closed.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"{what} must be exact int or None: {value!r}")
    if value < 0:
        raise FailClosedError(f"{what} must be non-negative: {value!r}")
    return value


def require_evidence_level(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"evidence_level must be a name: {value!r}")
    text = value.strip()
    if _is_sealed(text):
        raise FailClosedError(
            f"evidence_level names a sealed send/ready state: {text!r}")
    if text not in EVIDENCE_LEVELS:
        raise FailClosedError(
            f"unknown evidence_level is not a refusal class and not a grant: "
            f"{value!r}")
    return text


@dataclass(frozen=True)
class ContractPin:
    """A citation of an architecture contract. ``grants_send`` is False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``byte_size`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    contract: str
    sha256: str
    byte_size: Optional[int]
    evidence_level: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "ContractPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pin is not a send")
        object.__setattr__(self, "contract", require_contract(self.contract))
        object.__setattr__(self, "sha256", require_sha256(self.sha256))
        object.__setattr__(
            self, "byte_size", require_byte_size(self.byte_size))
        object.__setattr__(
            self, "evidence_level", require_evidence_level(self.evidence_level))

    def size_is_unknown(self) -> bool:
        """True only when the caller supplied None. 0 is a measurement."""
        return self.byte_size is None

    def independently_verified(self) -> bool:
        """A pin is one record. Level A/B/C are all not a pair."""
        return False


def pin_contract(
    *,
    contract: object,
    sha256: object,
    byte_size: object,
    evidence_level: object,
    body: object = None,
) -> ContractPin:
    """The boundary's only sanctioned constructor.

    ``body`` is accepted only as the explicit absence of a copy. Any
    supplied body — including empty string — is a verbatim embed and
    fails closed. The kernel does not hash the body; that would be I/O
    or a second, silent source.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``immutable``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    if body is not None:
        raise FailClosedError(
            "ContractPin refuses an embedded body — cite by contract + "
            "sha256 + byte_size + evidence_level")
    return ContractPin(
        contract=require_contract(contract),
        sha256=require_sha256(sha256),
        byte_size=require_byte_size(byte_size),
        evidence_level=require_evidence_level(evidence_level),
        grants_send=False,
    )
