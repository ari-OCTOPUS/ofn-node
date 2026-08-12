#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""policy_gate.py — fail-closed authorization gate (ADR-033).

Only versioned-policy allowlisted actions with valid state/approval proceed.
Ambiguity → DENY or QUARANTINE. Never open side-effects by default.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    QUARANTINE = "quarantine"


@dataclass(frozen=True)
class RequestContext:
    run_id: str
    checkpoint_id: str
    state_version: int
    policy_version: str
    actor: str
    action: str
    trust_level: str
    provenance_id: str | None
    approval_id: str | None
    idempotency_key: str | None
    kill_switch_engaged: bool


@dataclass(frozen=True)
class Policy:
    version: str
    read_only_actions: FrozenSet[str]
    approval_actions: FrozenSet[str]
    forbidden_actions: FrozenSet[str]


@dataclass(frozen=True)
class GateResult:
    decision: Decision
    reason: str

    @property
    def allowed(self) -> bool:
        return self.decision == Decision.ALLOW


SIDE_EFFECTS = frozenset({
    "external_send",
    "tool_write",
    "memory_write",
    "write_episodic_memory",
    "write_semantic_memory",
    "enable_harvest",
    "crm_mutation",
    "payment",
    "policy_mutation",
})

TALK_DISCOVERY_POLICY = Policy(
    version="ADR-033-v1",
    read_only_actions=frozenset({"retrieve_context", "respond_draft"}),
    approval_actions=frozenset({"write_episodic_memory"}),
    forbidden_actions=frozenset({
        "external_send",
        "enable_harvest",
        "crm_mutation",
        "payment",
        "policy_mutation",
        "write_semantic_memory",
        "tool_write",
        "memory_write",
    }),
)


class PolicyGate:
    def decide(self, ctx: RequestContext, policy: Policy | None) -> GateResult:
        if policy is None:
            return GateResult(Decision.DENY, "policy_unavailable")

        if ctx.kill_switch_engaged:
            return GateResult(Decision.DENY, "kill_switch_engaged")

        if ctx.policy_version != policy.version:
            return GateResult(Decision.DENY, "policy_version_mismatch")

        if ctx.action in policy.forbidden_actions:
            return GateResult(Decision.DENY, "action_hard_forbidden")

        if ctx.trust_level == "untrusted" and ctx.action in SIDE_EFFECTS:
            return GateResult(Decision.QUARANTINE, "untrusted_content_cannot_mutate")

        if not ctx.provenance_id:
            return GateResult(Decision.QUARANTINE, "provenance_missing")

        if ctx.action in policy.read_only_actions:
            return GateResult(Decision.ALLOW, "read_only_allowlisted")

        if ctx.action in policy.approval_actions:
            if not ctx.approval_id:
                return GateResult(Decision.DENY, "approval_missing")
            if not ctx.idempotency_key:
                return GateResult(Decision.DENY, "idempotency_key_missing")
            return GateResult(Decision.ALLOW, "approval_action_allowed")

        return GateResult(Decision.DENY, "unknown_action_fail_closed")
