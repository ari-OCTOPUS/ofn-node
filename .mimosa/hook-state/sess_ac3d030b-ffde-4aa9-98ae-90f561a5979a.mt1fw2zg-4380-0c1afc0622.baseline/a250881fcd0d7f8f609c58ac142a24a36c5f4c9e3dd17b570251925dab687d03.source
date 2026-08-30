# -*- coding: utf-8 -*-
"""P0 execution gate — single choke for overlay actions.

Order (fail-closed, INV-3 then INV-2 then INV-1 then INV-5 then execute):
  1. kill / composed STOP
  2. hard_no_go
  3. G4 taint latch → network.mode=none
  4. L3 owner approval for money / irreversible / production
  5. overlay budget reserve (≤ live HARD floors)
  6. capability lease consume (if provided)
  7. INTENT ledger append  ← no execute before this succeeds
  8. execute callback
  9. RESULT ledger + settle or release

This gate is not wired into organism.py. WIRED=False in __init__.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .budget import OverlayBudget
from .exceptions import PolicyDenied, TaintNetworkDenied
from .kill import KillSwitch
from .ledger import IntentLedger
from .lease import CapabilityLease, LeaseStore
from .policy import deny_forbidden, requires_owner
from .taint import TaskTaintLatch


@dataclass(frozen=True)
class Action:
    name: str
    actor: str
    task_id: str
    cost_cents: int = 0
    financial: bool = False
    irreversible: bool = False
    production: bool = False
    params: Mapping[str, Any] = field(default_factory=dict)
    untrusted_input: bool = False
    untrusted_source: str = ""
    network_requested: str = "none"
    lease: CapabilityLease | None = None
    owner_approved: bool = False


@dataclass(frozen=True)
class Verdict:
    ok: bool
    action: str
    ledger_seq: int
    network_mode: str
    detail: str = ""


class P0ExecutionGate:
    def __init__(
        self,
        *,
        ledger: IntentLedger,
        kill: KillSwitch,
        budget: OverlayBudget,
        taint: TaskTaintLatch,
        leases: LeaseStore | None = None,
        execute_fn: Callable[[Action], Any] | None = None,
    ) -> None:
        self.ledger = ledger
        self.kill = kill
        self.budget = budget
        self.taint = taint
        self.leases = leases
        self.execute_fn = execute_fn

    def admit_and_run(self, action: Action) -> Verdict:
        self.kill.assert_clear()
        deny_forbidden(action.name)

        if action.untrusted_input:
            self.taint.mark(action.task_id, action.untrusted_source or "untrusted")
        net = self.taint.network_mode(action.task_id, action.network_requested)
        if self.taint.is_tainted(action.task_id) and action.network_requested != "none":
            raise TaintNetworkDenied(
                f"G4 latch: task {action.task_id} tainted; network forced to none (requested {action.network_requested})"
            )

        if requires_owner(
            action.name,
            financial=action.financial,
            irreversible=action.irreversible,
            production=action.production,
        ) and not action.owner_approved:
            raise PolicyDenied("L3 owner approval required")

        self.budget.check_and_reserve(action.cost_cents)
        try:
            if action.lease is not None:
                if self.leases is None:
                    raise PolicyDenied("lease presented but store missing")
                self.leases.consume(action.lease, params=action.params, cost_cents=action.cost_cents)

            intent = self.ledger.append("INTENT", {
                "name": action.name,
                "actor": action.actor,
                "task_id": action.task_id,
                "cost_cents": action.cost_cents,
                "network_mode": net,
                "tainted": self.taint.is_tainted(action.task_id),
            })
        except Exception:
            self.budget.release(action.cost_cents)
            raise

        if self.execute_fn is None:
            self.budget.release(action.cost_cents)
            self.ledger.append("RESULT", {"seq": intent["seq"], "ok": False, "detail": "no executor"})
            raise PolicyDenied("no executor bound — P0 will not invent side effects")

        try:
            self.execute_fn(action)
        except Exception as exc:
            self.budget.release(action.cost_cents)
            self.ledger.append("RESULT", {"seq": intent["seq"], "ok": False, "detail": type(exc).__name__})
            raise

        self.budget.settle(action.cost_cents)
        self.ledger.append("RESULT", {"seq": intent["seq"], "ok": True, "detail": "done"})
        return Verdict(ok=True, action=action.name, ledger_seq=int(intent["seq"]), network_mode=net, detail="done")
