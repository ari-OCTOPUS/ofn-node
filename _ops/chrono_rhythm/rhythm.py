#!/usr/bin/env python3
"""rhythm.py — CR-B0: لایهٔ ریتم (numeric core، آفلاین، $0).

CHRONO-RHYTHM-LAYER-SPEC §۳–§۶:
  T_beat = T0 · exp(−κ·readiness + λ·stress) · (1 + ε·ξ_{1/f})
  HRV = std(ΔT_beat)  ·  dτ = γ·dt  ·  mode = Φ(HRV, σ, stress)
  γ = 1 + a·novelty − b·stress

§۶ safety (نقض=رد):
  - age_tick و hash-chainِ لجر باید با rhythm on/off یکسان بماند (TINV-3/7)
  - rhythm فقط advisory، هیچ settle/gate-bypass/money
  - نویز 1/f بوجهٔ کران‌دار و seeded (تستِ بازتولیدپذیر)
  - هیچ human-HRV واقعی (پشتِ Security Gate است)
  - بدونِ import اثرِ production
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from collections import deque


# ─── 1/f noise (bounded، seeded) ───────────────────────────────────────────────
class FractalNoise:
    """نویزِ 1/f بوجهٔ کران‌دار. seeded (بازتولیدپذیر).
    محدود به [-1, 1]. الگو: filter white noise."""
    def __init__(self, seed: int = 42, alpha: float = 1.0, cap: float = 1.0):
        self.rng = random.Random(seed)
        self.alpha = alpha   # 1 = pink noise
        self.cap = cap
        self._prev = 0.0

    def sample(self) -> float:
        """یک نمونهٔ 1/f کران‌دار ∈ [-cap, cap]."""
        white = self.rng.gauss(0, 1)
        # simple 1/f: exponential filter (approximates pink)
        self._prev = 0.97 * self._prev + 0.03 * white
        val = self._prev * self.alpha
        return max(-self.cap, min(self.cap, val))


# ─── Rhythm state ──────────────────────────────────────────────────────────────
@dataclass
class RhythmState:
    """state ثابتِ ریتم در یک لحظه. advisory، نه effector."""
    T_beat: float = 60.0       # seconds
    hrv: float = 5.0           # std of ΔT
    tau: float = 0.0           # subjective time accumulator
    gamma: float = 1.0         # time dilation
    mode_focus: str = "STEADY"  # CALM | STEADY | FOCUSED
    mode_color: str = "GREEN"   # GREEN | AMBER | RED
    coherence_r: float = 0.5   # Kuramoto order param
    noise_D: float = 0.0       # stochastic resonance
    readiness: float = 0.5
    stress: float = 0.0
    novelty: float = 0.0


class Rhythm:
    """لایهٔ ریتم: T_beat + HRV + τ + mode. advisory فقط.
    invariant: rhythm on/off نباید لجر را تغییر دهد."""

    def __init__(self, T0: float = 60.0, kappa: float = 0.5, lam: float = 0.3,
                 eps: float = 0.15, seed: int = 42,
                 hrv_window: int = 20):
        self.T0 = T0
        self.kappa = kappa
        self.lam = lam
        self.eps = eps
        self.noise = FractalNoise(seed=seed)
        self.hrv_window = hrv_window
        self._beat_times: deque[float] = deque(maxlen=hrv_window)
        self.state = RhythmState(T_beat=T0)

    def beat_interval(self, readiness: float, stress: float) -> float:
        """T_beat = T0 · exp(κ·readiness − λ·stress) · (1 + ε·ξ).
        calm/ready → slower (deliberate); stressed → faster (reactive).
        high readiness = long deliberate beats; high stress = short reactive beats."""
        xi = self.noise.sample()
        base = self.T0 * math.exp(self.kappa * readiness - self.lam * stress)
        return max(1.0, base * (1 + self.eps * xi))

    def step(self, readiness: float, stress: float, novelty: float,
             dt: float = 1.0, sigma: float = 0.5) -> RhythmState:
        """یک گامِ ریتم. updates T_beat، HRV، τ، mode.
        advisory: هیچ اثرِ بیرونی."""
        # T_beat
        T = self.beat_interval(readiness, stress)
        self._beat_times.append(T)
        # HRV = std(ΔT)
        if len(self._beat_times) >= 2:
            deltas = [self._beat_times[i] - self._beat_times[i-1]
                      for i in range(1, len(self._beat_times))]
            mean_d = sum(deltas) / len(deltas)
            hrv = math.sqrt(sum((d - mean_d) ** 2 for d in deltas) / len(deltas))
        else:
            hrv = 0.0
        # γ = 1 + a·novelty − b·stress
        gamma = max(0.1, 1.0 + 0.3 * novelty - 0.4 * stress)
        # τ = ∫γ dt
        self.state.tau += gamma * dt
        # mode map
        focus, color = self._mode_map(hrv, sigma, stress)
        # update state
        self.state.T_beat = T
        self.state.hrv = hrv
        self.state.gamma = gamma
        self.state.tau = self.state.tau
        self.state.mode_focus = focus
        self.state.mode_color = color
        self.state.readiness = readiness
        self.state.stress = stress
        self.state.novelty = novelty
        return self.state

    def _mode_map(self, hrv: float, sigma: float, stress: float) -> tuple[str, str]:
        """Φ(HRV, σ, stress) → (focus, color).
        HRV↓ + σ→1 + stress↑ → RED/CALM (throttle).
        HRV↑ + σ safe + stress↓ → GREEN/STEADY.
        توجه: HRV بر اساس ΔT است — برای ضربان‌های یکنواخت ممکن است کوچک باشد،
        پس فقط وقتی RED می‌زنیم که stress/σ هم بحرانی باشند."""
        # color (health) — stress و σ ملاک اصلی، HRV کمک‌کننده
        if stress > 0.8 or sigma > 0.95:
            color = "RED"
        elif stress > 0.5 or sigma > 0.8 or hrv < 0.2:
            color = "AMBER"
        else:
            color = "GREEN"
        # focus
        if color == "RED":
            focus = "CALM"       # throttle، observe
        elif stress > 0.3 and stress < 0.7:
            focus = "FOCUSED"    # moderate stress = sharp
        else:
            focus = "STEADY"
        return focus, color

    def hrv_alarm(self) -> dict | None:
        """HRV collapse → rigidity/stress alarm (Warden/Doctor reads it)."""
        if len(self._beat_times) >= 5 and self.state.hrv < 0.5:
            return {"type": "hrv-collapse", "hrv": round(self.state.hrv, 3),
                    "detail": "HRV پایین — rigidity/stress"}
        return None

    def advisory(self) -> dict:
        """snapshot برای publish روی UnifiedBus. advisory فقط."""
        s = self.state
        return {"T_beat": round(s.T_beat, 2), "hrv": round(s.hrv, 3),
                "tau": round(s.tau, 2), "gamma": round(s.gamma, 3),
                "mode": f"{s.mode_focus}/{s.mode_color}",
                "coherence_r": round(s.coherence_r, 3),
                "noise_D": round(s.noise_D, 3),
                "advisory_only": True}   # علامت: هیچ settle
