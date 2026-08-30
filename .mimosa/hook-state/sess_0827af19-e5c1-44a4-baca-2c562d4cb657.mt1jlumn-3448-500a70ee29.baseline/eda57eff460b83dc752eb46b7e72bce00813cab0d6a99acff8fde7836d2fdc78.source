#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""policy_enforcer.py -- Policy Enforcement Point (PEP) for Zero-Trust (EQUIP G7).

The PEP is the single point through which all tool/action invocations pass.
It combines identity verification, capability token validation, and ABAC/RBAC
policy checks into a single deny-by-default decision.

Design:
  - deny-by-default: no identity + no token = DENIED
  - RBAC: agent role determines base capability level
  - ABAC: context (risk, resource sensitivity) can further restrict
  - MCP tool discovery != permission: this module is the bridge
  - Tool arguments are policy-checked BEFORE reaching the tool
  - All deny/escalation attempts are audit-logged

The PEP does NOT execute tools. It returns a decision dict that the caller
uses to decide whether to proceed.

Acceptance scenario:
  A worker with read permission attempts a write. The PEP must DENY the
  request BEFORE it reaches the tool, and produce an audit trail.

$0 | stdlib-only | no network | audit log is append-only JSONL.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from identity_store import IdentityStore, Identity
from capability_token import verify as verify_token, consume_nonce

SCHEMA = "policy-enforcer.v1"

# Policy decision types
DECISION_ALLOW = "ALLOW"
DECISION_DENY = "DENY"
DECISION_ESCALATE = "ESCALATE"

# Tool sensitivity levels (ordered by restriction)
TOOL_SENSITIVITY = {
    "list_tree": "low",
    "read_file_slice": "low",
    "hash_file": "low",
    "search_hybrid": "low",
    "propose_action": "medium",
    "delete_file": "critical",     # not in MCP, but defensively listed
    "modify_file": "critical",     # not in MCP, but defensively listed
    "run_command": "critical",    # not in MCP, but defensively listed
}

# Scope requirements per sensitivity level
SENSITIVITY_SCOPE_REQUIREMENT = {
    "low": "read",
    "medium": "propose",
    "critical": "write",
}

# Risk factors that can escalate a decision (ABAC context)
RISK_FACTORS = (
    "path_contains_secrets",
    "path_contains_env",
    "path_contains_git",
    "path_outside_workspace",
    "large_output_requested",
    "resource_exhaustion_risk",
)

# Role to maximum allowed scope
ROLE_MAX_SCOPE = {
    "observer": "read",
    "worker": "read",
    "coordinator": "propose",
    "owner": "write",
}


@dataclass(frozen=True)
class PolicyDecision:
    """Immutable policy decision result.

    Fields:
        decision: ALLOW, DENY, or ESCALATE
        reason: Human-readable reason for the decision
        agent_id: Who requested the action
        action: What was requested
        resource: What resource was targeted
        token_id: Capability token that authorized this (if any)
        risk_factors: Any risk factors detected
        timestamp: When the decision was made
        audit_id: Unique ID for this decision (for audit trail)
    """
    decision: str
    reason: str
    agent_id: str
    action: str
    resource: str
    token_id: str | None = None
    risk_factors: tuple[str, ...] = ()
    timestamp: float = field(default_factory=time.time)
    audit_id: str = ""

    def __post_init__(self) -> None:
        if self.decision not in (DECISION_ALLOW, DECISION_DENY, DECISION_ESCALATE):
            raise ValueError(f"invalid decision: {self.decision}")


