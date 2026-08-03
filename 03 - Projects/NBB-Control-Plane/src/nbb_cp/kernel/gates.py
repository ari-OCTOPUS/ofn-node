"""Gates: pure decision functions. The kernel decides; adapters execute.

Triad: the Governor proposes, gates enforce, the human rules (INV-4). The
effector gate is the single choke point for anything that touches the world —
there is exactly one enforcement path, by design.

Every gate is fail-closed: unknown input, missing data, or violated
preconditions produce a denial, never a guess (INV-12).
"""

from __future__ import annotations

from typing import Mapping

from .budget import reserve
from .domain import (
    BudgetState,
    GateDecision,
    Mode,
    Organ,
    Proposal,
    ProposalKind,
    Verdict,
)
from .errors import CapExceededError, FailClosedError
from .sigma import sigma_allows_spawn


def budget_gate(state: BudgetState, proposal: Proposal, organs: Mapping[str, Organ]) -> GateDecision:
    """Admission check for GRANT proposals against the single global cap."""
    checks: list[str] = []
    if proposal.organ_id not in organs:
        return GateDecision(False, f"unknown organ {proposal.organ_id!r}", "INV-12", checks=("organ-known",))
    checks.append("organ-known")
    if proposal.amount.cents <= 0:
        return GateDecision(False, "amount must be positive", "INV-12", checks=tuple(checks))
    checks.append("amount-positive")
    try:
        reserve(state, proposal.amount)
    except CapExceededError as exc:
        return GateDecision(False, str(exc), "INV-1", checks=tuple(checks))
    except FailClosedError as exc:
        return GateDecision(False, str(exc), "INV-12", checks=tuple(checks))
    checks.append("cap-headroom")
    return GateDecision(True, "within cap", checks=tuple(checks))


def spawn_gate(proposal: Proposal, sigma: float, max_depth: int = 1) -> GateDecision:
    """Population discipline for SPAWN proposals (INV-6)."""
    if proposal.kind is not ProposalKind.SPAWN:
        return GateDecision(False, "spawn_gate only judges SPAWN proposals", "INV-12")
    if proposal.spawn_depth >= max_depth:
        return GateDecision(False, f"spawn depth {proposal.spawn_depth} at limit {max_depth}", "INV-6")
    if not sigma_allows_spawn(sigma):
        return GateDecision(False, f"sigma {sigma:.2f} > 1: replication frozen", "INV-6")
    return GateDecision(True, "spawn admissible pending human verdict", checks=("depth", "sigma"))


def effector_gate(
    proposal: Proposal,
    verdict: Verdict | None,
    mode: Mode,
    killed: bool,
) -> GateDecision:
    """The single choke point before any execution.

    Order matters: kill first (INV-3), then human sovereignty (INV-2), then
    mode. SPAWN and irreversible actions always need an approved verdict —
    self-reported success is never enough (INV-8).
    """
    if killed:
        return GateDecision(False, "kill switch engaged", "INV-3")
    needs_human = proposal.irreversible or proposal.kind is ProposalKind.SPAWN
    if needs_human:
        if verdict is None:
            return GateDecision(False, "human verdict required and absent", "INV-2")
        if verdict.proposal_id != proposal.proposal_id:
            return GateDecision(False, "verdict does not match proposal", "INV-12")
        if not verdict.approved:
            return GateDecision(False, f"denied by {verdict.by}", "INV-2")
    if mode is Mode.SHADOW:
        return GateDecision(True, "allowed in shadow: simulate, never execute", shadow=True)
    return GateDecision(True, "allowed live")
