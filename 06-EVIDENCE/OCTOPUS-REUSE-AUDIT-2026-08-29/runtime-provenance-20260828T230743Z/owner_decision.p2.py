"""The owner's decision, as data — rendered, validated, and never sent.

When the node wants to take a RED action (anything touching a person or a
provider), it does not act. It assembles everything the owner needs to say
yes or no into one record — the exact bytes it proposes to send, hashed;
the artifact and verdict that produced them, hashed; what to do when it
goes wrong — and hands over a card.

Twelve fields, no more, because every extra field is one more thing to
read past on a phone:

  decision_id        which question this card answers
  run_id             which run produced it
  lane               which business leg (painting / ziman)
  action             what kind of action is proposed
  recipient_masked   who receives it, masked — never a raw address
  exact_payload      the bytes themselves, verbatim, so approval is of the
                     real thing and not of a summary of it
  payload_sha        SHA-256 of exact_payload — the binding the executor
                     re-checks at send time
  artifact_sha       SHA-256 of the artifact the payload came from
  verdict_sha        SHA-256 of the verdict/policy output that proposed it
  idempotency_key    replay guard: one approval executes once
  expires_at         the approval's deadline, UTC, `YYYY-MM-DDTHH:MM:SSZ`
  rollback           what the owner should do instead of approving, if the
                     answer is no

`render_fake` produces the plain-text card: one decision per message, with
APPROVE_ONCE / REJECT / DETAILS buttons. It is called "fake" because it
renders a card and stops. Nothing in this module sends anything, to anyone,
on any channel — the sending executor lives elsewhere and answers to these
hashes. A module that both asked the question and delivered the answer would
be its own rubber stamp.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

# The three buttons on the card. APPROVE_ONCE, not APPROVE: an approval is
# spent by one execution, and the label must not promise a standing yes.
APPROVE_ONCE = "APPROVE_ONCE"
REJECT = "REJECT"
DETAILS = "DETAILS"
BUTTONS = (APPROVE_ONCE, REJECT, DETAILS)

# Every sha field in the contract is a bare lowercase SHA-256 hex digest.
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA_FIELDS = ("payload_sha", "artifact_sha", "verdict_sha")
# The one timestamp format accepted, everywhere in this contract: UTC, to
# the second, with the literal Z. No offsets, no milliseconds, no guessing.
EXPIRY_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
# strptime alone is lenient (it accepts "2026-8-4T9:0:0Z"); the shape is
# checked first so one spelling, exactly, is valid.
EXPIRY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

DECISION_FIELDS = (
    "decision_id", "run_id", "lane", "action", "recipient_masked",
    "exact_payload", "payload_sha", "artifact_sha", "verdict_sha",
    "idempotency_key", "expires_at", "rollback",
)


@dataclass(frozen=True)
class OwnerDecision:
    """One question for the owner. Frozen: nothing mutates a decision after
    it is asked, because the hashes would silently stop describing it."""
    decision_id: str
    run_id: str
    lane: str
    action: str
    recipient_masked: str
    exact_payload: str
    payload_sha: str
    artifact_sha: str
    verdict_sha: str
    idempotency_key: str
    expires_at: str
    rollback: str


def render_fake(decision: OwnerDecision) -> str:
    """Render one decision as a plain-text card. Sends nothing.

    Accepts a single `OwnerDecision`, or a container holding exactly one —
    two decisions on one card is how an approval for one thing gets spent
    on another, so it raises instead of picking a layout.
    """
    if isinstance(decision, (list, tuple, set, frozenset)):
        if len(decision) != 1:
            raise ValueError(
                f"render_fake: one decision per message, got {len(decision)}")
        decision = next(iter(decision))
    if not isinstance(decision, OwnerDecision):
        raise TypeError(
            f"render_fake: expected OwnerDecision, got {type(decision).__name__}")

    lines = ["OWNER DECISION CARD"]
    for name in DECISION_FIELDS:
        lines.append(f"{name}: {getattr(decision, name)}")
    lines.append("")
    lines.append(f"[{APPROVE_ONCE}] approve this exact payload, once")
    lines.append(f"[{REJECT}] do not send; follow the rollback line")
    lines.append(f"[{DETAILS}] show the artifact and verdict behind the hashes")
    return "\n".join(lines)


def validate(decision: OwnerDecision) -> list[str]:
    """Every reason this decision must not be shown, much less approved.

    Returns an empty list when the record is whole. Presence first (a blank
    field is a missing field — the owner cannot approve a question that was
    not fully asked), then the sha formats, then the expiry format. Errors
    are strings naming the field so a caller can surface them as-is.
    """
    errors: list[str] = []
    for name in DECISION_FIELDS:
        value = getattr(decision, name, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{name}: missing")
    for name in SHA_FIELDS:
        value = getattr(decision, name, None)
        if isinstance(value, str) and value and not SHA256_RE.fullmatch(value):
            errors.append(f"{name}: expected 64 lowercase hex characters")
    expires = getattr(decision, "expires_at", "")
    if isinstance(expires, str) and expires:
        if not EXPIRY_RE.fullmatch(expires):
            errors.append(
                f"expires_at: expected {EXPIRY_FORMAT} (got {expires!r})")
        else:
            try:
                datetime.strptime(expires, EXPIRY_FORMAT)
            except ValueError:
                errors.append(
                    f"expires_at: not a real UTC timestamp (got {expires!r})")
    return errors
