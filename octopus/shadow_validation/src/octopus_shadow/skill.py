from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Sequence


@dataclass(frozen=True)
class SkillReport:
    score: float | None
    lower: float | None
    samples: int
    eligible: bool
    reason: str
    model_loss: float | None = None
    baseline_loss: float | None = None


def weighted_mse(prediction: Sequence[float], actual: Sequence[float], weights: Sequence[float]) -> float:
    error_sum = 0.0
    weight_sum = 0.0
    for pred, truth, weight in zip(prediction, actual, weights, strict=True):
        delta = float(pred) - float(truth)
        error_sum += float(weight) * delta * delta
        weight_sum += float(weight)
    if weight_sum <= 0:
        raise ValueError("weights must sum to a positive value")
    return error_sum / weight_sum


def _skill(model_loss: float, baseline_loss: float) -> float | None:
    if model_loss < 0 or baseline_loss < 0:
        raise ValueError("loss must be non-negative")
    if baseline_loss <= 1e-12 and model_loss <= 1e-12:
        return 0.0
    if baseline_loss <= 1e-12:
        return None
    return 1.0 - model_loss / baseline_loss


def calculate(
    model: Sequence[Sequence[float]],
    baseline: Sequence[Sequence[float]],
    actual: Sequence[Sequence[float]],
    weights: Sequence[float],
    min_samples: int = 50,
    bootstrap: int = 1000,
    seed: int = 42,
) -> SkillReport:
    n = len(actual)
    if not (len(model) == len(baseline) == n):
        raise ValueError("paired sample lengths must match")
    if n < min_samples:
        return SkillReport(None, None, n, False, "insufficient_samples")

    model_losses = [weighted_mse(m, a, weights) for m, a in zip(model, actual, strict=True)]
    baseline_losses = [weighted_mse(b, a, weights) for b, a in zip(baseline, actual, strict=True)]
    model_loss = sum(model_losses) / n
    baseline_loss = sum(baseline_losses) / n
    score = _skill(model_loss, baseline_loss)
    if score is None:
        return SkillReport(None, None, n, False, "baseline_loss_near_zero", model_loss, baseline_loss)

    rng = Random(seed)
    boot: list[float] = []
    for _ in range(max(1, bootstrap)):
        picks = [rng.randrange(n) for _ in range(n)]
        m = sum(model_losses[i] for i in picks) / n
        b = sum(baseline_losses[i] for i in picks) / n
        sample = _skill(m, b)
        if sample is not None:
            boot.append(sample)
    boot.sort()
    lower = boot[max(0, int(0.025 * (len(boot) - 1)))] if boot else None
    eligible = lower is not None and lower > 0.0
    return SkillReport(
        score=score,
        lower=lower,
        samples=n,
        eligible=eligible,
        reason="skill_confirmed" if eligible else "not_better_than_baseline",
        model_loss=model_loss,
        baseline_loss=baseline_loss,
    )