class PolicyEnforcer:
    """Policy Enforcement Point. Combines identity + token + policy.

    Usage:
        store = IdentityStore()
        enforcer = PolicyEnforcer(store, audit_path="audit.jsonl")
        decision = enforcer.evaluate(
            agent_id="worker-1",
            action="read_file_slice",
            resource="path:/notes/daily.md",
            token=capability_token,
            args={"path": "/notes/daily.md", "offset": 0},
        )
        if decision.decision == "DENY":
            # stop before reaching the tool
    """

    def __init__(
        self,
        identity_store: IdentityStore,
        audit_path: Path | str | None = None,
        used_nonces: set[str] | None = None,
    ) -> None:
        self._store = identity_store
        self._audit_path = Path(audit_path) if audit_path else None
        self._used_nonces = used_nonces if used_nonces is not None else set()
        self._decision_count = 0

    def evaluate(
        self,
        agent_id: str,
        action: str,
        resource: str,
        *,
        token: dict | None = None,
        args: dict[str, Any] | None = None,
        task_id: str | None = None,
        now: float | None = None,
    ) -> PolicyDecision:
        """Evaluate whether an agent can perform an action on a resource.

        Decision pipeline (fail-fast, deny-by-default):
          1. Identity check: agent must be known
          2. Token check: if token provided, validate it
          3. RBAC: role must have sufficient privilege
          4. Scope check: token scope must meet tool sensitivity
          5. ABAC: risk factors assessed
          6. Final decision

        Returns PolicyDecision (immutable).
        """
        _now = now if now is not None else time.time()
        self._decision_count += 1
        audit_id = f"pd-{self._decision_count:06d}"

        risk_factors = self._assess_risks(action, resource, args)

        # Step 1: Identity check (deny-by-default for unknown agents)
        identity = self._store.lookup(agent_id)
        if identity is None:
            decision = PolicyDecision(
                decision=DECISION_DENY,
                reason="unknown-agent",
                agent_id=str(agent_id),
                action=str(action),
                resource=str(resource),
                risk_factors=risk_factors,
                timestamp=_now,
                audit_id=audit_id,
            )
            self._audit(decision)
            return decision

        # Step 2: Token validation (if token provided)
        if token is not None:
            token_result = verify_token(
                token,
                agent_id=agent_id,
                action=action,
                resource=resource,
                task_id=task_id,
                now=_now,
                used_nonces=self._used_nonces,
            )
            if not token_result["ok"]:
                decision = PolicyDecision(
                    decision=DECISION_DENY,
                    reason=f"token-{token_result['reason']}",
                    agent_id=str(agent_id),
                    action=str(action),
                    resource=str(resource),
                    token_id=token.get("token_id"),
                    risk_factors=risk_factors,
                    timestamp=_now,
                    audit_id=audit_id,
                )
                self._audit(decision)
                return decision

            # Consume nonce to prevent replay
            consume_nonce(token, self._used_nonces)

        # Step 3: RBAC -- role-based check
        role = identity.role
        tool_sensitivity = TOOL_SENSITIVITY.get(action, "medium")
        required_scope = SENSITIVITY_SCOPE_REQUIREMENT.get(tool_sensitivity, "read")
        max_scope = ROLE_MAX_SCOPE.get(role, "read")

        # Token scope overrides role scope if token is present
        if token is not None:
            token_scope = token.get("scope", "read")
            max_scope = token_scope

        if not _scope_sufficient(max_scope, required_scope):
            decision = PolicyDecision(
                decision=DECISION_DENY,
                reason=f"insufficient-privilege: role={role} scope={max_scope} "
                       f"required={required_scope}",
                agent_id=str(agent_id),
                action=str(action),
                resource=str(resource),
                token_id=token.get("token_id") if token else None,
                risk_factors=risk_factors,
                timestamp=_now,
                audit_id=audit_id,
            )
            self._audit(decision)
            return decision

        # Step 4: ABAC -- risk factor escalation
        if risk_factors and max_scope != "write":
            # Risk factors require escalation unless agent has write scope
            decision = PolicyDecision(
                decision=DECISION_ESCALATE,
                reason=f"risk-factors:{','.join(risk_factors)}",
                agent_id=str(agent_id),
                action=str(action),
                resource=str(resource),
                token_id=token.get("token_id") if token else None,
                risk_factors=risk_factors,
                timestamp=_now,
                audit_id=audit_id,
            )
            self._audit(decision)
            return decision

        # Step 5: ALLOW
        decision = PolicyDecision(
            decision=DECISION_ALLOW,
            reason="policy-pass",
            agent_id=str(agent_id),
            action=str(action),
            resource=str(resource),
            token_id=token.get("token_id") if token else None,
            risk_factors=risk_factors,
            timestamp=_now,
            audit_id=audit_id,
        )
        self._audit(decision)
        return decision

    def _assess_risks(
        self,
        action: str,
        resource: str,
        args: dict[str, Any] | None,
    ) -> tuple[str, ...]:
        """Assess risk factors for the action (ABAC context)."""
        risks: list[str] = []
        res_lower = str(resource).lower()

        if "secret" in res_lower or "credential" in res_lower or ".env" in res_lower:
            risks.append("path_contains_secrets")
        if ".env" in res_lower or "env" in res_lower.split("/"):
            risks.append("path_contains_env")
        if ".git" in res_lower:
            risks.append("path_contains_git")
        if args:
            path_arg = str(args.get("path", ""))
            if path_arg.startswith("..") or "://" in path_arg:
                risks.append("path_outside_workspace")
            length = args.get("length", args.get("max_results", 0))
            try:
                if int(length) > 10000:
                    risks.append("large_output_requested")
            except (TypeError, ValueError):
                pass

        return tuple(risks)

    def _audit(self, decision: PolicyDecision) -> None:
        """Append-only audit log. Never throws. Never blocks the decision path."""
        if not self._audit_path:
            return
        try:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "schema": SCHEMA,
                "audit_id": decision.audit_id,
                "timestamp": decision.timestamp,
                "decision": decision.decision,
                "reason": decision.reason,
                "agent_id": decision.agent_id,
                "action": decision.action,
                "resource": decision.resource,
                "token_id": decision.token_id,
                "risk_factors": list(decision.risk_factors),
            }
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError:
            pass  # audit failure must never block the decision path

    @property
    def used_nonces(self) -> set[str]:
        """Access the nonce set for persistence by the caller."""
        return set(self._used_nonces)


