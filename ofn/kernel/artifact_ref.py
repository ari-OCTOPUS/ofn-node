"""Artifact pointer — cite a body without copying it.

Incidents and receipts name a path, a sha256, a byte size, and an
evidence level. They do not embed the document. A pointer is not a
send, not an immutability claim, and not a second witness.

UNKNOWN size is None, never 0. 0 means the caller measured an empty
body. Missing size is not a measurement.

This module does not open the path. The caller supplies the digest
and the size; the kernel only classifies.

Not wired into the run store (that file is owned by an open change).

Admitting a pointer is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: dataclasses + re + typing. No json, no clock, no I/O.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .envelope import SHA256_HEX_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed evidence-level vocabulary. Widen only with a test.
# A = runtime measurement on this host
# B = git blob
# C = agent-reported (one record, not a pair)
EVIDENCE_LEVELS = frozenset({"A", "B", "C"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

_REL_PATH_RE = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/-]{0,255}$")


def grants_send() -> bool:
    """A pointer never authorizes a send. Structurally False."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pointer is not chattr +i."""
    return False


def copies_canonical() -> bool:
    """Structurally False. The pointer cites; it does not embed."""
    return False


def unknown_size_is_zero() -> bool:
    """Structurally False. UNKNOWN size is None, not 0."""
    return False


def agent_reported_is_verified() -> bool:
    """Structurally False. Level C is one record, not a pair."""
    return False


def halt_blocks_pointer() -> bool:
    """Structurally False. HALT stops STARTS, not citation."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _refuse_sealed(value: str, *, what: str) -> None:
    if _is_sealed(value):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    for part in value.replace("\\", "/").split("/"):
        if _is_sealed(part):
            raise FailClosedError(
                f"{what} path component names a sealed send/ready "
                f"state: {part!r}")


def require_rel_path(value: object, *, what: str = "pointer") -> str:
    """Repo-relative path. Absolute, ``..``, and sealed names fail closed."""
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty path: {value!r}")
    text = value.strip()
    _refuse_sealed(text, what=what)
    if text.startswith("/") or text.startswith("\\"):
        raise FailClosedError(f"{what} must be repo-relative: {value!r}")
    if "\\" in text:
        raise FailClosedError(f"{what} refuses backslash: {value!r}")
    if ".." in text.split("/"):
        raise FailClosedError(f"{what} refuses parent traversal: {value!r}")
    if not _REL_PATH_RE.match(text):
        raise FailClosedError(f"{what} malformed: {value!r}")
    return text


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
    _refuse_sealed(text, what="evidence_level")
    if text not in EVIDENCE_LEVELS:
        raise FailClosedError(
            f"unknown evidence_level is not a refusal class and not a grant: {value!r}")
    return text


@dataclass(frozen=True)
class ArtifactRef:
    """A citation. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``byte_size`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    pointer: str
    sha256: str
    byte_size: Optional[int]
    evidence_level: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "ArtifactRef cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pointer is not a send")
        object.__setattr__(self, "pointer", require_rel_path(self.pointer))
        object.__setattr__(self, "sha256", require_sha256(self.sha256))
        object.__setattr__(
            self, "byte_size", require_byte_size(self.byte_size))
        object.__setattr__(
            self, "evidence_level", require_evidence_level(self.evidence_level))

    def size_is_unknown(self) -> bool:
        """True only when the caller supplied None. 0 is a measurement."""
        return self.byte_size is None

    def independently_verified(self) -> bool:
        """A pointer is one record. Level A/B/C are all not a pair."""
        return False


def mint_artifact_ref(
    *,
    pointer: object,
    sha256: object,
    byte_size: object,
    evidence_level: object,
    body: object = None,
) -> ArtifactRef:
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
            "ArtifactRef refuses an embedded body — cite by pointer + "
            "sha256 + byte_size + evidence_level")
    return ArtifactRef(
        pointer=require_rel_path(pointer),
        sha256=require_sha256(sha256),
        byte_size=require_byte_size(byte_size),
        evidence_level=require_evidence_level(evidence_level),
        grants_send=False,
    )
