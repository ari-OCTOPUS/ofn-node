"""Skill uncertainty for serially correlated telemetry.

IID bootstrap understates uncertainty when consecutive samples are dependent.
Use moving-block bootstrap. Missing evidence is a failed gate, not a missing CI.
"""

from __future__ import annotations

from typing import Any, Sequence


def default_block_size(n: int) -> int:
    if n <= 0:
        return 1
    return max(5, min(n, int(n**0.5)))


def skill_from_losses(candidate_loss: float, baseline_loss: float) -> float:
    if baseline_loss <= 1e-12 and candidate_loss <= 1e-12:
        return 0.0
    if baseline_loss <= 1e-12:
        return -100.0
    return 1.0 - candidate_loss / baseline_loss


def _skill_of_sample(sample: Sequence[dict[str, Any]]) -> float:
    n = len(sample)
    cand = sum(float(p["candidate_loss"]) for p in sample) / n
    base = sum(float(p["persistence_loss"]) for p in sample) / n
    return skill_from_losses(cand, base)


def iid_bootstrap_skill(
    pairs: Sequence[dict[str, Any]],
    rounds: int = 1000,
    seed: int = 266,
) -> dict[str, float | int | None | str]:
    """IID resample. Forbidden as the acceptance CI for live telemetry."""
    import random

    n = len(pairs)
    if n < 50:
        return {
            "method": "iid_bootstrap",
            "point": None,
            "lower": None,
            "upper": None,
            "rounds": 0,
            "usable": False,
            "reason": "insufficient_samples",
        }
    rng = random.Random(seed)
    scores: list[float] = []
    for _ in range(rounds):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        scores.append(_skill_of_sample(sample))
    scores.sort()
    return {
        "method": "iid_bootstrap",
        "point": sum(scores) / rounds,
        "lower": scores[int(0.025 * (rounds - 1))],
        "upper": scores[int(0.975 * (rounds - 1))],
        "rounds": rounds,
        "usable": True,
        "acceptance": "FORBIDDEN_FOR_SERIAL_TELEMETRY",
    }


def block_bootstrap_skill(
    pairs: Sequence[dict[str, Any]],
    rounds: int = 1000,
    seed: int = 266,
    block_size: int | None = None,
) -> dict[str, float | int | None | str]:
    """Moving-block bootstrap. Contiguous telemetry stays contiguous."""
    import random

    n = len(pairs)
    if n < 50:
        return {
            "method": "block_bootstrap",
            "point": None,
            "lower": None,
            "upper": None,
            "rounds": 0,
            "block_size": None,
            "usable": False,
            "reason": "insufficient_samples",
        }
    L = int(block_size) if block_size is not None else default_block_size(n)
    L = max(1, min(L, n))
    rng = random.Random(seed)
    max_start = n - L
    n_blocks = (n + L - 1) // L
    scores: list[float] = []
    for _ in range(rounds):
        sample: list[dict[str, Any]] = []
        for _b in range(n_blocks):
            start = rng.randint(0, max_start)
            sample.extend(pairs[start : start + L])
        sample = sample[:n]
        scores.append(_skill_of_sample(sample))
    scores.sort()
    return {
        "method": "block_bootstrap",
        "point": sum(scores) / rounds,
        "lower": scores[int(0.025 * (rounds - 1))],
        "upper": scores[int(0.975 * (rounds - 1))],
        "rounds": rounds,
        "block_size": L,
        "usable": True,
        "acceptance": "REQUIRED_FOR_SERIAL_TELEMETRY",
    }


def complementary_metrics(
    pairs: Sequence[dict[str, Any]],
    *,
    calibration_error: float | None,
    missingness_rate: float | None,
    per_domain_skill: dict[str, float | None] | None = None,
) -> dict[str, Any]:
    domains = per_domain_skill or {}
    worst = None
    named = [v for v in domains.values() if v is not None]
    if named:
        worst = min(named)
    return {
        "calibration_error": calibration_error,
        "missingness_rate": missingness_rate,
        "per_domain_skill": domains,
        "per_domain_worst_case_skill": worst,
        "skill_is_not_sole_criterion": True,
    }


def m2_evidence_permitted(m1_gate_result: str) -> bool:
    """Skill on a Doctor-FAIL system is not evidence. M1 is a hard prerequisite."""
    return m1_gate_result == "PASS"
