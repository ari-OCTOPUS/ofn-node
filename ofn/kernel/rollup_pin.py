"""Rollup pin — kernel-pure overall verdict for a set of file attestations.

Per-file names come from ``attest_class``. This module is the second
witness for the *tree*: which file verdicts may promote, and which
must not.

Closed overall vocabulary (three names, not four):

  inconsistent  → any file is inconsistent (tamper wins)
  incomplete    → else any incomplete, any unknown, or truncated
  consistent    → else every file is consistent (empty + not
                  truncated is a fully witnessed empty tree)

Unknown files roll up as incomplete, never as inconsistent, and
never as consistent. Truncation is incomplete, not a silent
consistent. An empty file list with ``truncated=True`` is
incomplete — the walk stopped before it could finish.

A sealed send/ready name is never a verdict. ``campaign_envelope_ready``
is structurally distinct from ``send_authorized``; both are refused.

HALT stops STARTS. This pin has no halt parameter: an in-flight
rollup must still be classifiable so recovery does not need the
owner.

Not wired into the run store or any adapter. Rolling up is not
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.
Ready is not authorized.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .attest_class import FILE_VERDICTS
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed overall vocabulary. Widen only with a test.
# ``unknown`` is a file verdict, not an overall name — unknown files
# contribute to incomplete.
OVERALL_VERDICTS = frozenset({
    "consistent",
    "incomplete",
    "inconsistent",
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
    """A rollup never authorizes a send. Structurally False."""
    return False


def halt_blocks_rollup() -> bool:
    """Structurally False. HALT stops STARTS, not rollup."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A rollup is not chattr +i."""
    return False


def unknown_file_is_consistent() -> bool:
    """Structurally False. Unknown files make the tree incomplete."""
    return False


def unknown_file_is_inconsistent() -> bool:
    """Structurally False. Unknown is not tamper."""
    return False


def truncated_is_consistent() -> bool:
    """Structurally False. A stopped walk is incomplete."""
    return False


def empty_truncated_is_consistent() -> bool:
    """Structurally False. Empty + truncated is incomplete."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming a rollup is not an external effect."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _require_verdict(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"file verdict must be a name: {value!r}")
    name = value.strip()
    if _is_sealed(name):
        raise FailClosedError(
            f"file verdict names a sealed send/ready state: {name!r}")
    if name not in FILE_VERDICTS:
        raise FailClosedError(f"unknown file verdict is not a rollup: {name!r}")
    return name


def _require_verdicts(file_verdicts: object) -> tuple[str, ...]:
    """A missing list is UNKNOWN, not an empty tree.

    ``None`` fails closed. A string is not a list (iteration would
    walk characters). A bool is not a list.
    """
    if file_verdicts is None:
        raise FailClosedError(
            "file_verdicts is UNKNOWN, not empty — refusing rollup")
    if isinstance(file_verdicts, (bool, str, bytes, bytearray)):
        raise FailClosedError(
            f"file_verdicts must be a sequence of names: {file_verdicts!r}")
    if not isinstance(file_verdicts, (Sequence, Iterable)):
        raise FailClosedError(
            f"file_verdicts must be a sequence of names: {file_verdicts!r}")
    out: list[str] = []
    for item in file_verdicts:
        out.append(_require_verdict(item))
    return tuple(out)


@dataclass(frozen=True)
class RollupDecision:
    """One tree rollup. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``verdict`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    verdict: str
    truncated: bool
    file_count: int
    unknown_count: int
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "RollupDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a rollup is not a send")
        if self.verdict not in OVERALL_VERDICTS:
            raise FailClosedError(f"unknown overall verdict: {self.verdict!r}")
        if _is_sealed(self.verdict):
            raise FailClosedError(
                "RollupDecision cannot carry a sealed send/ready name")
        if not isinstance(self.truncated, bool):
            raise FailClosedError(
                f"truncated must be a bool: {self.truncated!r}")
        if (not isinstance(self.file_count, int)
                or isinstance(self.file_count, bool)
                or self.file_count < 0):
            raise FailClosedError(
                f"file_count must be a non-negative int: {self.file_count!r}")
        if (not isinstance(self.unknown_count, int)
                or isinstance(self.unknown_count, bool)
                or self.unknown_count < 0):
            raise FailClosedError(
                f"unknown_count must be a non-negative int: {self.unknown_count!r}")
        if self.unknown_count > self.file_count:
            raise FailClosedError(
                "unknown_count cannot exceed file_count")
        if self.verdict == "consistent":
            if self.truncated:
                raise FailClosedError(
                    "consistent rollup cannot be truncated")
            if self.unknown_count != 0:
                raise FailClosedError(
                    "consistent rollup cannot include unknown files")


def rollup(
    *,
    file_verdicts: object,
    truncated: object,
) -> RollupDecision:
    """Roll a sequence of file verdicts into one overall name.

    ``file_verdicts`` and ``truncated`` are required. A missing list
    (``None``) is UNKNOWN, not empty. A missing ``truncated``
    (``None``) is UNKNOWN, not False. A Python bool is the only
    admitted type for ``truncated``.

    Order of precedence is mechanical:

    1. any ``inconsistent`` → overall ``inconsistent``
    2. else any ``incomplete`` or ``unknown``, or ``truncated`` →
       overall ``incomplete``
    3. else ``consistent`` (including the empty, not-truncated tree)

    A sealed send/ready name fails closed. Signature is sealed: no
    ``resend``, no ``send_authorized``, no ``halt``. Tests lock the
    parameter list; the kernel does not import inspect.
    """
    names = _require_verdicts(file_verdicts)
    if truncated is None:
        raise FailClosedError(
            "truncated is UNKNOWN, not False — refusing rollup")
    if not isinstance(truncated, bool):
        raise FailClosedError(f"truncated must be a bool: {truncated!r}")

    unknown_count = sum(1 for n in names if n == "unknown")
    if any(n == "inconsistent" for n in names):
        overall = "inconsistent"
    elif truncated or any(n in {"incomplete", "unknown"} for n in names):
        overall = "incomplete"
    else:
        overall = "consistent"

    return RollupDecision(
        verdict=overall,
        truncated=truncated,
        file_count=len(names),
        unknown_count=unknown_count,
    )
