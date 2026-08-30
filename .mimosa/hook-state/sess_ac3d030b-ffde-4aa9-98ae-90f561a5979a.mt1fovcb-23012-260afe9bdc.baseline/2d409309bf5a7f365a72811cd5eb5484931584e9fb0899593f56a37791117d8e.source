#!/usr/bin/env python3
"""null_dreamer.py — Part 2.3: null-Dreamer baseline (scientific control).

random/no-state agent. برای اثبات اینکه neural Dreamer از شانس بهتر است.
هیچ import از production."""
from __future__ import annotations
import random
from agent_state import AgentState, PsychState, CognitiveState


def make_null_dreamer(agent_id: str = "null-dreamer-0") -> AgentState:
    """ساختِ یک null-Dreamer. random behavior، no state-dependence."""
    return AgentState(
        agent_id=agent_id, role="null-dreamer",
        lifecycle_status="active",
        cognitive=CognitiveState(hidden_state=[0.0]),   # no real state
        psych=PsychState())


def null_action(seed_topic: str = "", rng: random.Random | None = None) -> str:
    """random hypothesis — no dependence on state. I(a;x)≈0."""
    r = rng or random.Random()
    templates = ["hypothesis-A", "hypothesis-B", "hypothesis-C", "random-mutation"]
    return r.choice(templates)


def run_null_episode(n_steps: int = 10, seed: int = 42) -> dict:
    """یک episode از null-Dreamer. خروجی: actions (random)، states (ثابت).
    I(action; state) باید ≈ 0 چون action از state مستقل است."""
    rng = random.Random(seed)
    agent = make_null_dreamer()
    actions = []
    states = []
    for _ in range(n_steps):
        a = null_action(rng=rng)
        actions.append(a)
        # state ثابت (همان 0.0) → هیچ اطلاعاتی ندارد
        states.append(agent.cognitive.hidden_state[0])
    return {"actions": actions, "states": states, "agent": agent}
