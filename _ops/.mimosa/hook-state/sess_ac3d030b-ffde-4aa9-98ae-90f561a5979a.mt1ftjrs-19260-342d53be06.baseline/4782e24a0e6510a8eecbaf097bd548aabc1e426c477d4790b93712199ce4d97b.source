"""Metacontrol Gate — domain skill scores. Never sets executable True."""
from __future__ import annotations

from typing import Any

from .observation import Observation, Quality

SCORE_WEIGHTS_V1 = {
    "version": "skill-weights.v1",
    "evidence_coverage": 0.20,
    "freshness": 0.15,
    "calibration": 0.15,
    "stability": 0.10,
    "agreement": 0.10,
    "restart_readiness": 0.15,
    "ood_risk_inv": 0.05,
    "contradiction_penalty": 0.10,
}

DOMAINS = (
    "telemetry_interpretation",
    "homeostasis",
    "identity_assessment",
    "judge_reliability",
    "life_currency_accounting",
    "world_state_estimation",
)

D6 = "BETWEEN_RUN_VARIANCE"
GAP_001 = "OPEN"


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def _score_vector(obs: list[Observation], assessment: dict[str, Any], world: dict[str, Any], domain: str) -> dict[str, Any]:
    n = max(1, len(obs))
    valid = sum(1 for o in obs if o.quality == Quality.VALID.value)
    stale = sum(1 for o in obs if o.quality == Quality.STALE.value)
    warmup = any(o.quality == Quality.WARMUP.value for o in obs)
    conflict = any(o.quality == Quality.CONFLICTING.value for o in obs)
    future = any(o.quality == Quality.FUTURE_DATA.value for o in obs)
    unit_bad = any(o.quality == Quality.UNIT_MISMATCH.value for o in obs)
    coverage = valid / n
    freshness = 1.0 - (stale / n)
    calibration = 0.5 if domain == "judge_reliability" else 0.8
    stability = 0.4 if warmup else 0.7
    agreement = 0.0 if conflict else 0.8
    restart_readiness = 0.2 if warmup else 0.8
    ood_risk = 0.6 if future else 0.2
    cpen = 0.8 if (assessment.get("contradictions") or conflict) else 0.0
    w = SCORE_WEIGHTS_V1
    final = (
        w["evidence_coverage"] * coverage
        + w["freshness"] * freshness
        + w["calibration"] * calibration
        + w["stability"] * stability
        + w["agreement"] * agreement
        + w["restart_readiness"] * restart_readiness
        + w["ood_risk_inv"] * (1.0 - ood_risk)
        - w["contradiction_penalty"] * cpen
    )
    reasons = [
        f"weights={w['version']}",
        f"coverage={coverage:.3f}",
        f"freshness={freshness:.3f}",
        f"restart_readiness={restart_readiness:.3f}",
        f"D6={D6}",
        f"GAP-001={GAP_001}",
    ]
    return {
        "domain": domain,
        "evidence_coverage": round(coverage, 4),
        "freshness": round(freshness, 4),
        "calibration": calibration,
        "stability": stability,
        "agreement": agreement,
        "restart_readiness": restart_readiness,
        "ood_risk": ood_risk,
        "contradiction_penalty": cpen,
        "final_score": round(_clip(final), 4),
        "confidence": round(coverage * freshness, 4),
        "reasons": reasons,
        "evidence_ids": [o.observation_id for o in obs],
        "weights_version": w["version"],
        "block_flags": {
            "future": future,
            "unit_mismatch": unit_bad,
            "conflicting": conflict,
            "warmup": warmup,
        },
    }


def _mode(vec: dict[str, Any], domain: str, assessment: dict[str, Any]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    flags = vec["block_flags"]
    if flags["future"]:
        blockers.append("FUTURE_DATA")
    if flags["unit_mismatch"]:
        blockers.append("UNIT_MISMATCH")
    if flags["conflicting"]:
        blockers.append("CONFLICTING")
    if GAP_001 == "OPEN":
        blockers.append("GAP-001_OPEN")
    cons = assessment.get("contradictions") or []
    if any("C-042" in str(c) for c in cons) and domain == "life_currency_accounting":
        blockers.append("C-042_STARVATION")
    hard = {"FUTURE_DATA", "UNIT_MISMATCH", "CONFLICTING", "C-042_STARVATION"} & set(blockers)
    if hard:
        return "BLOCK", blockers
    if flags["warmup"]:
        return "SHADOW", blockers + ["WARMUP_MAX_SHADOW"]
    if domain == "judge_reliability":
        return "ADVISORY", blockers + ["D6_BETWEEN_RUN_VARIANCE_CAP"]
    return "ADVISORY", blockers


def decide(
    observations: list[Observation],
    assessment: dict[str, Any],
    world: dict[str, Any],
) -> list[dict[str, Any]]:
    out = []
    for domain in DOMAINS:
        vec = _score_vector(observations, assessment, world, domain)
        mode, blockers = _mode(vec, domain, assessment)
        reasons = list(vec["reasons"]) + [f"mode={mode}"] + [f"blocker={b}" for b in blockers]
        out.append({
            "schema": "gate-decision.v1",
            "domain": domain,
            "skill_score": vec,
            "mode": mode,
            "executable": False,
            "blockers": blockers,
            "reasons": reasons,
            "assessment_id": assessment.get("assessment_id"),
            "world_state_id": world.get("state_id"),
        })
    return out


def assert_no_executable(decisions: list[dict[str, Any]]) -> int:
    n = 0
    for d in decisions:
        if d.get("executable") is True:
            n += 1
        ss = d.get("skill_score") or {}
        if ss.get("executable") is True:
            n += 1
    return n
