"""Approval class — kernel-pure classifier for one review event.

A CI gate can read GitHub reviews. This module is the second
witness: what *name* does that event earn?

Five closed verdicts:

  independent   → approver is listed, not the author, not a bot
  author_self   → approver equals author (self-approval)
  bot           → approver carries the bot marker
  unlisted      → a human non-author who is not in the valid set
  unknown       → approver or state is missing. Never a silent skip.

Unknown is UNKNOWN, not FALSE and not independent. A bot listed
in the valid set is still a bot. An author listed in the valid
set is still author_self. Lowering the required-approvals count
is not this module's job and is not a knob here.

A sealed send/ready name is never a login and never a verdict.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused.

HALT stops STARTS. This classifier has no halt parameter:
classification is collection-only and must still run so recovery
does not need the owner.

Not wired into the run store, the review-gate workflow, or any
adapter (those files are owned by other open changes).
Classifying is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed approval-verdict vocabulary. Widen only with a test.
APPROVAL_VERDICTS = frozenset({
    "independent",
    "author_self",
    "bot",
    "unlisted",
    "unknown",
})

# Closed state vocabulary for a review event. COMMENTED is not
# an approval state — it is refused as a shape error, not unknown.
APPROVAL_STATES = frozenset({
    "APPROVED",
    "CHANGES_REQUESTED",
    "DISMISSED",
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
    """An approval classification never authorizes a send. Structurally False."""
    return False


def halt_blocks_approval() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. Missing approver/state is UNKNOWN, not FALSE."""
    return False


def unknown_is_independent() -> bool:
    """Structurally False. Unknown is not a valid independent approval."""
    return False


def author_self_is_independent() -> bool:
    """Structurally False. The author cannot satisfy independence."""
    return False


def bot_is_independent() -> bool:
    """Structurally False. Bot/App approvals do not satisfy."""
    return False


def unlisted_is_independent() -> bool:
    """Structurally False. A human outside the valid set does not satisfy."""
    return False


def listed_bot_is_independent() -> bool:
    """Structurally False. Listing a bot does not make it independent."""
    return False


def listed_author_is_independent() -> bool:
    """Structurally False. Listing the author does not make it independent."""
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
    name = value.strip()
    if _is_sealed(name):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {name!r}")
    return name


def _is_bot(login: str) -> bool:
    return login.lower().endswith("[bot]")


def _require_valid_reviewers(value: object) -> FrozenSet[str]:
    """A missing set is UNKNOWN, not empty.

    ``None`` fails closed. A string is not a set (iteration would
    walk characters). A bool is not a set. Empty is a shape error
    — it would make independence unreachable and is not a grant.
    """
    if value is None:
        raise FailClosedError(
            "valid_reviewers is UNKNOWN, not empty — refusing classify")
    if isinstance(value, (bool, str, bytes, bytearray)):
        raise FailClosedError(
            f"valid_reviewers must be a collection of names: {value!r}")
    if not isinstance(value, Iterable):
        raise FailClosedError(
            f"valid_reviewers must be a collection of names: {value!r}")
    out: set[str] = set()
    for item in value:
        out.add(_require_name(item, what="valid_reviewer"))
    if not out:
        raise FailClosedError(
            "valid_reviewers is empty — lowering the set does not satisfy")
    return frozenset(out)


@dataclass(frozen=True)
class ApprovalDecision:
    """One review-event classification. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``verdict`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    verdict: str
    author: str
    approver: Optional[str]
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "ApprovalDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a classification is not a send")
        if self.verdict not in APPROVAL_VERDICTS:
            raise FailClosedError(f"unknown approval verdict: {self.verdict!r}")
        if _is_sealed(self.verdict):
            raise FailClosedError(
                "ApprovalDecision cannot carry a sealed send/ready name")
        object.__setattr__(self, "author", _require_name(self.author, what="author"))
        if self.approver is not None:
            object.__setattr__(
                self, "approver", _require_name(self.approver, what="approver"))
        if self.verdict == "unknown" and self.approver is not None:
            # unknown-from-missing-state still records the login
            pass
        if self.verdict == "independent" and self.approver is None:
            raise FailClosedError(
                "independent verdict cannot carry a missing approver")
        if self.verdict == "independent" and self.approver == self.author:
            raise FailClosedError(
                "independent verdict cannot name the author as approver")
        if self.verdict == "author_self" and self.approver != self.author:
            raise FailClosedError(
                "author_self verdict must name the author as approver")
        if self.verdict == "bot" and (
                self.approver is None or not _is_bot(self.approver)):
            raise FailClosedError(
                "bot verdict must name an approver with the bot marker")


def classify_approval(
    *,
    author: object,
    approver: object,
    state: object,
    valid_reviewers: object,
) -> ApprovalDecision:
    """Classify one review event against a valid-reviewer set.

    ``author`` and ``valid_reviewers`` are required. A missing
    ``author`` (``None``) is UNKNOWN, not a grant. A missing
    ``valid_reviewers`` is UNKNOWN, not empty.

    ``approver`` or ``state`` of ``None`` is unknown — not
    independent and not FALSE. ``state`` must be one of the
    closed review states when present; ``COMMENTED`` is refused
    (not an approval). Only ``APPROVED`` can become independent.

    Bot marker is a suffix ``[bot]`` (case-insensitive). A bot
    in ``valid_reviewers`` is still a bot. The author in
    ``valid_reviewers`` is still author_self.

    A sealed send/ready name fails closed. Signature is sealed:
    no ``resend``, no ``send_authorized``, no ``halt``. Tests
    lock the parameter list; the kernel does not import inspect.
    """
    author_name = _require_name(author, what="author")
    valid = _require_valid_reviewers(valid_reviewers)

    if approver is None or state is None:
        approver_name: Optional[str] = None
        if approver is not None:
            approver_name = _require_name(approver, what="approver")
        return ApprovalDecision(
            verdict="unknown",
            author=author_name,
            approver=approver_name,
        )

    approver_name = _require_name(approver, what="approver")
    if isinstance(state, bool) or not isinstance(state, str) or not state.strip():
        raise FailClosedError(f"state must be a review state name: {state!r}")
    state_name = state.strip()
    if _is_sealed(state_name):
        raise FailClosedError(
            f"state names a sealed send/ready state: {state_name!r}")
    if state_name not in APPROVAL_STATES:
        raise FailClosedError(f"unknown review state: {state_name!r}")
    if state_name != "APPROVED":
        return ApprovalDecision(
            verdict="unknown",
            author=author_name,
            approver=approver_name,
        )

    if _is_bot(approver_name):
        return ApprovalDecision(
            verdict="bot",
            author=author_name,
            approver=approver_name,
        )
    if approver_name == author_name:
        return ApprovalDecision(
            verdict="author_self",
            author=author_name,
            approver=approver_name,
        )
    if approver_name not in valid:
        return ApprovalDecision(
            verdict="unlisted",
            author=author_name,
            approver=approver_name,
        )
    return ApprovalDecision(
        verdict="independent",
        author=author_name,
        approver=approver_name,
    )
