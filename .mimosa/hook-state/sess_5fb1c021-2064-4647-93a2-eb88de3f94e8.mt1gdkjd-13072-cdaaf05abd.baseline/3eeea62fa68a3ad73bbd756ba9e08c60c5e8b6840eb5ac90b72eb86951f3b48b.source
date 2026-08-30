"""Governance gates for the Mining project.

Important: this is a policy/checking module only. It does not perform execution.
"""
from __future__ import annotations

from collections.abc import Iterable

from .constants import ELECTRICITY_CEILING_USD_PER_KWH, HARD_GATED_ACTIONS
from .models import GateResult, HardwareNode, RiskLevel, VerdictItem, DecisionStatus


class GovernanceError(RuntimeError):
    """Raised when a caller requests a forbidden action."""


def assert_action_allowed(action: str) -> None:
    """Fail closed for all hard-gated action names."""
    if action in HARD_GATED_ACTIONS:
        raise GovernanceError(
            f"Action '{action}' is hard-gated in Mining. Human verdict required; agents are INFORM-only."
        )


def verdict_queue_gate(items: Iterable[VerdictItem]) -> GateResult:
    open_items = [i.id for i in items if i.status == DecisionStatus.OPEN]
    if open_items:
        return GateResult(
            name="VERDICT_QUEUE",
            passed=False,
            risk=RiskLevel.RED,
            message=f"Execution locked: {len(open_items)} verdict item(s) still open.",
            evidence=open_items,
        )
    return GateResult(
        name="VERDICT_QUEUE",
        passed=True,
        risk=RiskLevel.GREEN,
        message="All verdict items are closed.",
    )


def electricity_gate(nodes: Iterable[HardwareNode]) -> GateResult:
    nodes = list(nodes)
    if not nodes:
        return GateResult(
            name="ELECTRICITY",
            passed=False,
            risk=RiskLevel.RED,
            message="No hardware nodes registered; electricity cost/source cannot be verified.",
        )
    unsafe = []
    unknown = []
    for n in nodes:
        if n.power_source.value == "unknown" or n.electricity_cost_usd_kwh is None and n.power_source.value not in {"solar", "free"}:
            unknown.append(n.node_id)
        elif not n.is_electricity_safe:
            unsafe.append(f"{n.node_id}={n.electricity_cost_usd_kwh}")
    if unsafe:
        return GateResult(
            name="ELECTRICITY",
            passed=False,
            risk=RiskLevel.RED,
            message=f"Mining HALT: electricity exceeds ${ELECTRICITY_CEILING_USD_PER_KWH}/kWh for at least one node.",
            evidence=unsafe,
        )
    if unknown:
        return GateResult(
            name="ELECTRICITY",
            passed=False,
            risk=RiskLevel.ORANGE,
            message="Electricity source/cost unknown for some nodes; cannot enter execution.",
            evidence=unknown,
        )
    return GateResult(
        name="ELECTRICITY",
        passed=True,
        risk=RiskLevel.GREEN,
        message="All registered nodes pass electricity gate or are solar/free.",
    )


def wallet_gate(zero_agent_access_confirmed: bool) -> GateResult:
    if not zero_agent_access_confirmed:
        return GateResult(
            name="WALLET_ZERO_ACCESS",
            passed=False,
            risk=RiskLevel.RED,
            message="Wallet zero-access policy not confirmed. Execution locked.",
        )
    return GateResult(
        name="WALLET_ZERO_ACCESS",
        passed=True,
        risk=RiskLevel.GREEN,
        message="Wallet access policy confirmed: zero agent access.",
    )


def aggregate_gates(gates: Iterable[GateResult]) -> GateResult:
    gates = list(gates)
    failed = [g for g in gates if not g.passed]
    if failed:
        risk_order = {RiskLevel.GREEN: 0, RiskLevel.YELLOW: 1, RiskLevel.ORANGE: 2, RiskLevel.RED: 3}
        worst = max((g.risk for g in failed), key=lambda r: risk_order[r])
        return GateResult(
            name="EXECUTION_READINESS",
            passed=False,
            risk=worst,
            message="Execution is NOT allowed. Failed gates: " + ", ".join(g.name for g in failed),
            evidence=[f"{g.name}: {g.message}" for g in failed],
        )
    return GateResult(
        name="EXECUTION_READINESS",
        passed=True,
        risk=RiskLevel.GREEN,
        message="All pre-execution gates passed. Human still must approve any actual experiment.",
    )
