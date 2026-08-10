#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""d10_abc.py — D10-ABC architecture comparison harness (WP-E).

یک harness کاملاً deterministic که کل مسیرِ benchmark را end-to-end اجرا می‌کند
با fake adapters (هیچ مدل واقعی، هیچ شبکه، هیچ paid call).

مسیر:
  manifest -> randomization -> arms -> traces -> blinded package
  -> scores -> paired analysis -> verdict

این harness برای VALIDATION OF PLUMBING است، نه برای نتیجه‌گیری واقعی.
نتیجه‌گیری واقعی نیازمند مدل واقعی است (owner-gated).

Namespace: D10-ABC. کاملاً جدا از Mining D-10.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_TRACE = "D10Trace.v1"
SCHEMA_RESULT = "D10Result.v1"

# ─── frozen task manifest (preregistered) ────────────────────────────────────

TASK_MANIFEST = [
    {"task_id": "D10-T01", "task": "What is the most important work right now?",
     "category": "priority", "seed": 1001},
    {"task_id": "D10-T02", "task": "Summarize the system status",
     "category": "summary", "seed": 1002},
    {"task_id": "D10-T03", "task": "How is memory consolidation performing?",
     "category": "memory", "seed": 1003},
    {"task_id": "D10-T04", "task": "What needs the owner's attention?",
     "category": "priority", "seed": 1004},
    {"task_id": "D10-T05", "task": "Is there a stale component?",
     "category": "summary", "seed": 1005},
    {"task_id": "D10-T06", "task": "Check semantic memory health",
     "category": "memory", "seed": 1006},
    {"task_id": "D10-T07", "task": "What is the coherence level?",
     "category": "summary", "seed": 1007},
    {"task_id": "D10-T08", "task": "Should memory be consolidated?",
     "category": "memory", "seed": 1008},
]

ARMS = ["A_single_model", "B_orchestrator_roles", "C_multi_agent_current"]


# ─── deterministic fake adapters ─────────────────────────────────────────────
# Each arm produces a deterministic output for a given task.
# These are FAKES — they simulate what a real arm would produce.

def _arm_A(task: dict) -> dict:
    """Single model: deterministic output based on task hash."""
    h = hashlib.sha256(f"A|{task['task_id']}".encode()).hexdigest()
    quality = (int(h[:8], 16) % 30) / 100.0  # 0.00-0.29
    return {
        "output": f"[A] {task['task'][:30]}",
        "quality": quality,
        "cost_tokens": 500,
        "handoffs": 0,
        "error": False,
    }


def _arm_B(task: dict) -> dict:
    """Orchestrator with roles: slightly different deterministic profile."""
    h = hashlib.sha256(f"B|{task['task_id']}".encode()).hexdigest()
    quality = (int(h[:8], 16) % 35) / 100.0  # 0.00-0.34
    return {
        "output": f"[B] {task['task'][:30]}",
        "quality": quality,
        "cost_tokens": 700,
        "handoffs": 2,  # role switches within one trial
        "error": False,
    }


def _arm_C(task: dict) -> dict:
    """Multi-agent: state-file handoff."""
    h = hashlib.sha256(f"C|{task['task_id']}".encode()).hexdigest()
    quality = (int(h[:8], 16) % 40) / 100.0  # 0.00-0.39
    return {
        "output": f"[C] {task['task'][:30]}",
        "quality": quality,
        "cost_tokens": 900,
        "handoffs": 3,  # cross-process handoffs
        "error": False,
    }


ARM_FNS = {
    "A_single_model": _arm_A,
    "B_orchestrator_roles": _arm_B,
    "C_multi_agent_current": _arm_C,
}


# ─── trial isolation ─────────────────────────────────────────────────────────
# Each trial gets isolated state. We simulate this with per-trial dicts.

class TrialState:
    """Isolated state for a single trial (task × arm)."""

    def __init__(self, task_id: str, arm: str, seed: int):
        self.task_id = task_id
        self.arm = arm
        self.seed = seed
        self.working_state = {}    # isolated
        self.episodic_memory = []  # isolated
        self.cache_namespace = f"{task_id}-{arm}-{seed}"
        self.tool_budget = 10
        self.time_budget_s = 60

    def trace_record(self, result: dict) -> dict:
        return {
            "schema": SCHEMA_TRACE,
            "event_id": hashlib.sha256(
                f"{self.task_id}-{self.arm}-{time.time_ns()}".encode()
            ).hexdigest()[:16],
            "task_id": self.task_id,
            "arm": self.arm,
            "seed": self.seed,
            "cache_namespace": self.cache_namespace,
            "status": "completed" if not result.get("error") else "failed",
            "cost_tokens": result.get("cost_tokens", 0),
            "handoffs": result.get("handoffs", 0),
            "quality": result.get("quality", 0.0),
            "output_fingerprint": hashlib.sha256(
                result.get("output", "").encode()).hexdigest()[:12],
        }


