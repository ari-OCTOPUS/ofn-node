"""CPU/ARM mining algorithm classifier.

This is deliberately conservative and report-only.
"""
from __future__ import annotations

from dataclasses import dataclass

from .constants import CPU_ARM_PREFERRED_ALGOS, GPU_OR_ASIC_DOMINATED_ALGOS
from .models import RiskLevel


@dataclass(frozen=True)
class AlgoAssessment:
    algorithm: str
    arm_viable: bool
    category: str
    risk: RiskLevel
    rationale: str
    suggested_miner: str | None = None


def classify_algorithm(algorithm: str) -> AlgoAssessment:
    algo = (algorithm or "").strip().lower()
    if not algo:
        return AlgoAssessment(
            algorithm=algorithm,
            arm_viable=False,
            category="unknown",
            risk=RiskLevel.ORANGE,
            rationale="Algorithm missing; cannot prove CPU/ARM viability.",
        )

    if algo in CPU_ARM_PREFERRED_ALGOS or any(a in algo for a in CPU_ARM_PREFERRED_ALGOS):
        miner = "xmrig" if "random" in algo or algo.startswith("rx") else "cpuminer/ccminer-arm64"
        return AlgoAssessment(
            algorithm=algorithm,
            arm_viable=True,
            category="cpu_arm_preferred",
            risk=RiskLevel.YELLOW,
            rationale="Algorithm is known as CPU/ARM-viable, but real hashrate/watt must be measured on local hardware.",
            suggested_miner=miner,
        )

    if algo in GPU_OR_ASIC_DOMINATED_ALGOS or any(a in algo for a in GPU_OR_ASIC_DOMINATED_ALGOS):
        return AlgoAssessment(
            algorithm=algorithm,
            arm_viable=False,
            category="gpu_or_asic_dominated",
            risk=RiskLevel.RED,
            rationale="Algorithm is likely GPU/ASIC dominated; not suitable for OPi5 CPU fleet except as research.",
        )

    return AlgoAssessment(
        algorithm=algorithm,
        arm_viable=False,
        category="needs_manual_review",
        risk=RiskLevel.ORANGE,
        rationale="Algorithm is not in the local allow/deny table. Manual verification required before any experiment proposal.",
    )
