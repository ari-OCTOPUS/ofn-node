"""Coin scouting report generation.

No live network scraping here yet. This module scores user-supplied candidates.
"""
from __future__ import annotations

from .algo_classifier import classify_algorithm
from .models import CoinCandidate, GateResult, RiskLevel


def score_candidate(candidate: CoinCandidate) -> dict:
    algo = classify_algorithm(candidate.algorithm)
    age = candidate.age_days()
    reasons: list[str] = []
    score = 0

    if algo.arm_viable:
        score += 30
        reasons.append("CPU/ARM viable algorithm")
    else:
        reasons.append(algo.rationale)

    if age is not None and 0 <= age <= 90:
        score += 20
        reasons.append("launch age <= 90 days")
    elif age is None:
        reasons.append("launch age unknown")
    else:
        reasons.append(f"launch age {age}d outside preferred <=90d window")

    if candidate.dev_activity_notes.strip():
        score += 15
        reasons.append("dev activity evidence present")
    else:
        reasons.append("dev activity evidence missing")

    if candidate.community_notes.strip():
        score += 10
        reasons.append("community evidence present")
    else:
        reasons.append("community evidence missing")

    if candidate.quantum_resistance_claim:
        score += 5
        reasons.append("quantum-resistance claim present; verify separately")

    if candidate.network_hashrate_hs is not None:
        score += 10
        reasons.append("network hashrate provided")
    else:
        reasons.append("network hashrate missing; cannot estimate fleet share")

    if candidate.block_reward is not None and candidate.blocks_per_day is not None:
        score += 10
        reasons.append("emission data provided")
    else:
        reasons.append("block reward / blocks per day missing")

    risk = RiskLevel.GREEN if score >= 70 else RiskLevel.YELLOW if score >= 45 else RiskLevel.ORANGE
    if not algo.arm_viable:
        risk = RiskLevel.RED

    return {
        "symbol": candidate.symbol,
        "name": candidate.name,
        "score": min(score, 100),
        "risk": risk.value,
        "algorithm": candidate.algorithm,
        "arm_viable": algo.arm_viable,
        "algo_category": algo.category,
        "reasons": reasons,
        "sources": candidate.source_urls,
    }


def candidate_gate(candidate: CoinCandidate) -> GateResult:
    scored = score_candidate(candidate)
    passed = scored["arm_viable"] and scored["score"] >= 45
    return GateResult(
        name=f"COIN_SCOUT:{candidate.symbol}",
        passed=passed,
        risk=RiskLevel(scored["risk"]),
        message=(
            "Candidate is suitable for a DRAFT report. Human verdict still required."
            if passed
            else "Candidate is not ready for an experiment proposal."
        ),
        evidence=scored["reasons"],
    )
