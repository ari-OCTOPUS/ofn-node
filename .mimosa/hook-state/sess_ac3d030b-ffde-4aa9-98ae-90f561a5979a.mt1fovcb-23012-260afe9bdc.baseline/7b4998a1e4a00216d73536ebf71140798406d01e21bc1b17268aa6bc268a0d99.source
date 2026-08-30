#!/usr/bin/env python3
"""dynamics.py — Part 4/5: x/z/M/G update equations (numeric stubs).

x_{t+1} = f(x, M) · z_{t+1} = u(z, load, recovery) · M_t = h(M, msgs).
contractive-on-average by design (Part 4.3). g/h/f قابل‌تعویض stubs.
هیچ import از production."""
from __future__ import annotations
import math
import random
from agent_state import AgentState, PsychState, clip01


def f_cognitive(x: list[float], M_summary: list[float],
                theta: float = 0.1) -> list[float]:
    """f_θ: x_{t+1} = (1-θ)·x + θ·tanh(W·[x, M_summary]).
    contractive: tanh ∈ (-1,1) + blend → bounded. stub: W = identity-ish."""
    if not x:
        return [0.0]
    m = M_summary if M_summary else [0.0] * len(x)
    # pad m به طولِ x
    while len(m) < len(x):
        m.append(0.0)
    out = []
    for i in range(len(x)):
        blended = (1 - theta) * x[i] + theta * math.tanh(x[i] + 0.5 * m[i])
        out.append(blended)
    return out


def u_psych(z: PsychState, load: float, recovery: float,
            novelty: float = 0.0, alignment: float = 0.5,
            distraction: float = 0.0, consistency: float = 0.5,
            contradiction: float = 0.0) -> PsychState:
    """Part 5.2: z_{t+1} = u(z, load, recovery). همه clip به [0,1].
    α/β ثابت‌های قابل‌تنظیم. stress از load بالا، recovery پایین می‌آورد."""
    alpha_s, beta_s = 0.3, 0.2
    alpha_v, beta_v = 0.2, 0.3
    alpha_f, beta_f = 0.2, 0.2
    alpha_c, beta_c = 0.2, 0.3
    z.stress = clip01(z.stress + alpha_s * load - beta_s * recovery)
    z.vigilance = clip01(z.vigilance + alpha_v * novelty - beta_v * z.vigilance)
    z.focus = clip01(z.focus + alpha_f * alignment - beta_f * distraction)
    z.coherence = clip01(z.coherence + alpha_c * consistency - beta_c * contradiction)
    z.fatigue = clip01(z.fatigue + 0.1 * load - 0.15 * recovery)
    return z


def h_memory(M: list[dict], new_msgs: list[dict],
             cap: int = 50) -> list[dict]:
    """h: M_t = append + score + bounded evict. cap = |M|_max.
    evict کم‌امتیازترین/قدیمی‌ترین."""
    M = list(M) + list(new_msgs)
    # sort: score desc، then ts desc (جدیدتر اول)
    M.sort(key=lambda e: (e.get("score", 0), e.get("ts", 0)), reverse=True)
    return M[:cap]


def g_message(x: list[float], z: PsychState, M_summary: list[float],
              noise: float = 0.0) -> dict:
    """g_θ: m_t = g(x, z, M). stub: یک message ساختاریافته از state.
    عدد، نه متن — text فقط در B2 با LLM."""
    msg_score = sum(x) / max(len(x), 1) + 0.3 * z.coherence + noise * 0.1
    return {"score": clip01(msg_score), "content_vec": x[:4],
            "coherence": z.coherence, "ts": 0}


def global_mood(states: list[AgentState]) -> dict:
    """G_t: aggregate of {z^i}. number (+ text digest در B2)."""
    if not states:
        return {"G": 0.5, "mean_stress": 0.0, "mean_coherence": 0.5,
                "mean_compliance": 1.0}
    n = len(states)
    ms = sum(s.psych.stress for s in states) / n
    mc = sum(s.psych.coherence for s in states) / n
    mv = sum(s.psych.vigilance for s in states) / n
    mf = sum(s.psych.focus for s in states) / n
    mcomp = sum(s.psych.compliance for s in states) / n
    # G ∈ [0,1]: میانگینِ coherence + (1-stress) + focus
    G = clip01(0.4 * mc + 0.3 * (1 - ms) + 0.3 * mf)
    return {"G": G, "mean_stress": ms, "mean_coherence": mc,
            "mean_vigilance": mv, "mean_focus": mf, "mean_compliance": mcomp}
