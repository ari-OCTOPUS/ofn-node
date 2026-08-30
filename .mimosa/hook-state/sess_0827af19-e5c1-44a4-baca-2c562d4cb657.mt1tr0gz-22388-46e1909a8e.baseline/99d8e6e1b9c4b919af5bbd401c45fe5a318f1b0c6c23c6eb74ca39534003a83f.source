#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""approval_sm.py — owner approval state machine (fail-closed).

Unknown / invalid / timeout / version mismatch → BLOCKED.
No Redis dependency: callers persist proposals themselves (JSONL/file).
Confirming owner approval re-verifies proposal_hash before EXECUTING.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ApprovalState(str, Enum):
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


ALLOWED: dict[ApprovalState, set[ApprovalState]] = {
    ApprovalState.DRAFT: {ApprovalState.PROPOSED},
    ApprovalState.PROPOSED: {ApprovalState.WAITING_OWNER, ApprovalState.BLOCKED},
    ApprovalState.WAITING_OWNER: {
        ApprovalState.APPROVED,
        ApprovalState.REJECTED,
        ApprovalState.EXPIRED,
        ApprovalState.BLOCKED,
    },
    ApprovalState.APPROVED: {
        ApprovalState.EXECUTING,
        ApprovalState.EXPIRED,
        ApprovalState.BLOCKED,
    },
    ApprovalState.EXECUTING: {
        ApprovalState.COMPLETED,
        ApprovalState.FAILED,
        ApprovalState.BLOCKED,
    },
}

POLICY_VERSION = "talk-approval-sm.v1"


def transition(current: ApprovalState, target: ApprovalState) -> ApprovalState:
    if target not in ALLOWED.get(current, set()):
        return ApprovalState.BLOCKED  # unknown / invalid = fail-closed
    return target


@dataclass
class ApprovalProposal:
    proposal_hash: str
    policy_version: str
    state_version: int
    expiry_at: str
    owner_approval_id: str | None
    idempotency_key: str
    state: ApprovalState = ApprovalState.DRAFT
    body: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        return d


def compute_proposal_hash(body: dict[str, Any], *, idempotency_key: str) -> str:
    raw = json.dumps(
        {"body": body, "idempotency_key": idempotency_key},
        sort_keys=True, ensure_ascii=False, default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def advance(proposal: ApprovalProposal, target: ApprovalState) -> ApprovalProposal:
    nxt = transition(proposal.state, target)
    proposal.state = nxt
    if nxt != ApprovalState.BLOCKED and target == nxt:
        proposal.state_version = int(proposal.state_version) + 1
    return proposal


def verify_hash(proposal: ApprovalProposal) -> bool:
    expected = compute_proposal_hash(proposal.body, idempotency_key=proposal.idempotency_key)
    return expected == proposal.proposal_hash


def begin_execute(proposal: ApprovalProposal) -> ApprovalProposal:
    """Move APPROVED → EXECUTING only if hash still matches; else BLOCKED."""
    if proposal.state != ApprovalState.APPROVED:
        proposal.state = ApprovalState.BLOCKED
        return proposal
    if not verify_hash(proposal):
        proposal.state = ApprovalState.BLOCKED
        return proposal
    if proposal.policy_version != POLICY_VERSION:
        proposal.state = ApprovalState.BLOCKED
        return proposal
    # expiry check (ISO compare lexicographic for Zulu timestamps)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if proposal.expiry_at and now > proposal.expiry_at:
        proposal.state = ApprovalState.EXPIRED
        return proposal
    return advance(proposal, ApprovalState.EXECUTING)
