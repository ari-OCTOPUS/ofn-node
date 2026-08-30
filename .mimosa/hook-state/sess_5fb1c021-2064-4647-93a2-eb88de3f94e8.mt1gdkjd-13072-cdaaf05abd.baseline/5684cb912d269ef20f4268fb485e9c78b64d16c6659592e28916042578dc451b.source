#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""semantic_ablation.py — shadow ablation harness for semantic memory (WP-C).

هدف: پاسخِ علمی به این پرسش که آیا تزریقِ gist از semantic_memory کیفیت
خروجیِ cortex.think() را بهتر می‌کند یا فقط آن را متفاوت می‌کند.

طراحی:
  control   = همان task/context بدون semantic gist
  treatment = همان task/context با semantic gist

قیود:
  - هیچ paid call مگر با fixture/replay موجود؛ این harness از deterministic stub
    استفاده می‌کند (هیچ مدل واقعی، هیچ شبکه).
  - taskها و seeds ثابت و preregistered.
  - تفاوتِ خروجی به‌تنهایی success نیست — quality/error/cost metric مستقل.
  - primary estimand: paired quality difference.

Primary estimand:
  delta_quality = quality(treatment) − quality(control) per task

Possible honest outcomes:
  - context changes output but no quality lift (gist makes it different, not better)
  - positive lift (gist helps)
  - negative lift (gist hurts — stale/wrong context)
  - no change (gist ignored by model)

هر نتیجه صادقانه ثبت می‌شود.

پشتِ OCTOPUS_WIRE_SEMANTIC_ABLATION (default OFF). $0، deterministic.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS_PATH = HERE.parent / "state" / "cortex" / "semantic-ablation-results.jsonl"
SCHEMA = "SemanticAblationResult.v1"


# ─── deterministic fake model stub ────────────────────────────────────────────
# This stub simulates what a model would do: given a prompt (control vs treatment),
# produce an output and a quality score. It is FULLY DETERMINISTIC — same input
# always produces same output. No network, no API, no randomness.

def _fake_model(prompt: str, task: str) -> tuple[str, float]:
    """Deterministic fake model.

    Returns (output_text, quality_score 0..1).

    The stub has a SIMPLE embedded "ground truth": for tasks about "memory",
    adding a relevant keyword to the prompt slightly improves the deterministic
    score; for other tasks, it's noise. This lets us test that the harness
    correctly measures paired differences — the actual research question requires
    a REAL model (not this stub).
    """
    h = hashlib.sha256(f"{prompt}|{task}".encode()).hexdigest()
    base = (int(h[:8], 16) % 40) / 100.0  # 0.00-0.39 baseline

    # Simple "ground truth" for testing the harness itself:
    if "memory" in task.lower() and "gist" in prompt.lower():
        base += 0.05  # treatment helps for memory tasks

    return f"[stub output for {task[:20]}]", min(base, 1.0)


# ─── tasks (preregistered, frozen) ───────────────────────────────────────────

TASKS = [
    {"task_id": "T01", "task": "What is the most important work right now?",
     "category": "priority"},
    {"task_id": "T02", "task": "Summarize the system status",
     "category": "summary"},
    {"task_id": "T03", "task": "How is memory consolidation performing?",
     "category": "memory"},
    {"task_id": "T04", "task": "What needs the owner's attention?",
     "category": "priority"},
    {"task_id": "T05", "task": "Is there a stale component?",
     "category": "summary"},
    {"task_id": "T06", "task": "Check semantic memory health",
     "category": "memory"},
    {"task_id": "T07", "task": "What is the coherence level?",
     "category": "summary"},
    {"task_id": "T08", "task": "Should memory be consolidated?",
     "category": "memory"},
]


def _make_control_prompt(task: str) -> str:
    """Control prompt: no semantic gist."""
    return f"وضعیت مجموعه: coherence=0.97. یک جمله: {task}"


