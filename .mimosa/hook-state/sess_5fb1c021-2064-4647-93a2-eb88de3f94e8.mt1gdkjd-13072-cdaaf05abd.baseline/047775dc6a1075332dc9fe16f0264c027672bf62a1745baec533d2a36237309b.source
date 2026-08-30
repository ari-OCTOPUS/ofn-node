#!/usr/bin/env python3
"""risk_gate.py -- Unified risk classification and enforcement gate (EQUIP G8).

Maps tool/action invocations to risk tiers and enforces containment:
  - read_only: no approval needed, no budget check
  - reversible_write: idempotency required, light audit
  - irreversible: approval required, dry-run available
  - financial: full approval chain + money_gate + budget ceiling

Design:
  - deny-by-default: unknown action = IRREVERSIBLE (safest)
  - Tool classification is a dict mapping tool_name -> risk tier
  - Each enforcement check returns a decision dict with allow/deny + reason
  - Dry-run mode: returns what WOULD happen without executing
  - Integrates with existing: money_gate, capability_gate, circuit_breaker

$0 | stdlib-only | no network | pure functions where possible
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))


class RiskTier(str, Enum):
    """Risk tiers for tool/action classification. Higher = more dangerous."""
    READ_ONLY = "read_only"
    REVERSIBLE_WRITE = "reversible_write"
    IRREVERSIBLE = "irreversible"
    FINANCIAL = "financial"


# Rank for comparison: higher number = more dangerous
_TIER_RANK = {
    RiskTier.READ_ONLY: 0,
    RiskTier.REVERSIBLE_WRITE: 1,
    RiskTier.IRREVERSIBLE: 2,
    RiskTier.FINANCIAL: 3,
}

# Default tool classification -- unknown tools = IRREVERSIBLE (fail-closed)
DEFAULT_CLASSIFICATION: dict[str, RiskTier] = {
    # Read-only tools
    "list_tree": RiskTier.READ_ONLY,
    "read_file_slice": RiskTier.READ_ONLY,
    "hash_file": RiskTier.READ_ONLY,
    "search_hybrid": RiskTier.READ_ONLY,
    "get_status": RiskTier.READ_ONLY,
    "list_identities": RiskTier.READ_ONLY,
    # Reversible writes (sandbox, internal artifacts)
    "create_note": RiskTier.REVERSIBLE_WRITE,
    "update_artifact": RiskTier.REVERSIBLE_WRITE,
    "schedule_task": RiskTier.REVERSIBLE_WRITE,
    # Irreversible (external effects, deployments)
    "propose_action": RiskTier.IRREVERSIBLE,
    "send_message": RiskTier.IRREVERSIBLE,
    "deploy": RiskTier.IRREVERSIBLE,
    "delete_file": RiskTier.IRREVERSIBLE,
    # Financial
    "execute_trade": RiskTier.FINANCIAL,
    "send_payment": RiskTier.FINANCIAL,
    "subscribe_service": RiskTier.FINANCIAL,
}

SCHEMA = "risk-gate.v1"

# Budget defaults (per-agent, per-epoch)
DEFAULT_BUDGET = {
    "max_token_cost_usd": 1.0,
    "max_time_seconds": 300,
    "max_retries": 5,
    "max_external_calls": 20,
    "max_money_usd": 0.0,  # zero by default -- only owner can raise
}


@dataclass
class BudgetState:
    """Track per-agent resource consumption."""
    agent_id: str
    token_cost_usd: float = 0.0
    time_seconds: float = 0.0
    retries: int = 0
    external_calls: int = 0
    money_spent_usd: float = 0.0
    started_at: float = field(default_factory=time.time)
    limits: dict = field(default_factory=lambda: dict(DEFAULT_BUDGET))

    def remaining(self) -> dict:
        return {
            "token_cost_usd": max(0.0, self.limits["max_token_cost_usd"] - self.token_cost_usd),
            "time_seconds": max(0.0, self.limits["max_time_seconds"] - self.time_seconds),
            "retries": max(0, self.limits["max_retries"] - self.retries),
            "external_calls": max(0, self.limits["max_external_calls"] - self.external_calls),
            "money_spent_usd": max(0.0, self.limits["max_money_usd"] - self.money_spent_usd),
        }

    @property
    def consumed(self) -> dict:
        return {
            "token_cost_usd": self.token_cost_usd,
            "time_seconds": self.time_seconds,
            "retries": self.retries,
            "external_calls": self.external_calls,
            "money_spent_usd": self.money_spent_usd,
        }

    def exceeded(self) -> str | None:
        """Return first exceeded limit name, or None if within budget."""
        r = self.remaining()
        for key, val in r.items():
            if val <= 0:
                return key
        return None

    def record(self, token_cost: float = 0.0, elapsed: float = 0.0,
               is_retry: bool = False, external_call: bool = False,
               money: float = 0.0) -> dict:
        """Record resource consumption. Returns updated state."""
        self.token_cost_usd += token_cost
        self.time_seconds += elapsed
        if is_retry:
            self.retries += 1
        if external_call:
            self.external_calls += 1
        self.money_spent_usd += money
        exc = self.exceeded()
        return {
            "agent_id": self.agent_id,
            "consumed": {
                "token_cost_usd": self.token_cost_usd,
                "time_seconds": self.time_seconds,
                "retries": self.retries,
                "external_calls": self.external_calls,
                "money_spent_usd": self.money_spent_usd,
            },
            "remaining": self.remaining(),
            "exceeded": exc,
        }


def classify(tool_name: str,
             classification: dict[str, RiskTier] | None = None) -> RiskTier:
    """Classify a tool by risk tier. Unknown tools = IRREVERSIBLE (fail-closed)."""
    cls = classification or DEFAULT_CLASSIFICATION
    return cls.get(tool_name, RiskTier.IRREVERSIBLE)


def tier_min(a: RiskTier, b: RiskTier) -> RiskTier:
    """Return the lower (safer) of two tiers."""
    return a if _TIER_RANK.get(a, 99) <= _TIER_RANK.get(b, 99) else b


def tier_max(a: RiskTier, b: RiskTier) -> RiskTier:
    """Return the higher (more dangerous) of two tiers."""
    return a if _TIER_RANK.get(a, 0) >= _TIER_RANK.get(b, 0) else b


def action_fingerprint(action_id: str, tool_name: str,
                      arguments: dict | None = None) -> str:
    """Deterministic fingerprint of an action for approval binding.
    Changes in tool_name or arguments produce different fingerprints.
    Does NOT include action_id itself (it's the key, not content)."""
    payload = {"tool": tool_name, "args": arguments or {}}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                     default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


@dataclass
class EnforcementDecision:
    """Result of risk gate enforcement."""
    allow: bool
    risk_tier: RiskTier
    tool_name: str
    action_id: str
    reason: str
    requires_approval: bool = False
    requires_dry_run: bool = False
    budget_exceeded: str | None = None
    circuit_open: bool = False
    kill_active: bool = False
    dry_run: bool = False  # True if this was a dry-run evaluation

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "allow": self.allow,
            "risk_tier": self.risk_tier.value,
            "tool_name": self.tool_name,
            "action_id": self.action_id,
            "reason": self.reason,
            "requires_approval": self.requires_approval,
            "requires_dry_run": self.requires_dry_run,
            "budget_exceeded": self.budget_exceeded,
            "circuit_open": self.circuit_open,
            "kill_active": self.kill_active,
            "dry_run": self.dry_run,
        }


