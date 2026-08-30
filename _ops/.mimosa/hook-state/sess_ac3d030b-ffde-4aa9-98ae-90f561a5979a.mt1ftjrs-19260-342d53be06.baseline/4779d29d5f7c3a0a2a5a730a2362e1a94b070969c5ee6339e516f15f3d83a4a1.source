#!/usr/bin/env python3
"""rhythm.py — CR-B0/CR-B1: هستهٔ عددیِ ریتم (آفلاین، $0).

رفتارِ زندهٔ CR-B0 (قفل‌شده با تست):
  T_beat = T0 · exp(+κ·readiness − λ·stress) · (1 + ε·ξ_{1/f})
  HRV = std(ΔT_beat)  ·  dτ = γ·dt  ·  mode = Φ(HRV, σ, stress)
  γ = 1 + a·novelty − b·stress

CR-B1 فقط helper ریاضیِ pure برای پارامتر نظم/گام Kuramoto است؛ هیچ منبع فاز
runtime اختراع نمی‌کند و به scheduler وصل نیست.

خطوط قرمز:
  - age_tick و hash-chain لجر با rhythm on/off یکسان می‌ماند (TINV-3/7)
  - هسته هیچ IO/network/settle/gate/money ندارد
  - نویز bounded + seeded و replayپذیر است
  - human-HRV واقعی این‌جا وارد نمی‌شود
"""
from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from typing import Iterable, Sequence

CR_B0_FORMULA_VERSION = "chrono_rhythm.cr-b0.v1"
CR_B1_FORMULA_VERSION = "chrono_rhythm.cr-b1.kuramoto.v1"
DEFAULT_MIN_PERIOD_S = 1.0
DEFAULT_MAX_PERIOD_S = 300.0
MAX_NOISE_EPS = 0.2