def _scope_sufficient(held: str, required: str) -> bool:
    """Check if held scope meets or exceeds required scope.

    Hierarchy: read < propose < write.
    """
    scope_rank = {"read": 0, "propose": 1, "write": 2}
    return scope_rank.get(held, -1) >= scope_rank.get(required, 0)


# -- Convenience: quick check without full enforcer --
def quick_check(
    identity_store: IdentityStore,
    agent_id: str,
    action: str,
    resource: str,
    scope: str = "read",
) -> PolicyDecision:
    """Quick RBAC-only check without token or audit.

    Useful for fast pre-filtering. For full policy evaluation, use
    PolicyEnforcer.evaluate() instead.
    """
    identity = identity_store.lookup(agent_id)
    if identity is None:
        return PolicyDecision(
            decision=DECISION_DENY,
            reason="unknown-agent",
            agent_id=str(agent_id),
            action=str(action),
            resource=str(resource),
        )

    tool_sensitivity = TOOL_SENSITIVITY.get(action, "medium")
    required_scope = SENSITIVITY_SCOPE_REQUIREMENT.get(tool_sensitivity, "read")
    max_scope = ROLE_MAX_SCOPE.get(identity.role, "read")

    # Use provided scope if it's higher than role scope
    effective_scope = max(scope, max_scope, key=lambda s: _scope_sufficient(s, "read") and {"read": 0, "propose": 1, "write": 2}.get(s, -1))

    if not _scope_sufficient(effective_scope, required_scope):
        return PolicyDecision(
            decision=DECISION_DENY,
            reason=f"insufficient-privilege",
            agent_id=str(agent_id),
            action=str(action),
            resource=str(resource),
        )

    return PolicyDecision(
        decision=DECISION_ALLOW,
        reason="quick-pass",
        agent_id=str(agent_id),
        action=str(action),
        resource=str(resource),
    )
