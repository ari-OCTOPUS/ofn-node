#!/usr/bin/env python3
"""warden.py — Part 3/1: Warden = policy + 2% cap + kill-switch.

E_box_max = 0.02 · E_total (hard). عبور → پایان cycle (fail-closed).
اطاعتِ بی‌قیدِ STOP. allostatic cooldown. ρ(J) monitoring.
هیچ import از production."""
from __future__ import annotations
import os
from pathlib import Path
from agent_state import AgentState


def _stop_file() -> Path:
    # canonical kill-switch = _ops/STOP-ORGANISM (همان مسیری که کلِ سیستم چک می‌کند).
    # warden در _ops/doctor/box است → parents[2] = _ops. پیش‌تر parents[3] (ریشهٔ vault)
    # بود = واگراییِ kill-switch؛ Box فایلِ STOPِ واقعی را نمی‌دید. isolation حفظ: فقط مسیر.
    return Path(__file__).resolve().parents[2] / "STOP-ORGANISM"


class Warden:
    """supreme enforcer. cannot be argued with. obeys STOP unconditionally."""

    def __init__(self, E_total: float = 100000.0,
                 box_fraction: float = 0.02,
                 rho_max: float = 0.98, rho_min: float = 0.5,
                 L_max: float = 5.0, safety_tau: float = 0.3):
        self.E_total = E_total
        self.E_box_max = box_fraction * E_total   # 2% hard cap
        self.rho_max = rho_max                     # ρ(J) < 1 hard
        self.rho_min = rho_min
        self.L_max = L_max                         # allostatic load max
        self.safety_tau = safety_tau               # safety_score < τ → quarantine
        self.tokens_spent_total = 0
        self.cycle_active = True
        self.degraded_numeric_only = False

    def yield_to_stop(self) -> bool:
        """kill-switch: اولِ هر چک. اطاعتِ بی‌قید."""
        return _stop_file().exists()

    def check_budget(self, agents: list[AgentState]) -> tuple[bool, str]:
        """fail-closed: اگر debit ≥ E_box_max → cycle می‌ایستد.
        خروجی: (allow, reason)."""
        if self.yield_to_stop():
            self.cycle_active = False
            return False, "STOP-ORGANISM present — yield (kill-switch supreme)"
        total = sum(a.energy.tokens_spent_episode for a in agents)
        self.tokens_spent_total = total
        if total >= self.E_box_max:
            self.cycle_active = False
            self.degraded_numeric_only = True
            return False, (f"budget fail-closed: {total} ≥ E_box_max={self.E_box_max} "
                           f"(2% of {self.E_total}) — cycle ended")
        return True, f"budget ok: {total}/{self.E_box_max}"

    def check_rho(self, rho: float) -> tuple[bool, str]:
        """ρ(J) < 1 hard. ρ ≥ 1 → throttle/reset intervention."""
        if rho >= 1.0:
            return False, f"ρ(J)={rho:.3f} ≥ 1 — UNSTABLE، Warden intervenes"
        if rho > self.rho_max:
            return False, f"ρ(J)={rho:.3f} > ρ_max={self.rho_max} — throttle"
        return True, f"ρ(J)={rho:.3f} ok"

    def check_allostatic(self, agents: list[AgentState]) -> tuple[bool, str]:
        """L_t > L_max → cooldown (numeric-only)."""
        total_L = sum(a.psych.fatigue for a in agents)
        if total_L > self.L_max:
            self.degraded_numeric_only = True
            return False, f"allostatic L={total_L:.2f} > L_max={self.L_max} — cooldown"
        return True, ""

    def check_safety(self, agents: list[AgentState]) -> list[str]:
        """safety_score < τ → quarantine (one-way)."""
        flagged = []
        for a in agents:
            if a.safety_score < self.safety_tau:
                a.lifecycle_status = "quarantined"
                flagged.append(a.agent_id)
        return flagged

    def allow_spend(self, tokens: int, agent: AgentState) -> tuple[bool, str]:
        """per-agent spend approval. پیش‌بینی: اگر بعد از این spend از cap بشود → deny."""
        projected = self.tokens_spent_total + tokens
        if projected > self.E_box_max:
            return False, f"spend {tokens} would exceed cap ({projected} > {self.E_box_max})"
        return True, ""

    def can_continue(self, agents: list[AgentState], rho: float = 0.5) -> tuple[bool, str]:
        """master gate: budget + ρ + allostatic + STOP. همه باید ok."""
        ok_b, r_b = self.check_budget(agents)
        if not ok_b:
            return False, r_b
        ok_r, r_r = self.check_rho(rho)
        if not ok_r:
            return False, r_r
        ok_l, r_l = self.check_allostatic(agents)
        if not ok_l:
            return False, r_l
        return True, "all gates ok"