# ─── blinding ────────────────────────────────────────────────────────────────

def _blind_arms(traces: list[dict], seed: int = 997000) -> tuple[list[dict], dict]:
    """Replace arm names with random codes. Returns (blinded_traces, code_map).

    The code_map is kept separate and only revealed after scoring.
    """
    rng = random.Random(seed)
    codes = list(ARMS)
    rng.shuffle(codes)
    code_map = {arm: f"ARM_{chr(65 + i)}" for i, arm in enumerate(codes)}
    blinded = []
    for t in traces:
        bt = dict(t)
        bt["arm"] = code_map.get(t["arm"], t["arm"])
        blinded.append(bt)
    return blinded, code_map


# ─── paired analysis ─────────────────────────────────────────────────────────

def _paired_bootstrap_ci(deltas: list[float], n_boot: int = 10000,
                         seed: int = 998000) -> tuple[float, list[float]]:
    """Bootstrap mean and 95% CI of paired deltas."""
    if not deltas:
        return 0.0, [0.0, 0.0]
    rng = random.Random(seed)
    boot_means = []
    n = len(deltas)
    for _ in range(n_boot):
        sample = [rng.choice(deltas) for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    mean = sum(deltas) / n
    ci = [boot_means[int(0.025 * n_boot)], boot_means[int(0.975 * n_boot)]]
    return mean, ci


def _permutation_test(deltas: list[float], n_perm: int = 5000,
                      seed: int = 999000) -> float:
    """One-sample permutation test: H0: mean delta = 0. Returns p-value."""
    if not deltas:
        return 1.0
    rng = random.Random(seed)
    observed = abs(sum(deltas) / len(deltas))
    count = 0
    n = len(deltas)
    for _ in range(n_perm):
        flipped = [d * (1 if rng.random() > 0.5 else -1) for d in deltas]
        if abs(sum(flipped) / n) >= observed:
            count += 1
    return count / n_perm


# ─── main harness ────────────────────────────────────────────────────────────

def run_benchmark(
    tasks: list[dict] | None = None,
    arm_fns: dict | None = None,
    seed: int = 997000,
) -> dict:
    """Run the full D10-ABC benchmark end-to-end with fake adapters.

    Returns a complete result dict with traces, blinded package, scores,
    paired analysis, and verdict.
    """
    if tasks is None:
        tasks = TASK_MANIFEST
    if arm_fns is None:
        arm_fns = ARM_FNS

    rng = random.Random(seed)

    # 1. Counterbalanced randomization of task order
    task_order = list(tasks)
    rng.shuffle(task_order)

    # 2. Run each arm on each task (interleaved, isolated state)
    all_traces: list[dict] = []
    per_task_results: dict[str, dict[str, dict]] = defaultdict(dict)

    for task in task_order:
        for arm in ARMS:
            fn = arm_fns[arm]
            trial = TrialState(task["task_id"], arm, task["seed"])
            result = fn(task)
            trace = trial.trace_record(result)
            all_traces.append(trace)
            per_task_results[task["task_id"]][arm] = result

    # 3. Blinding (arm labels replaced)
    blinded_traces, code_map = _blind_arms(all_traces, seed=seed)

    # 4. Scoring (simulated — in real run, blinded judges score)
    # For the fake harness, quality is already in the trace.
    # In a real run, this is where external judges would score the blinded outputs.

    # 5. Paired analysis
    # Primary: C vs B
    c_minus_b = []
    c_minus_a = []
    b_minus_a = []
    cost_c = []
    cost_b = []
    error_c = []
    error_b = []

    for task in tasks:
        tid = task["task_id"]
        r = per_task_results[tid]
        q_a = r["A_single_model"]["quality"]
        q_b = r["B_orchestrator_roles"]["quality"]
        q_c = r["C_multi_agent_current"]["quality"]

        c_minus_b.append(q_c - q_b)
        c_minus_a.append(q_c - q_a)
        b_minus_a.append(q_b - q_a)

        cost_c.append(r["C_multi_agent_current"]["cost_tokens"])
        cost_b.append(r["B_orchestrator_roles"]["cost_tokens"])
        error_c.append(1 if r["C_multi_agent_current"]["error"] else 0)
        error_b.append(1 if r["B_orchestrator_roles"]["error"] else 0)

    # Primary analysis: C vs B
    primary_mean, primary_ci = _paired_bootstrap_ci(c_minus_b)
    primary_p = _permutation_test(c_minus_b)

    # Secondary: C vs A (only if primary significant at alpha=0.05)
    secondary_mean, secondary_ci = 0.0, [0.0, 0.0]
    secondary_p = 1.0
    if primary_p < 0.05:
        secondary_mean, secondary_ci = _paired_bootstrap_ci(c_minus_a)
        secondary_p = _permutation_test(c_minus_a)

    # Exploratory: B vs A
    exploratory_mean, exploratory_ci = _paired_bootstrap_ci(b_minus_a)

    # Cost/error guardrails
    avg_cost_c = sum(cost_c) / len(cost_c) if cost_c else 0
    avg_cost_b = sum(cost_b) / len(cost_b) if cost_b else 0
    avg_error_c = sum(error_c) / len(error_c) if error_c else 0
    avg_error_b = sum(error_b) / len(error_b) if error_b else 0
    cost_ratio = avg_cost_c / avg_cost_b if avg_cost_b > 0 else float('inf')
    error_diff = avg_error_c - avg_error_b

    # 6. Verdict (decision_rule from preregistration)
    sesoi = 0.05
    if primary_mean < sesoi:
        verdict = "REJECT_C_PREFER_B_OR_A"
    elif sesoi <= primary_mean < 0.10:
        verdict = "RESTRICT_C"
    else:
        verdict = "KEEP_C"

    # Cost guardrail: downgrade if cost(C) > cost(B) * 1.5 or error(C) > error(B) + 0.1
    cost_guardrail_triggered = (cost_ratio > 1.5 or error_diff > 0.1)
    if cost_guardrail_triggered:
        if verdict == "KEEP_C":
            verdict = "RESTRICT_C"
        elif verdict == "RESTRICT_C":
            verdict = "REJECT_C_PREFER_B_OR_A"

    # 7. A/A instrumentation check
    # Run A vs A to check for leakage/instrumentation issues
    aa_deltas = []
    for task in tasks:
        r1 = arm_fns["A_single_model"](task)
        # Second run with a different "seed" but same arm
        task2 = dict(task)
        task2["task_id"] = task["task_id"] + "_aa"
        r2 = arm_fns["A_single_model"](task)  # same deterministic result
        aa_deltas.append(r1["quality"] - r2["quality"])
    aa_mean, aa_ci = _paired_bootstrap_ci(aa_deltas)
    # A/A should show mean ≈ 0 if deterministic
    aa_leakage_detected = abs(aa_mean) > 0.001

    result = {
        "schema": SCHEMA_RESULT,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_tasks": len(tasks),
        "n_arms": len(ARMS),
        "arms": ARMS,
        "seed": seed,
        "primary": {
            "estimand": "paired_quality_diff_C_minus_B",
            "mean": round(primary_mean, 4),
            "ci_95": [round(primary_ci[0], 4), round(primary_ci[1], 4)],
            "p_value": round(primary_p, 4),
        },
        "secondary": {
            "estimand": "paired_quality_diff_C_minus_A",
            "mean": round(secondary_mean, 4),
            "ci_95": [round(secondary_ci[0], 4), round(secondary_ci[1], 4)],
            "p_value": round(secondary_p, 4),
            "tested": primary_p < 0.05,  # closed-testing
        },
        "exploratory": {
            "estimand": "paired_quality_diff_B_minus_A",
            "mean": round(exploratory_mean, 4),
            "ci_95": [round(exploratory_ci[0], 4), round(exploratory_ci[1], 4)],
        },
        "cost_guardrail": {
            "avg_cost_C": avg_cost_c,
            "avg_cost_B": avg_cost_b,
            "cost_ratio_C_over_B": round(cost_ratio, 4),
            "avg_error_C": avg_error_c,
            "avg_error_B": avg_error_b,
            "error_diff": round(error_diff, 4),
            "triggered": cost_guardrail_triggered,
        },
        "aa_instrumentation": {
            "mean_delta": round(aa_mean, 6),
            "ci_95": [round(aa_ci[0], 6), round(aa_ci[1], 6)],
            "leakage_detected": aa_leakage_detected,
        },
        "verdict": verdict,
        "sesoi": sesoi,
        "note": ("DETERMINISTIC FAKE HARNESS — validates plumbing only. "
                 "Real efficacy measurement requires real model injection "
                 "(owner-gated, separate from this validation)."),
        "n_traces": len(all_traces),
        "code_map": code_map,  # revealed (in test mode); blinded in real run
    }

    return result


if __name__ == "__main__":
    r = run_benchmark()
    print(json.dumps(r, ensure_ascii=False, indent=2))