def _finite(value, default: float) -> float:
    """float محدود یا default؛ UNKNOWN عددی هرگز به NaN/Inf نشت نمی‌کند."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float(default)
    return out if math.isfinite(out) else float(default)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


class FractalNoise:
    """تقریب سبک 1/f از white noise فیلترشده، bounded و seeded."""

    def __init__(self, seed: int = 42, alpha: float = 1.0, cap: float = 1.0):
        self.rng = random.Random(seed)
        self.alpha = _finite(alpha, 1.0)
        self.cap = max(0.0, _finite(cap, 1.0))
        self._prev = 0.0

    def sample(self) -> float:
        white = self.rng.gauss(0, 1)
        self._prev = 0.97 * self._prev + 0.03 * white
        val = _finite(self._prev * self.alpha, 0.0)
        return _clamp(val, -self.cap, self.cap)


@dataclass
class RhythmState:
    """state درون‌حافظه‌ای ریتم؛ خودش هیچ authority یا IO ندارد."""

    T_beat: float = 60.0
    hrv: float = 5.0
    tau: float = 0.0
    gamma: float = 1.0
    mode_focus: str = "STEADY"
    mode_color: str = "GREEN"
    coherence_r: float | None = None
    noise_D: float = 0.0
    readiness: float = 0.5
    stress: float = 0.0
    novelty: float = 0.0


def kuramoto_order_parameter(phases: Iterable[float]) -> float | None:
    """پارامتر نظم ``r = |Σ exp(iθ)| / N``؛ خالی=UNKNOWN، N=1 برابر 1.

    ورودی non-finite دادهٔ معتبر نیست و به‌جای coherence جعلی ``None`` می‌دهد.
    """
    values = []
    try:
        for phase in phases:
            p = float(phase)
            if not math.isfinite(p):
                return None
            values.append(p)
    except (TypeError, ValueError):
        return None
    if not values:
        return None
    n = float(len(values))
    re = sum(math.cos(p) for p in values) / n
    im = sum(math.sin(p) for p in values) / n
    return _clamp(math.hypot(re, im), 0.0, 1.0)


def kuramoto_step(
    phases: Sequence[float],
    natural_frequencies: Sequence[float],
    coupling: float,
    *,
    dt: float = 1.0,
) -> tuple[tuple[float, ...], float | None]:
    """یک Euler-step خالص از مدل Kuramoto؛ فقط CR-B1 آفلاین.

    پیکربندی بد (طول نابرابر، NaN/Inf، dt منفی) با ``ValueError`` روشن رد
    می‌شود. ورودی خالی ``((), None)`` است. خروجی فازها به ``[0, 2π)`` نرمال
    و r از فازهای تازه محاسبه می‌شود.
    """
    try:
        theta = tuple(float(x) for x in phases)
        omega = tuple(float(x) for x in natural_frequencies)
        k = float(coupling)
        step_dt = float(dt)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid Kuramoto numeric input") from exc
    if len(theta) != len(omega):
        raise ValueError("phases and natural_frequencies must have equal length")
    if not theta:
        return (), None
    if (not math.isfinite(k) or not math.isfinite(step_dt) or step_dt < 0
            or any(not math.isfinite(x) for x in theta + omega)):
        raise ValueError("Kuramoto inputs must be finite and dt non-negative")

    n = len(theta)
    updated = []
    for j, phase_j in enumerate(theta):
        coupling_term = (k / n) * sum(
            math.sin(phase_k - phase_j) for phase_k in theta
        )
        updated.append((phase_j + step_dt * (omega[j] + coupling_term)) % (2 * math.pi))
    out = tuple(updated)
    return out, kuramoto_order_parameter(out)


class Rhythm:
    """CR-B0: T_beat + HRV + τ + mode؛ بدون IO و بدون authority مستقیم."""

    def __init__(
        self,
        T0: float = 60.0,
        kappa: float = 0.5,
        lam: float = 0.3,
        eps: float = 0.15,
        seed: int = 42,
        hrv_window: int = 20,
        min_period_s: float = DEFAULT_MIN_PERIOD_S,
        max_period_s: float = DEFAULT_MAX_PERIOD_S,
    ):
        self.T0 = max(DEFAULT_MIN_PERIOD_S, _finite(T0, 60.0))
        self.kappa = _finite(kappa, 0.5)
        self.lam = _finite(lam, 0.3)
        self.eps = _clamp(_finite(eps, 0.15), 0.0, MAX_NOISE_EPS)
        self.noise = FractalNoise(seed=seed)
        try:
            window = int(hrv_window)
        except (TypeError, ValueError):
            window = 20
        self.hrv_window = max(2, window)
        lo = max(DEFAULT_MIN_PERIOD_S, _finite(min_period_s, DEFAULT_MIN_PERIOD_S))
        hi = max(lo, _finite(max_period_s, DEFAULT_MAX_PERIOD_S))
        self.min_period_s = lo
        self.max_period_s = hi
        self._beat_times: deque[float] = deque(maxlen=self.hrv_window)
        self.state = RhythmState(T_beat=_clamp(self.T0, lo, hi))

    def beat_interval(self, readiness: float, stress: float) -> float:
        """دورهٔ bounded؛ readiness بیشتر کندتر، stress بیشتر سریع‌تر."""
        ready = _clamp(_finite(readiness, 0.5), 0.0, 1.0)
        strain = _clamp(_finite(stress, 0.0), 0.0, 1.0)
        xi = self.noise.sample()
        exponent = _clamp(self.kappa * ready - self.lam * strain, -20.0, 20.0)
        base = self.T0 * math.exp(exponent)
        period = base * (1.0 + self.eps * xi)
        return _clamp(_finite(period, self.T0), self.min_period_s, self.max_period_s)

    def step(
        self,
        readiness: float,
        stress: float,
        novelty: float,
        dt: float = 1.0,
        sigma: float = 0.5,
    ) -> RhythmState:
        """یک گام CR-B0؛ UNKNOWNها sanitize می‌شوند و خروجی همیشه finite است."""
        ready = _clamp(_finite(readiness, 0.5), 0.0, 1.0)
        strain = _clamp(_finite(stress, 0.0), 0.0, 1.0)
        novel = _clamp(_finite(novelty, 0.0), 0.0, 1.0)
        step_dt = max(0.0, _finite(dt, 0.0))
        sigma_value = max(0.0, _finite(sigma, 0.5))

        T = self.beat_interval(ready, strain)
        self._beat_times.append(T)
        if len(self._beat_times) >= 2:
            deltas = [
                self._beat_times[i] - self._beat_times[i - 1]
                for i in range(1, len(self._beat_times))
            ]
            mean_d = sum(deltas) / len(deltas)
            hrv = math.sqrt(sum((d - mean_d) ** 2 for d in deltas) / len(deltas))
        else:
            hrv = 0.0
        hrv = max(0.0, _finite(hrv, 0.0))

        gamma = _clamp(1.0 + 0.3 * novel - 0.4 * strain, 0.1, 2.0)
        tau = _finite(self.state.tau + gamma * step_dt, self.state.tau)
        focus, color = self._mode_map(hrv, sigma_value, strain)

        self.state.T_beat = T
        self.state.hrv = hrv
        self.state.gamma = gamma
        self.state.tau = tau
        self.state.mode_focus = focus
        self.state.mode_color = color
        self.state.readiness = ready
        self.state.stress = strain
        self.state.novelty = novel
        return self.state

    def _mode_map(self, hrv: float, sigma: float, stress: float) -> tuple[str, str]:
        if stress > 0.8 or sigma > 0.95:
            color = "RED"
        elif stress > 0.5 or sigma > 0.8 or hrv < 0.2:
            color = "AMBER"
        else:
            color = "GREEN"
        if color == "RED":
            focus = "CALM"
        elif 0.3 < stress < 0.7:
            focus = "FOCUSED"
        else:
            focus = "STEADY"
        return focus, color

    def hrv_alarm(self) -> dict | None:
        if len(self._beat_times) >= 5 and self.state.hrv < 0.5:
            return {
                "type": "hrv-collapse",
                "hrv": round(self.state.hrv, 3),
                "detail": "HRV پایین — rigidity/stress",
            }
        return None

    def advisory(self) -> dict:
        """snapshot خودِ signal؛ authority مستقیم ندارد."""
        s = self.state
        return {
            "T_beat": round(s.T_beat, 2),
            "hrv": round(s.hrv, 3),
            "tau": round(s.tau, 2),
            "gamma": round(s.gamma, 3),
            "mode": f"{s.mode_focus}/{s.mode_color}",
            "coherence_r": (
                None if s.coherence_r is None else round(s.coherence_r, 3)
            ),
            "noise_D": round(s.noise_D, 3),
            "formula_version": CR_B0_FORMULA_VERSION,
            "advisory_only": True,
        }