def check(tool_name: str, action_id: str,
          arguments: dict | None = None,
          agent_id: str = "unknown",
          budget: BudgetState | None = None,
          circuit_open: bool = False,
          kill_active: bool = False,
          approved: bool = False,
          dry_run: bool = False,
          classification: dict[str, RiskTier] | None = None) -> EnforcementDecision:
    """Evaluate a tool invocation against the risk gate.

    Checks in order (fail-fast):
      1. Kill switch active -> DENY
      2. Circuit breaker open -> DENY
      3. Budget exceeded -> DENY
      4. Risk classification
      5. Approval requirements
      6. Dry-run mode

    In dry-run mode, the decision reflects what WOULD happen, but allow is always
    True (the action is not actually executed).
    """
    tier = classify(tool_name, classification)

    # 1. Kill switch check
    if kill_active:
        return EnforcementDecision(
            allow=False, risk_tier=tier, tool_name=tool_name,
            action_id=action_id,
            reason="kill_switch_active:action_blocked",
            kill_active=True, dry_run=dry_run,
        )

    # 2. Circuit breaker check
    if circuit_open:
        return EnforcementDecision(
            allow=False, risk_tier=tier, tool_name=tool_name,
            action_id=action_id,
            reason="circuit_open:action_blocked",
            circuit_open=True, dry_run=dry_run,
        )

    # 3. Budget check (if budget tracking is active)
    if budget is not None:
        exc = budget.exceeded()
        if exc:
            return EnforcementDecision(
                allow=False, risk_tier=tier, tool_name=tool_name,
                action_id=action_id,
                reason=f"budget_exceeded:{exc}",
                budget_exceeded=exc, dry_run=dry_run,
            )

    # 4. Risk classification enforcement
    requires_approval = tier in (RiskTier.IRREVERSIBLE, RiskTier.FINANCIAL)
    requires_dry_run = tier in (RiskTier.IRREVERSIBLE, RiskTier.FINANCIAL)

    # 5. Approval check for sensitive tiers
    if requires_approval and not approved:
        if dry_run:
            return EnforcementDecision(
                allow=True, risk_tier=tier, tool_name=tool_name,
                action_id=action_id,
                reason="dry_run:would_require_approval",
                requires_approval=True, requires_dry_run=requires_dry_run,
                dry_run=True,
            )
        return EnforcementDecision(
            allow=False, risk_tier=tier, tool_name=tool_name,
            action_id=action_id,
            reason="approval_required",
            requires_approval=True, requires_dry_run=requires_dry_run,
            dry_run=dry_run,
        )

    # 6. Financial tier also needs money gate (external check, not enforced here)
    if tier == RiskTier.FINANCIAL and not dry_run:
        return EnforcementDecision(
            allow=True, risk_tier=tier, tool_name=tool_name,
            action_id=action_id,
            reason="financial:approved_but_money_gate_required",
            requires_approval=True, dry_run=dry_run,
        )

    # All checks passed
    return EnforcementDecision(
        allow=True, risk_tier=tier, tool_name=tool_name,
        action_id=action_id,
        reason="allowed",
        requires_approval=requires_approval,
        requires_dry_run=requires_dry_run,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    # Demo
    tools = ["list_tree", "propose_action", "execute_trade", "unknown_tool"]
    for t in tools:
        d = check(t, "test-001", dry_run=True)
        print(json.dumps(d.to_dict(), indent=2))
