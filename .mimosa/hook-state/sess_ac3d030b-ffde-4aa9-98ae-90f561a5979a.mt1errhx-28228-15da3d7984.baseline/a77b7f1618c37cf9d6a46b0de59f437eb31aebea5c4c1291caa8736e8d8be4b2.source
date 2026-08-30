#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""control_contracts — typed trust-boundary contracts for Octopus v2030.

The agent may PROPOSE, an owner/policy may AUTHORIZE, and the execution gateway
may ACT only when proposal and decision bind to the exact same immutable action.
Stdlib-only so this boundary remains available even when optional packages fail.
No executor, network or live side effect exists in this module.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

SCHEMA = "octopus-control.v2"
RISK = ("low", "medium", "high", "critical")
DECISIONS = ("approve", "reject", "revise")
ACTION_TYPES = ("file_write", "shell_command", "http_request", "memory_promotion",
                "external_message", "code_patch", "task_delegation")
SENSITIVE_ACTIONS = frozenset({"file_write", "shell_command", "http_request",
                               "memory_promotion", "external_message", "code_patch"})


def _canon(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha(v: Any) -> str:
    return hashlib.sha256(_canon(v).encode("utf-8")).hexdigest()


def _now() -> float:
    return time.time()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


@dataclass(frozen=True)
class ActionSpec:
    action_type: str
    target: str
    operation: str
    args: Dict[str, Any] = field(default_factory=dict)
    reversible: bool = True
    sandbox_required: bool = True

    def validate(self) -> List[str]:
        e: List[str] = []
        if self.action_type not in ACTION_TYPES:
            e.append("unknown action_type")
        if not str(self.target).strip() or not str(self.operation).strip():
            e.append("target and operation are required")
        if self.action_type in ("shell_command", "code_patch") and not self.sandbox_required:
            e.append("shell/code actions require sandbox")
        return e

    @property
    def sha256(self) -> str:
        return _sha(asdict(self))


@dataclass(frozen=True)
class ActionProposal:
    proposal_id: str
    mission_id: str
    task_id: str
    trace_id: str
    tenant_id: str
    project_id: str
    agent_id: str
    title: str
    summary: str
    risk: str
    confidence: float
    action: ActionSpec
    reason_codes: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    expected_impact: str = ""
    rollback_plan: str = ""
    created_at: float = field(default_factory=_now)
    expires_at: Optional[float] = None
    schema: str = SCHEMA

    @classmethod
    def create(cls, *, mission_id: str, task_id: str, trace_id: str,
               tenant_id: str, project_id: str, agent_id: str, title: str,
               summary: str, risk: str, confidence: float, action: ActionSpec,
               reason_codes=None, evidence_refs=None, expected_impact="",
               rollback_plan="", ttl_s: Optional[int] = 3600) -> "ActionProposal":
        now = _now()
        return cls(_id("ap"), mission_id, task_id, trace_id, tenant_id, project_id,
                   agent_id, title, summary, risk, float(confidence), action,
                   list(reason_codes or []), list(evidence_refs or []),
                   expected_impact, rollback_plan, now,
                   now + int(ttl_s) if ttl_s else None)

    @property
    def action_sha256(self) -> str:
        return self.action.sha256

    def validate(self, now: Optional[float] = None) -> List[str]:
        e = self.action.validate()
        for k in ("proposal_id", "mission_id", "task_id", "trace_id", "tenant_id",
                  "project_id", "agent_id", "title", "summary"):
            if not str(getattr(self, k, "") or "").strip():
                e.append(f"{k} required")
        if self.risk not in RISK:
            e.append("invalid risk")
        if not 0.0 <= float(self.confidence) <= 1.0:
            e.append("confidence outside [0,1]")
        if self.expires_at is not None and self.expires_at <= (now if now is not None else _now()):
            e.append("proposal expired")
        return e


@dataclass(frozen=True)
class ApprovalDecision:
    decision_id: str
    proposal_id: str
    action_sha256: str
    decision: str
    reviewer_id: str
    reviewer_type: str
    decided_at: float
    expires_at: Optional[float] = None
    revision_instructions: str = ""
    policy_version: str = "octopus-policy.v1"
    schema: str = SCHEMA

    @classmethod
    def create(cls, proposal: ActionProposal, *, decision: str, reviewer_id: str,
               reviewer_type: str = "human", ttl_s: Optional[int] = 900,
               revision_instructions: str = "") -> "ApprovalDecision":
        now = _now()
        return cls(_id("ad"), proposal.proposal_id, proposal.action_sha256,
                   decision, reviewer_id, reviewer_type, now,
                   now + int(ttl_s) if ttl_s else None, revision_instructions)

    def validate(self, proposal: ActionProposal, now: Optional[float] = None) -> List[str]:
        n = now if now is not None else _now()
        e: List[str] = []
        if self.decision not in DECISIONS:
            e.append("invalid decision")
        if self.proposal_id != proposal.proposal_id:
            e.append("decision does not bind proposal")
        if self.action_sha256 != proposal.action_sha256:
            e.append("decision does not bind exact action")
        if self.expires_at is not None and self.expires_at <= n:
            e.append("decision expired")
        if self.decided_at < proposal.created_at:
            e.append("decision predates proposal")
        if self.decision == "revise" and not self.revision_instructions.strip():
            e.append("revise requires instructions")
        return e


def authorization(proposal: ActionProposal, decision: Optional[ApprovalDecision],
                  *, now: Optional[float] = None) -> Dict[str, Any]:
    """Pure fail-closed authorization check. It never executes the action."""
    n = now if now is not None else _now()
    pe = proposal.validate(n)
    if pe:
        return {"allow": False, "reason": "invalid-proposal", "errors": pe}
    requires_human = (proposal.risk in ("high", "critical") or
                      proposal.action.action_type in SENSITIVE_ACTIONS or
                      proposal.confidence < 0.75)
    if not requires_human:
        return {"allow": True, "reason": "low-risk-policy", "action_sha256": proposal.action_sha256}
    if decision is None:
        return {"allow": False, "reason": "approval-required"}
    de = decision.validate(proposal, n)
    if de:
        return {"allow": False, "reason": "invalid-decision", "errors": de}
    if decision.reviewer_type != "human":
        return {"allow": False, "reason": "human-approval-required"}
    if decision.decision != "approve":
        return {"allow": False, "reason": decision.decision}
    return {"allow": True, "reason": "exact-human-authorization",
            "decision_id": decision.decision_id, "action_sha256": proposal.action_sha256}


# ════════════════════════════════════════════════════════════════════════════
# ExecutionResult — what actually ran, recorded apart from what was approved.
#
# Why a separate record (2026-07-28, step 5 of the vertical slice):
#   `approval_state_machine` already had an `execution_result` field, but it
#   lived **on the approval object** and was mutated in place. That conflates
#   two different facts:
#       "the owner approved action X"        (a decision, immutable)
#       "action Y actually ran and returned" (an event, append-only)
#   With one mutable field you can never answer the question that matters:
#   *was what executed the same thing that was approved?* The approval's own
#   history gets overwritten by the outcome.
#
#   Step 4 gave every action an `action_sha256`. This closes the loop: the
#   executor records the hash of what it **actually** ran, and
#   `execution_matches_approval()` compares the two. A mismatch means the
#   payload changed between approval and execution — the TOCTOU window.
#
# This module still executes nothing. It only describes and compares.
# ════════════════════════════════════════════════════════════════════════════

EXECUTION_OUTCOMES = ("success", "failure", "cancelled", "expired", "refused")


@dataclass(frozen=True)
class ExecutionResult:
    result_id: str
    proposal_id: str
    decision_id: str
    action_sha256: str          # hash of what WAS ACTUALLY RUN, not what was approved
    outcome: str
    started_at: float
    finished_at: float
    error: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    @classmethod
    def create(cls, *, proposal_id: str, decision_id: str, action_sha256: str,
               outcome: str, started_at: float, finished_at: Optional[float] = None,
               error: str = "", evidence_refs=None) -> "ExecutionResult":
        return cls(_id("er"), proposal_id, decision_id, action_sha256, outcome,
                   float(started_at),
                   float(finished_at if finished_at is not None else _now()),
                   str(error or ""), list(evidence_refs or []))

    def validate(self) -> List[str]:
        e: List[str] = []
        if self.outcome not in EXECUTION_OUTCOMES:
            e.append(f"outcome must be one of {EXECUTION_OUTCOMES}")
        if not self.action_sha256:
            e.append("action_sha256 is required")
        if not self.proposal_id:
            e.append("proposal_id is required")
        if self.finished_at < self.started_at:
            e.append("finished_at precedes started_at")
        return e


def execution_matches_approval(decision: Optional[ApprovalDecision],
                               result: Optional[ExecutionResult]) -> Dict[str, Any]:
    """Did the thing that ran match the thing that was approved? Fail-closed.

    Every failure path returns match=False. A missing decision or a missing
    result is not "probably fine" — it is an unverifiable execution, which for
    an audit trail is the same as a mismatch.
    """
    if decision is None:
        return {"match": False, "reason": "no-approval"}
    if result is None:
        return {"match": False, "reason": "no-execution-record"}
    re_ = result.validate()
    if re_:
        return {"match": False, "reason": "invalid-result", "errors": re_}
    if result.decision_id and result.decision_id != decision.decision_id:
        return {"match": False, "reason": "different-decision"}
    if result.action_sha256 != decision.action_sha256:
        return {"match": False, "reason": "action-changed-after-approval",
                "approved": decision.action_sha256, "executed": result.action_sha256}
    return {"match": True, "reason": "approved-action-executed",
            "action_sha256": result.action_sha256}
