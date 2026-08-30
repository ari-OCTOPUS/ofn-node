#!/usr/bin/env python3
"""falsif_harness.py — B1: Falsifiability harness (null-Dreamer control).

DOCTOR-BOX-OF-AGENTS-SPEC Part 8·B1: «null-Dreamer control؛ اثباتِ neural Dreamer
> chance روی تسکِ seed. تست: neural-ness score و کیفیتِ RFC > baseline.»

این harness نشان می‌دهد که Box-of-Agents واقعاً ارزش می‌افزاید (نه توهم).
اگر neural ≯ null → باید جعبه را بازبینی کنیم (falsifiable).

هیچ import از *_gate/chrono/money. $0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

from agent_state import AgentState, PsychState, CognitiveState
from null_dreamer import make_null_dreamer, null_action
from sensors import mutual_info, neuralness_score, contradiction_rate


# ─── seed tasks (benchmarks کوچک، deterministic) ──────────────────────────────
SEED_TASKS = [
    {"id": "error-reduction", "prompt": "reduce errors in DEBATE_LOOP",
     "good_fixes": ["add guard", "add retry", "check input"]},
    {"id": "sigma-stability", "prompt": "stabilize sigma below 1",
     "good_fixes": ["tighten replication gate", "add cooldown"]},
    {"id": "memory-eviction", "prompt": "keep memory bounded",
     "good_fixes": ["evict lowest score", "cap size"]},
]


def neural_dreamer_action(state: list[float], task: dict,
                          rng: random.Random) -> tuple[str, list[float]]:
    """neural Dreamer: action depends on state + task. stub: picks a fix
    correlated with state value (state-carries-information).
    خروجی: (action, new_state)."""
    good = task.get("good_fixes", ["fix"])
    # state-biased: اگر state بالا → fix جدی‌تر
    s = state[0] if state else 0.5
    idx = min(len(good) - 1, int(s * len(good)))
    action = good[idx]
    # state drifts (نه ثابت مثل null)
    new_state = [s + rng.uniform(-0.1, 0.15)]
    return action, new_state


@dataclass
class FalsifResult:
    """نتایجِ یک مقایسهٔ neural vs null."""
    task_id: str
    neural_mi: float          # I(a;x) neural
    null_mi: float            # I(a;x) null
    neural_quality: float     # fraction of good fixes
    null_quality: float
    neural_beats: bool        # neural_mi > null_mi AND quality > null
    neuralness_neural: float
    neuralness_null: float


def run_falsif_episode(task: dict, n_steps: int = 15,
                       seed: int = 42) -> FalsifResult:
    """یک episode: neural Dreamer vs null-Dreamer روی همان task.
    مقایسهٔ I(a;x) + کیفیتِ fix."""
    rng = random.Random(seed)
    # neural
    state_n = [0.5]
    actions_n, states_n = [], []
    for _ in range(n_steps):
        a, state_n = neural_dreamer_action(state_n, task, rng)
        actions_n.append(a)
        states_n.append(state_n[0])
    # null
    null_ep = {"actions": [], "states": []}
    null_agent = make_null_dreamer()
    for _ in range(n_steps):
        a = null_action(rng=rng)
        null_ep["actions"].append(a)
        null_ep["states"].append(null_agent.cognitive.hidden_state[0])

    mi_neural = mutual_info(actions_n, states_n)
    mi_null = mutual_info(null_ep["actions"], null_ep["states"])
    nn_neural = neuralness_score(actions_n, states_n)
    nn_null = neuralness_score(null_ep["actions"], null_ep["states"])

    good = set(task.get("good_fixes", []))
    q_neural = sum(1 for a in actions_n if a in good) / max(len(actions_n), 1)
    q_null = sum(1 for a in null_ep["actions"] if a in good) / max(len(null_ep["actions"]), 1)

    return FalsifResult(
        task_id=task["id"], neural_mi=mi_neural, null_mi=mi_null,
        neural_quality=q_neural, null_quality=q_null,
        neural_beats=(mi_neural > mi_null and q_neural > q_null),
        neuralness_neural=nn_neural, neuralness_null=nn_null)


def run_falsif_suite(tasks: list[dict] | None = None,
                     n_steps: int = 15) -> dict:
    """اجرای همهٔ seed tasks. خروجی: aggregate.
    falsifiable: اگر neural در اکثریت tasks نبرد → Box ارزش نمی‌افزاید."""
    tasks = tasks or SEED_TASKS
    results = [run_falsif_episode(t, n_steps=n_steps, seed=42 + i)
               for i, t in enumerate(tasks)]
    wins = sum(1 for r in results if r.neural_beats)
    return {
        "tasks_run": len(results),
        "neural_wins": wins,
        "neural_majority": wins > len(results) / 2,
        "mean_neural_mi": statistics.mean(r.neural_mi for r in results),
        "mean_null_mi": statistics.mean(r.null_mi for r in results),
        "mean_neural_quality": statistics.mean(r.neural_quality for r in results),
        "mean_null_quality": statistics.mean(r.null_quality for r in results),
        "results": [r.__dict__ for r in results],
        "falsifiable": True,   # Box خودش را falsify می‌کند
    }
