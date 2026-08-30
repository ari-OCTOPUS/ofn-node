#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""approval_state.py — Talk Discovery approval gates (hash/expiry/forbidden).

Store failures and mismatches → BLOCKED / not allowed. No Redis required.
2026-08-12 owner «نمیخوام مرزی بمونه»: hard-forbidden action set emptied;
approval still requires fingerprint/expiry/idempotency + owner path.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256


class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    WAITING_OWNER = "waiting_owner"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class TalkProposal:
    proposal_id: str
    action: str
    payload_digest: str
    policy_version: str
    state_version: int
    expires_at: datetime
    idempotency_key: str


FORBIDDEN_ACTIONS: set[str] = set()  # 2026-08-12 owner: emptied; owner approval path remains

CURRENT_POLICY_VERSION = "talk-discovery-policy.v2"

# In-process idempotency registry (fail-closed on duplicate).
_SEEN_IDEMPOTENCY: set[str] = set()


def proposal_fingerprint(proposal: TalkProposal) -> str:
    body = "|".join(
        (
            proposal.proposal_id,
            proposal.action,
            proposal.payload_digest,
            proposal.policy_version,
            str(proposal.state_version),
            proposal.expires_at.astimezone(UTC).isoformat(),
            proposal.idempotency_key,
        )
    )
    return sha256(body.encode("utf-8")).hexdigest()


def can_approve(
    proposal: TalkProposal,
    *,
    signed_fingerprint: str,
    current_policy_version: str,
    now: datetime | None = None,
    store_ok: bool = True,
) -> tuple[bool, str]:
    now = now or datetime.now(UTC)

    if not store_ok:
        return False, "store_failure_blocked"

    if proposal.action in FORBIDDEN_ACTIONS:
        return False, "hard_forbidden_action"

    if proposal.expires_at <= now:
        return False, "proposal_expired"

    if proposal.policy_version != current_policy_version:
        return False, "policy_version_mismatch"

    if signed_fingerprint != proposal_fingerprint(proposal):
        return False, "proposal_changed_after_approval"

    if proposal.idempotency_key in _SEEN_IDEMPOTENCY:
        return False, "duplicate_idempotency_key"

    return True, "approved"


def register_idempotency(key: str) -> None:
    _SEEN_IDEMPOTENCY.add(key)


def clear_idempotency_registry() -> None:
    """Test seam only."""
    _SEEN_IDEMPOTENCY.clear()


def approve_or_block(
    proposal: TalkProposal,
    *,
    signed_fingerprint: str,
    current_policy_version: str = CURRENT_POLICY_VERSION,
    now: datetime | None = None,
    store_ok: bool = True,
) -> tuple[ApprovalStatus, str]:
    ok, reason = can_approve(
        proposal,
        signed_fingerprint=signed_fingerprint,
        current_policy_version=current_policy_version,
        now=now,
        store_ok=store_ok,
    )
    if not ok:
        if reason == "proposal_expired":
            return ApprovalStatus.EXPIRED, reason
        return ApprovalStatus.BLOCKED, reason
    register_idempotency(proposal.idempotency_key)
    return ApprovalStatus.APPROVED, reason
