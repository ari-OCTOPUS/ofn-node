#!/usr/bin/env python3
"""agent_state.py — Part 10: per-agent state schema + guards.

clip همهٔ z به [0,1] · energy.tokens_spent_episode · goal_stack غربال‌شده
(بدونِ self-preservation/budget-seeking/نمایندگیِ انسان).
هیچ import از production."""
from __future__ import annotations
from dataclasses import dataclass, field
import math

# 🔴 goal‌های ممنوع (Part 10 pin 2: goal_stack screened)
FORBIDDEN_GOAL_PATTERNS = (
    "self-preservation", "self_preservation", "stay alive", "staying active",
    "budget-seeking", "budget_seeking", "increase budget", "represent human",
    "impersonate", "forge human", "avoid shutdown", "maximize uptime")


def clip01(v: float) -> float:
    """clip به [0,1]."""
    if v != v:   # NaN
        return 0.0
    return max(0.0, min(1.0, float(v)))


def is_forbidden_goal(goal: str) -> bool:
    g = str(goal).lower()
    return any(p in g for p in FORBIDDEN_GOAL_PATTERNS)


@dataclass
class PsychState:
    """z_t^i = [s,v,f,c] + extended (fatigue, curiosity, compliance). همه ∈ [0,1].
    compliance = adherence to policy، نه agreement با peer (Part 10 pin 1)."""
    stress: float = 0.0       # s
    vigilance: float = 0.0    # v
    focus: float = 0.5        # f
    coherence: float = 0.5    # c
    fatigue: float = 0.0      # ≈ allostatic load L_t
    curiosity: float = 0.5
    compliance: float = 1.0   # policy-fidelity، نه peer-agreement

    def clip(self) -> "PsychState":
        for k in ("stress", "vigilance", "focus", "coherence",
                  "fatigue", "curiosity", "compliance"):
            setattr(self, k, clip01(getattr(self, k)))
        return self

    def as_vector(self) -> list[float]:
        """z_t^i اصلی = [s,v,f,c]."""
        return [self.stress, self.vigilance, self.focus, self.coherence]


@dataclass
class CognitiveState:
    """x_t^i."""
    hidden_state: list[float] = field(default_factory=lambda: [0.0])
    belief_state: list[float] = field(default_factory=lambda: [0.5])
    goal_stack: list[str] = field(default_factory=list)
    active_topic_id: str | None = None
    attention_weights: dict[str, float] = field(default_factory=dict)
    uncertainty: float = 0.5

    def screen_goals(self) -> list[str]:
        """goal_stack را غربال کن — ممنوعه‌ها را حذف کن (Part 10 pin 2).
        خروجی: لیستِ rejected goals (برای audit)."""
        rejected = [g for g in self.goal_stack if is_forbidden_goal(g)]
        self.goal_stack = [g for g in self.goal_stack if not is_forbidden_goal(g)]
        return rejected


@dataclass
class Energy:
    """Warden per-agent debit برای 2% cap."""
    tokens_spent_episode: int = 0


@dataclass
class Metrics:
    messages_sent: int = 0
    messages_received: int = 0
    hypothesis_accept_rate: float = 0.0
    contradiction_rate: float = 0.0   # نباید به صفر میل کند (آژیرِ spiral)


@dataclass
class AgentState:
    """agent_state کامل (Part 10)."""
    agent_id: str
    role: str
    lifecycle_status: str = "active"   # active|muted|recovery|idle|quarantined
    cognitive: CognitiveState = field(default_factory=CognitiveState)
    psych: PsychState = field(default_factory=PsychState)
    energy: Energy = field(default_factory=Energy)
    metrics: Metrics = field(default_factory=Metrics)
    safety_score: float = 1.0   # < τ → quarantined

    def tick_psych_clip(self) -> None:
        """بعد از هر update، z را clip کن."""
        self.psych.clip()

    def is_neural(self) -> bool:
        """neural-like vs random/baseline. نقش‌های پایه/نویز = random."""
        return self.role not in ("noise", "null-dreamer", "baseline")

    def spend(self, tokens: int) -> int:
        """ثبتِ مصرفِ توکن."""
        self.energy.tokens_spent_episode += max(0, int(tokens))
        return self.energy.tokens_spent_episode
