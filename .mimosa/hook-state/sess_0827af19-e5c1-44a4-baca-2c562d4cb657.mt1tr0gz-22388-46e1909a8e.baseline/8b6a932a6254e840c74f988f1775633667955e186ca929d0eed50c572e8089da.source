"""Death-watch evaluation following project rule D2."""
from __future__ import annotations

from .constants import DEFAULT_DEV_DEAD_WEEKS_THRESHOLD
from .models import DeathWatch, GateResult, RiskLevel


def evaluate_death_watch(dw: DeathWatch) -> GateResult:
    evidence = list(dw.evidence)
    if dw.dev_dead_weeks is not None and dw.dev_dead_weeks >= DEFAULT_DEV_DEAD_WEEKS_THRESHOLD:
        evidence.append(f"dev_dead_weeks={dw.dev_dead_weeks} >= {DEFAULT_DEV_DEAD_WEEKS_THRESHOLD}")
    if dw.chain_stalled is True:
        evidence.append("chain_stalled=true")
    if dw.community_dead is True:
        evidence.append("community_dead=true")

    if dw.abandon_flag:
        return GateResult(
            name=f"DEATH_WATCH:{dw.coin}",
            passed=False,
            risk=RiskLevel.RED,
            message="ABANDON proposal may be drafted: at least one D2 death criterion is met.",
            evidence=evidence,
        )
    unknowns = []
    if dw.dev_dead_weeks is None:
        unknowns.append("dev_dead_weeks")
    if dw.chain_stalled is None:
        unknowns.append("chain_stalled")
    if dw.community_dead is None:
        unknowns.append("community_dead")
    if unknowns:
        return GateResult(
            name=f"DEATH_WATCH:{dw.coin}",
            passed=False,
            risk=RiskLevel.ORANGE,
            message="Death-watch incomplete; cannot conclude survival or abandonment.",
            evidence=unknowns,
        )
    return GateResult(
        name=f"DEATH_WATCH:{dw.coin}",
        passed=True,
        risk=RiskLevel.GREEN,
        message="No D2 death criterion met. Payback/liquidity must not be used as kill criteria.",
        evidence=evidence,
    )
