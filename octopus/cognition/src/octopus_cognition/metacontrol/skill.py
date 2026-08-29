from collections import deque
from dataclasses import dataclass
from math import sqrt
from statistics import fmean, pstdev


@dataclass(frozen=True)
class SkillReport:
    score: float | None
    lower_bound: float | None
    samples: int
    eligible: bool
    reason: str
    calibration_error: float | None = None
    model_mse: float | None = None
    baseline_mse: float | None = None


class DomainSkillTracker:
    def __init__(self, window: int = 200, minimum: int = 50) -> None:
        self.window = window
        self.minimum = minimum
        self.ratios: deque[float] = deque(maxlen=window)
        self.model_losses: deque[float] = deque(maxlen=window)
        self.baseline_losses: deque[float] = deque(maxlen=window)

    def record(self, model_loss: float, baseline_loss: float) -> None:
        if model_loss < 0 or baseline_loss < 0:
            raise ValueError("loss must be non-negative")
        if model_loss <= 1e-12 and baseline_loss <= 1e-12:
            ratio = 1.0
        elif baseline_loss <= 1e-12:
            ratio = 100.0
        else:
            ratio = model_loss / baseline_loss
        self.ratios.append(min(ratio, 100.0))
        self.model_losses.append(model_loss)
        self.baseline_losses.append(baseline_loss)

    def loads(self, payload: dict) -> None:
        self.ratios.clear()
        self.model_losses.clear()
        self.baseline_losses.clear()
        for row in payload.get("ratios") or []:
            self.ratios.append(float(row))
        for row in payload.get("model_losses") or []:
            self.model_losses.append(float(row))
        for row in payload.get("baseline_losses") or []:
            self.baseline_losses.append(float(row))

    def dumps(self) -> dict:
        return {
            "ratios": list(self.ratios),
            "model_losses": list(self.model_losses),
            "baseline_losses": list(self.baseline_losses),
            "window": self.window,
            "minimum": self.minimum,
        }

    def report(self) -> SkillReport:
        n = len(self.ratios)
        if n < self.minimum:
            return SkillReport(None, None, n, False, "insufficient_samples")

        scores = [1.0 - ratio for ratio in self.ratios]
        score = fmean(scores)
        spread = pstdev(scores) if n > 1 else float("inf")
        standard_error = spread / sqrt(n) if n > 1 else float("inf")
        lower = score - 1.96 * standard_error
        eligible = lower > 0.0
        model_mse = fmean(self.model_losses) if self.model_losses else None
        baseline_mse = fmean(self.baseline_losses) if self.baseline_losses else None
        return SkillReport(
            score=score,
            lower_bound=lower,
            samples=n,
            eligible=eligible,
            reason="skill_confirmed" if eligible else "not_better_than_baseline",
            calibration_error=None,
            model_mse=model_mse,
            baseline_mse=baseline_mse,
        )