def _make_treatment_prompt(task: str, gist: str) -> str:
    """Treatment prompt: same as control + semantic gist."""
    return f"وضعیت مجموعه: coherence=0.97. آخرینِ بازتاب: {gist[:120]}. یک جمله: {task}"


# ─── fixed gists per task (preregistered) ────────────────────────────────────
# In a real run, these come from semantic_memory.jsonl. For the ablation harness
# test, they are frozen fixtures so results are reproducible.

GISTS = {
    "T01": "اولویت امروز پایداری سهمیه است",
    "T02": "consolidation دو رکورد اضافه کرد",
    "T03": "حافظه معنایی سالم است و رشد کرده",
    "T04": "هیچ مداخله بحرانی باز نیست",
    "T05": "هیچ عضوی stale نیست",
    "T06": "semantic_memory 521 رکورد دارد",
    "T07": "coherence 0.97 است",
    "T08": "consolidation هر 720 beat اجرا می‌شود",
}


def run_ablation(tasks: list[dict] | None = None,
                 gists: dict[str, str] | None = None,
                 model_fn=None) -> dict:
    """Run a paired ablation: for each task, run control and treatment.

    Returns a dict with per-task results and aggregate statistics.

    Args:
        tasks: list of {task_id, task, category}. Defaults to frozen TASKS.
        gists: {task_id: gist_text}. Defaults to frozen GISTS.
        model_fn: callable(prompt, task) -> (output, quality). Defaults to stub.
    """
    if tasks is None:
        tasks = TASKS
    if gists is None:
        gists = GISTS
    if model_fn is None:
        model_fn = _fake_model

    results = []
    for t in tasks:
        tid = t["task_id"]
        task = t["task"]

        control_prompt = _make_control_prompt(task)
        control_out, control_q = model_fn(control_prompt, task)

        gist = gists.get(tid, "")
        treatment_prompt = _make_treatment_prompt(task, gist) if gist else control_prompt
        treatment_out, treatment_q = model_fn(treatment_prompt, task)

        delta = treatment_q - control_q
        output_changed = control_out != treatment_out

        results.append({
            "task_id": tid,
            "category": t.get("category", "?"),
            "control_quality": round(control_q, 4),
            "treatment_quality": round(treatment_q, 4),
            "delta": round(delta, 4),
            "output_changed": output_changed,
            "gist_present": bool(gist),
        })

    # Aggregate
    deltas = [r["delta"] for r in results]
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    n_positive = sum(1 for d in deltas if d > 0)
    n_negative = sum(1 for d in deltas if d < 0)
    n_zero = sum(1 for d in deltas if d == 0)
    n_changed = sum(1 for r in results if r["output_changed"])

    # Simple bootstrap CI (1000 resamples) for the mean delta
    import random
    rng = random.Random(997000)  # fixed seed
    boot_means = []
    for _ in range(1000):
        sample = rng.choices(deltas, k=len(deltas))
        boot_means.append(sum(sample) / len(sample))
    boot_means.sort()
    ci_lo = boot_means[50]   # 5th percentile
    ci_hi = boot_means[950]  # 95th percentile

    summary = {
        "schema": SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_tasks": len(results),
        "mean_delta": round(mean_delta, 4),
        "ci_95": [round(ci_lo, 4), round(ci_hi, 4)],
        "n_positive": n_positive,
        "n_negative": n_negative,
        "n_zero": n_zero,
        "n_output_changed": n_changed,
        "per_task": results,
        "note": ("Harness test with deterministic stub. Real efficacy measurement "
                 "requires a REAL model, not this stub. The stub's embedded ground "
                 "truth only tests that the HARNESS works, not that gist helps."),
    }

    # Persist (if enabled)
    if os.environ.get("OCTOPUS_WIRE_SEMANTIC_ABLATION", "0") == "1":
        try:
            RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(RESULTS_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(summary, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError:
            pass

    return summary


if __name__ == "__main__":
    result = run_ablation()
    print(json.dumps(result, ensure_ascii=False, indent=2))
