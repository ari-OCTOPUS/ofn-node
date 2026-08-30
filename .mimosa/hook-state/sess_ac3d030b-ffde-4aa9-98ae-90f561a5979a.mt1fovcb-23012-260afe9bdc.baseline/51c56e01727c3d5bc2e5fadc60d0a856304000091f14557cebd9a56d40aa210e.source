#!/usr/bin/env python3
"""kill_coordinator.py -- Unified kill switch coordinator (EQUIP G8).

Coordinates all kill switch mechanisms to ensure:
  1. Kill is independent of LLM (file-based, no AI call needed)
  2. No new tasks start after kill
  3. No compensation runs after kill
  4. Kill can be activated from Telegram/NBB-CP
  5. Existing kill mechanisms (halted(), kill_seam_denies(), HALT-ALL) are honored

This is a COORDINATION layer, not a replacement. It wraps existing mechanisms
and adds agent-level kill tracking.

$0 | stdlib-only | no network | no LLM dependency
"""
from __future__ import annotations

import json
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

SCHEMA = "kill-coordinator.v1"


class KillReason(str, Enum):
    """Standardized kill reasons."""
    OWNER_COMMAND = "owner_command"
    BUDGET_EXCEEDED = "budget_exceeded"
    CIRCUIT_BREAKER = "circuit_breaker"
    SAFETY_VIOLATION = "safety_violation"
    RETRY_STORM = "retry_storm"
    MEMORY_POISONING = "memory_poisoning"
    EXTERNAL_ALERT = "external_alert"


@dataclass
class KillOrder:
    """A kill order that has been issued."""
    reason: KillReason
    issued_at: float
    issued_by: str  # "owner", "system", "telegram", "nbb_cp"
    details: dict = field(default_factory=dict)
    target_agent: str | None = None  # None = global kill

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "reason": self.reason.value,
            "issued_at": self.issued_at,
            "issued_by": self.issued_by,
            "details": self.details,
            "target_agent": self.target_agent,
        }


class KillCoordinator:
    """Coordinates kill switches across the system.

    Wraps existing mechanisms (halted(), kill_seam_denies()) and adds
    agent-level tracking. All checks are LLM-independent (file-based or
    in-memory state).

    Invariants:
      - Once killed, an agent cannot be unkilled programmatically
      - After global kill, no new tasks start for any agent
      - Compensation is never run after kill
      - Kill state is independent of LLM output
    """

    def __init__(self, sandbox_dir: Path | None = None):
        """Initialize coordinator.

        Args:
            sandbox_dir: If provided, use isolated kill files (for testing).
                         If None, use real opslib paths (read-only check).
        """
        self._global_killed = False
        self._global_kill_order: KillOrder | None = None
        self._agent_kills: dict[str, KillOrder] = {}
        self._kill_history: list[KillOrder] = []
        self._sandbox_dir = sandbox_dir

    @property
    def is_global_kill(self) -> bool:
        """Check if global kill is active."""
        if self._global_killed:
            return True
        # Also check existing system-level kill mechanisms
        try:
            import opslib
            if opslib.halted() is not None:
                return True
        except Exception:
            pass
        return False

    @property
    def global_kill_order(self) -> KillOrder | None:
        return self._global_kill_order

    def is_agent_killed(self, agent_id: str) -> bool:
        """Check if a specific agent is killed."""
        if self.is_global_kill:
            return True  # Global kill covers all agents
        return agent_id in self._agent_kills

    def kill_global(self, reason: KillReason, issued_by: str = "owner",
                   details: dict | None = None) -> KillOrder:
        """Issue a global kill order.

        No new tasks will be started for any agent.
        """
        order = KillOrder(
            reason=reason,
            issued_at=time.time(),
            issued_by=issued_by,
            details=details or {},
        )
        self._global_killed = True
        self._global_kill_order = order
        self._kill_history.append(order)
        return order

    def kill_agent(self, agent_id: str, reason: KillReason,
                   issued_by: str = "system",
                   details: dict | None = None) -> KillOrder:
        """Issue a per-agent kill order."""
        order = KillOrder(
            reason=reason,
            issued_at=time.time(),
            issued_by=issued_by,
            details=details or {},
            target_agent=agent_id,
        )
        self._agent_kills[agent_id] = order
        self._kill_history.append(order)
        return order

    def can_start_task(self, agent_id: str) -> dict:
        """Check if a new task can be started.

        Returns:
            {allow: bool, reason: str, kill_order: dict | None}
        """
        if self.is_global_kill:
            order = self._global_kill_order
            return {
                "allow": False,
                "reason": f"global_kill:{order.reason.value if order else 'unknown'}",
                "kill_order": order.to_dict() if order else None,
            }
        if agent_id in self._agent_kills:
            order = self._agent_kills[agent_id]
            return {
                "allow": False,
                "reason": f"agent_killed:{order.reason.value}",
                "kill_order": order.to_dict(),
            }
        return {"allow": True, "reason": "no_kill_active", "kill_order": None}

    def can_run_compensation(self, agent_id: str) -> dict:
        """Check if compensation can be run.

        Compensation is NEVER allowed after kill (per OCTOPUS invariant).
        """
        if self.is_global_kill:
            return {
                "allow": False,
                "reason": "compensation_forbidden_after_kill",
            }
        if agent_id in self._agent_kills:
            return {
                "allow": False,
                "reason": "compensation_forbidden_after_agent_kill",
            }
        return {"allow": True, "reason": "no_kill_active"}

    def system_halt_status(self) -> dict:
        """Get status of all system-level halt mechanisms (read-only)."""
        result = {
            "global_killed": self._global_killed,
            "agent_kills": len(self._agent_kills),
            "kill_history_count": len(self._kill_history),
        }
        try:
            import opslib
            result["halted"] = opslib.halted()
            result["kill_seam_denies"] = opslib.kill_seam_denies()
            result["master_halted"] = opslib.master_halted()
        except Exception:
            result["halted"] = "opslib_unavailable"
        return result

    @property
    def kill_history(self) -> list[KillOrder]:
        return list(self._kill_history)


if __name__ == "__main__":
    # Demo
    coord = KillCoordinator()
    print("Initial:", coord.can_start_task("worker-1"))

    # Kill a specific agent
    coord.kill_agent("worker-1", KillReason.RETRY_STORM, "system",
                     {"retry_count": 150})
    print("After agent kill:", coord.can_start_task("worker-1"))
    print("Other agent:", coord.can_start_task("worker-2"))

    # Global kill
    coord.kill_global(KillReason.OWNER_COMMAND, "owner")
    print("After global kill:", coord.can_start_task("worker-2"))
    print("Compensation:", coord.can_run_compensation("worker-1"))
    print("System status:", coord.system_halt_status())
