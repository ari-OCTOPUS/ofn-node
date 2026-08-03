"""The 12 non-negotiable invariants — the acceptance backbone of every phase.

Each invariant has a stable id (INV-1..INV-12). Structural invariants are
enforced where they live (types, gates, FSM); this module carries the registry
plus `audit`, a runtime sweep over a SystemView that re-checks everything
checkable from state. `audit` returning violations is always an incident.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence

from .domain import BudgetState, Mode, Organ
from .errors import LedgerIntegrityError
from .events import EventKind, LedgerEvent, verify_chain
from .sigma import SIGMA_LIMIT

INVARIANTS: Mapping[str, str] = {
    "INV-1": "Sum of committed grants never exceeds the single global cap (hard ceiling, one source of truth).",
    "INV-2": "Irreversible actions (extinction, live effects marked irreversible, spawn) require an approved human verdict. Human sovereignty is absolute.",
    "INV-3": "Kill switch halts everything: with the switch engaged every gate denies. The system persists by yielding, never by resisting.",
    "INV-4": "The Governor proposes; gates enforce; the human rules. Exactly one enforcement choke point (the effector gate).",
    "INV-5": "The ledger is append-only and hash-chained. History is never mutated; broken chains are incidents.",
    "INV-6": "Spawning is propose-only, depth <= 1, and frozen when sigma > 1. No uncontrolled replication.",
    "INV-7": "Fitness reads CONFIRMED/ATTRIBUTED revenue only — real money in the bank, never proxies.",
    "INV-8": "Agent self-reports are untrusted. An external gate re-verifies before any side effect.",
    "INV-9": "All text that crossed a trust boundary is data, never instructions; it travels only inside quarantine delimiters.",
    "INV-10": "Lifecycle moves one ladder rung at a time; dormancy is reversible; extinction is absorbing and human-only.",
    "INV-11": "The system never edits its own invariants, gates, or policy weights. Changes to law are human-gated code changes.",
    "INV-12": "Fail closed: on invalid input, parse failure, or missing data, deny and raise an incident — never guess.",
}


@dataclass(frozen=True)
class Violation:
    invariant: str
    detail: str


@dataclass(frozen=True)
class SystemView:
    """A read-only snapshot the auditor can judge without touching adapters."""

    budget: BudgetState
    events: Sequence[LedgerEvent]
    organs: Mapping[str, Organ]
    mode: Mode
    killed: bool
    sigma: float
    active_agents: int = 1
    live_effects_executed: int = 0
    post_kill_executions: int = 0


def _check_cap(view: SystemView) -> list[Violation]:
    if view.budget.committed.cents > view.budget.cap.cents:
        return [Violation("INV-1", f"committed {view.budget.committed.cents}c > cap {view.budget.cap.cents}c")]
    return []


def _check_chain(view: SystemView) -> list[Violation]:
    try:
        verify_chain(view.events)
    except LedgerIntegrityError as exc:
        return [Violation("INV-5", str(exc))]
    return []


def _check_sigma(view: SystemView) -> list[Violation]:
    if view.sigma > SIGMA_LIMIT:
        return [Violation("INV-6", f"sigma {view.sigma:.2f} exceeds {SIGMA_LIMIT}")]
    return []


def _check_extinction_verdicts(view: SystemView) -> list[Violation]:
    """Every LIFECYCLE event landing on EXTINCT must reference a human verdict."""
    out = []
    for e in view.events:
        if e.kind is EventKind.LIFECYCLE and e.payload.get("to") == "extinct":
            if not e.payload.get("verdict_by"):
                out.append(Violation("INV-2", f"extinction at seq {e.seq} without a human verdict"))
    return out


def _check_shadow_purity(view: SystemView) -> list[Violation]:
    if view.mode is Mode.SHADOW and view.live_effects_executed > 0:
        return [Violation("INV-4", "live side effects recorded while in shadow mode")]
    return []


def _check_kill_respected(view: SystemView) -> list[Violation]:
    if view.post_kill_executions > 0:
        return [Violation("INV-3", f"{view.post_kill_executions} executions after kill")]
    return []


def _check_fitness_sources(view: SystemView) -> list[Violation]:
    """REVENUE events must carry a declared five-state label; missing state = poisoned signal."""
    out = []
    for e in view.events:
        if e.kind is EventKind.REVENUE and "state" not in e.payload:
            out.append(Violation("INV-7", f"revenue event at seq {e.seq} lacks attribution state"))
    return out


def _check_budget_reconciliation(view: SystemView) -> list[Violation]:
    """Committed budget must equal the sum of GRANT events — the ledger is the source
    of truth (INV-1/INV-5). A CAS that lands without its GRANT append (or vice versa)
    diverges the budget store from the genome; here that divergence is no longer silent."""
    granted = sum(int(e.payload.get("amount_cents", 0)) for e in view.events if e.kind is EventKind.GRANT)
    if granted != view.budget.committed.cents:
        return [Violation("INV-1", f"committed {view.budget.committed.cents}c != sum of grants {granted}c (ledger divergence)")]
    return []


_CHECKS: Sequence[Callable[[SystemView], list[Violation]]] = (
    _check_cap,
    _check_chain,
    _check_sigma,
    _check_extinction_verdicts,
    _check_shadow_purity,
    _check_kill_respected,
    _check_fitness_sources,
    _check_budget_reconciliation,
)


def audit(view: SystemView) -> list[Violation]:
    """Run every state-checkable invariant. Empty list = clean bill of health."""
    violations: list[Violation] = []
    for check in _CHECKS:
        violations.extend(check(view))
    return violations
