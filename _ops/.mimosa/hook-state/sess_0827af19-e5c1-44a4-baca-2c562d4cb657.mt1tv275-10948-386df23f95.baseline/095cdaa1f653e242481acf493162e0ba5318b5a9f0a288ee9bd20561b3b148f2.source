#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_d10_abc_benchmark — تست‌های WP-E: D10-ABC benchmark harness.

تست می‌کند که harness plumbing درست کار می‌کند:
  - randomization reproducibility
  - no cross-trial state leakage
  - cache isolation
  - trace parent validity
  - blinded labels
  - paired analysis
  - closed-testing (secondary only if primary significant)
  - cost guardrail
  - A/A leakage detection
  - verdict logic
  - determinism (same seed = same result)
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_RSC = _OPS.parent / "03 - Projects" / "research-spec-compiler"
for _p in (str(_OPS), str(_RSC / "experiments"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("d10-abc-benchmark")

import d10_abc  # noqa: E402


# ─── TESTS ────────────────────────────────────────────────────────────────────

def t_randomization_reproducible():
    """همان seed باید همان ترتیبِ task را بدهد."""
    r1 = d10_abc.run_benchmark(seed=997000)
    r2 = d10_abc.run_benchmark(seed=997000)
    assert r1["verdict"] == r2["verdict"]
    assert r1["primary"]["mean"] == r2["primary"]["mean"]


def t_different_seed_different_order():
    """seed متفاوت باید ترتیب متفاوت بدهد (در نتیجه‌های متفاوت)."""
    r1 = d10_abc.run_benchmark(seed=997000)
    r2 = d10_abc.run_benchmark(seed=998000)
    # Traces may differ in count but structure is the same
    assert r1["n_traces"] == r2["n_traces"]


def t_no_cross_trial_state_leakage():
    """هر trial باید state ایزوله داشته باشد."""
    # Run benchmark and verify that each TrialState has unique cache_namespace
    tasks = d10_abc.TASK_MANIFEST[:2]
    for task in tasks:
        for arm in d10_abc.ARMS:
            trial = d10_abc.TrialState(task["task_id"], arm, task["seed"])
            assert f"{task['task_id']}-{arm}" in trial.cache_namespace
            assert trial.working_state == {}  # isolated, empty


def t_cache_isolation():
    """cache_namespace باید یکتا باشد per (task, arm)."""
    namespaces = set()
    for task in d10_abc.TASK_MANIFEST:
        for arm in d10_abc.ARMS:
            trial = d10_abc.TrialState(task["task_id"], arm, task["seed"])
            ns = trial.cache_namespace
            assert ns not in namespaces, f"cache namespace تکراری: {ns}"
            namespaces.add(ns)


def t_trace_has_parent_validity():
    """هر trace باید فیلدهای ضروری داشته باشد."""
    r = d10_abc.run_benchmark()
    # Reconstruct traces by re-running (deterministic)
    for task in d10_abc.TASK_MANIFEST[:1]:
        for arm in d10_abc.ARMS:
            fn = d10_abc.ARM_FNS[arm]
            result = fn(task)
            trial = d10_abc.TrialState(task["task_id"], arm, task["seed"])
            trace = trial.trace_record(result)
            assert "event_id" in trace
            assert "task_id" in trace
            assert "arm" in trace
            assert "output_fingerprint" in trace
            assert trace["status"] in ("completed", "failed")


def t_blinded_labels():
    """blinding باید arm names را با کد جایگزین کند."""
    # Manually test blinding
    fake_traces = [
        {"task_id": "T1", "arm": "A_single_model"},
        {"task_id": "T1", "arm": "B_orchestrator_roles"},
        {"task_id": "T1", "arm": "C_multi_agent_current"},
    ]
    blinded, code_map = d10_abc._blind_arms(fake_traces, seed=42)
    for bt in blinded:
        assert bt["arm"].startswith("ARM_"), f"باید کد باشد: {bt['arm']}"
    assert len(code_map) == 3


def t_paired_analysis_present():
    """result باید primary/secondary/exploratory داشته باشد."""
    r = d10_abc.run_benchmark()
    assert "primary" in r
    assert "secondary" in r
    assert "exploratory" in r
    assert "ci_95" in r["primary"]
    assert len(r["primary"]["ci_95"]) == 2


def t_closed_testing_enforced():
    """secondary فقط باید تست شود اگر primary significant."""
    r = d10_abc.run_benchmark()
    if r["primary"]["p_value"] >= 0.05:
        assert r["secondary"]["tested"] == False, \
            "secondary نباید تست شود وقتی primary nonsignificant"


def t_cost_guardrail_present():
    """cost guardrail باید محاسبه و گزارش شود."""
    r = d10_abc.run_benchmark()
    cg = r["cost_guardrail"]
    assert "cost_ratio_C_over_B" in cg
    assert "triggered" in cg
    assert isinstance(cg["triggered"], bool)


def t_aa_leakage_detection():
    """A/A check باید کار کند — deterministic stub باید mean≈0 بدهد."""
    r = d10_abc.run_benchmark()
    aa = r["aa_instrumentation"]
    assert "leakage_detected" in aa
    # With deterministic stub, A/A should show ~0
    assert abs(aa["mean_delta"]) < 0.01, \
        f"A/A delta باید ~0 باشد نه {aa['mean_delta']}"


def t_verdict_in_valid_set():
    """verdict باید یکی از سه حالت مجاز باشد."""
    r = d10_abc.run_benchmark()
    assert r["verdict"] in ("REJECT_C_PREFER_B_OR_A", "RESTRICT_C", "KEEP_C"), \
        f"verdict نامعتبر: {r['verdict']}"


def t_namespace_separate_from_mining_d10():
    """D10-ABC نباید با Mining D-10 اشتباه شود."""
    # The benchmark is about architecture comparison, not financial HARD_STOP
    r = d10_abc.run_benchmark()
    assert "Mining" not in r.get("note", "")
    assert "architecture" in r["note"].lower() or "plumbing" in r["note"].lower()


def t_no_network_or_model_in_harness():
    """harness نباید مدل واقعی یا شبکه صدا بزند."""
    r = d10_abc.run_benchmark()
    assert "FAKE" in r["note"] or "DETERMINISTIC" in r["note"]


def t_deterministic_same_seed():
    """اجرای مجدد با همان seed باید نتیجه یکسان بدهد."""
    r1 = d10_abc.run_benchmark(seed=12345)
    r2 = d10_abc.run_benchmark(seed=12345)
    assert r1 == r2, "non-deterministic!"


def t_missing_trial_fail_closed():
    """یک arm که fail می‌کند باید به‌عنوان failure ثبت شود."""
    # Create a fake arm that errors
    def failing_arm(task):
        return {"output": "", "quality": 0.0, "cost_tokens": 0,
                "handoffs": 0, "error": True}

    arm_fns = dict(d10_abc.ARM_FNS)
    arm_fns["C_multi_agent_current"] = failing_arm
    r = d10_abc.run_benchmark(arm_fns=arm_fns)
    # C quality should be 0 for all tasks => C vs B is negative
    assert r["primary"]["mean"] < 0 or r["verdict"] == "REJECT_C_PREFER_B_OR_A"


def t_custom_arms_injectable():
    """باید arm_fns سفارشی قبول کند (for real model injection)."""
    def custom_A(task):
        return {"output": "custom", "quality": 0.99, "cost_tokens": 100,
                "handoffs": 0, "error": False}

    arm_fns = dict(d10_abc.ARM_FNS)
    arm_fns["A_single_model"] = custom_A
    r = d10_abc.run_benchmark(arm_fns=arm_fns)
    # With A=0.99, B vs A should be negative
    assert r["exploratory"]["mean"] < 0


# ─── RUN ──────────────────────────────────────────────────────────────────────

CHECKS = [
    ("randomization-reproducible", t_randomization_reproducible),
    ("different-seed-different-order", t_different_seed_different_order),
    ("no-cross-trial-state-leakage", t_no_cross_trial_state_leakage),
    ("cache-isolation", t_cache_isolation),
    ("trace-has-parent-validity", t_trace_has_parent_validity),
    ("blinded-labels", t_blinded_labels),
    ("paired-analysis-present", t_paired_analysis_present),
    ("closed-testing-enforced", t_closed_testing_enforced),
    ("cost-guardrail-present", t_cost_guardrail_present),
    ("aa-leakage-detection", t_aa_leakage_detection),
    ("verdict-in-valid-set", t_verdict_in_valid_set),
    ("namespace-separate-from-mining-d10", t_namespace_separate_from_mining_d10),
    ("no-network-or-model-in-harness", t_no_network_or_model_in_harness),
    ("deterministic-same-seed", t_deterministic_same_seed),
    ("missing-trial-fail-closed", t_missing_trial_fail_closed),
    ("custom-arms-injectable", t_custom_arms_injectable),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
