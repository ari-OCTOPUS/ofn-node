"""Attest class — kernel-pure classifier for one file attestation.

A read-only witness adapter can hash bytes. This module is the second
witness: what *name* does that comparison earn?

Four closed file verdicts:

  consistent     → observed digest equals the expected digest
  inconsistent   → both digests present and they differ (tamper)
  incomplete     → expected missing (unmanifested) or path missing
                   (missing-expected). Absence is not tampering.
  unknown        → bytes were unreadable. Never a silent skip.

Unreadable is UNKNOWN, not FALSE and not inconsistent. A missing
expected path is incomplete, not inconsistent. An unmanifested path
is incomplete, not a grant of consistency.

A sealed send/ready name is never a path and never a verdict.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused.

HALT stops STARTS. This classifier has no halt parameter:
classification is collection-only and must still run so recovery
does not need the owner.

Not wired into the run store or any adapter (those files are owned
by other open changes). Classifying is not ``send_authorized``,
``quote_sent``, or ``campaign_envelope_ready``. Ready is not
authorized.

Kernel purity: dataclasses + re + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import SHA256_HEX_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed file-verdict vocabulary. Widen only with a test.
FILE_VERDICTS = frozenset({
    "consistent",
    "inconsistent",
    "incomplete",
    "unknown",
})

# Closed label vocabulary. Widen only with a test.
FILE_LABELS = frozenset({
    "match",
    "mismatch",
    "unmanifested",
    "missing-expected",
    "unreadable",
})

# Known refusals that stay named. Unknown labels fail closed.
REFUSAL_REASONS = frozenset({
    "sealed_effect",
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
    """A file attestation never authorizes a send. Structurally False."""
    return False


def halt_blocks_attest() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. Unreadable is UNKNOWN, not FALSE."""
    return False


def unknown_is_inconsistent() -> bool:
    """Structurally False. Unreadable is not a tamper verdict."""
    return False


def missing_expected_is_inconsistent() -> bool:
    """Structurally False. Absence is not tampering."""
    return False


def unmanifested_is_consistent() -> bool:
    """Structurally False. A path the manifest never named is incomplete."""
    return False


def unreadable_is_skip() -> bool:
    """Structurally False. Unreadable is recorded as unknown, never skipped."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming a verdict is not an external effect."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def _require_digest(value: object, *, what: str) -> str:
    name = _require_name(value, what=what)
    if _is_sealed(name):
        raise FailClosedError(f"{what} names a sealed send/ready state: {name!r}")
    if not SHA256_HEX_RE.match(name):
        raise FailClosedError(f"{what} must be a 64-char lowercase hex digest")
    return name


def _refuse_sealed_path(path: str) -> None:
    if _is_sealed(path):
        raise FailClosedError(
            f"path names a sealed send/ready state: {path!r}")
    for part in path.replace("\\", "/").split("/"):
        if _is_sealed(part):
            raise FailClosedError(
                f"path component names a sealed send/ready state: {part!r}")


@dataclass(frozen=True)
class AttestDecision:
    """One file attestation. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``verdict`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    verdict: str
    label: str
    path: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "AttestDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a classification is not a send")
        if self.verdict not in FILE_VERDICTS:
            raise FailClosedError(f"unknown file verdict: {self.verdict!r}")
        if self.label not in FILE_LABELS:
            raise FailClosedError(f"unknown file label: {self.label!r}")
        object.__setattr__(self, "path", _require_name(self.path, what="path"))
        _refuse_sealed_path(self.path)
        if self.verdict == "unknown" and self.label != "unreadable":
            raise FailClosedError(
                "unknown verdict must carry the unreadable label")
        if self.verdict == "inconsistent" and self.label != "mismatch":
            raise FailClosedError(
                "inconsistent verdict must carry the mismatch label")
        if self.verdict == "consistent" and self.label != "match":
            raise FailClosedError(
                "consistent verdict must carry the match label")
        if self.verdict == "incomplete" and self.label not in {
            "unmanifested", "missing-expected",
        }:
            raise FailClosedError(
                "incomplete verdict must be unmanifested or missing-expected")


def classify_file(
    *,
    path: object,
    readable: object,
    observed_sha: Optional[object] = None,
    expected_sha: Optional[object] = None,
) -> AttestDecision:
    """Classify one path against an expected digest.

    ``path`` and ``readable`` are required. A missing ``readable``
    (``None``) is UNKNOWN, not True and not a skip. A Python bool is
    the only admitted type for ``readable`` — a string is not a
    readability claim.

    When ``readable`` is False the observed/expected digests are
    ignored: unreadable cannot be argued into consistent or
    inconsistent. The verdict is ``unknown`` / ``unreadable``.

    When ``readable`` is True, ``observed_sha`` must be a 64-char
    lowercase hex digest. ``expected_sha`` of ``None`` is
    unmanifested (incomplete). A present expected digest that
    differs is inconsistent. A match is consistent.

    A sealed send/ready name in ``path`` or either digest fails
    closed. Signature is sealed: no ``resend``, no
    ``send_authorized``, no ``halt``. Tests lock the parameter
    list; the kernel does not import inspect.
    """
    path_name = _require_name(path, what="path")
    _refuse_sealed_path(path_name)

    if readable is None:
        raise FailClosedError(
            "readable is UNKNOWN, not True — refusing to skip or grant")
    if not isinstance(readable, bool):
        raise FailClosedError(f"readable must be a bool: {readable!r}")

    if not readable:
        return AttestDecision(
            verdict="unknown",
            label="unreadable",
            path=path_name,
        )

    observed = _require_digest(observed_sha, what="observed_sha")
    if expected_sha is None:
        return AttestDecision(
            verdict="incomplete",
            label="unmanifested",
            path=path_name,
        )
    expected = _require_digest(expected_sha, what="expected_sha")
    if observed == expected:
        return AttestDecision(
            verdict="consistent",
            label="match",
            path=path_name,
        )
    return AttestDecision(
        verdict="inconsistent",
        label="mismatch",
        path=path_name,
    )


def classify_missing_expected(*, path: object) -> AttestDecision:
    """A path the caller expected, and the tree does not have.

    Absence is incomplete, not inconsistent. A sealed send/ready
    name fails closed. Signature is sealed: no ``resend``, no
    ``send_authorized``, no ``halt``.
    """
    path_name = _require_name(path, what="path")
    _refuse_sealed_path(path_name)
    return AttestDecision(
        verdict="incomplete",
        label="missing-expected",
        path=path_name,
    )
