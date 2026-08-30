#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_semantic_trace_ablation — تست‌های WP-C: semantic trace + ablation harness.

دو بخش:
  1. semantic_trace.py: trace instrumentation (PII safety، default OFF، hash-only)
  2. semantic_ablation.py: paired ablation harness (deterministic stub، CI، per-task)
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "cortex"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("semantic-trace-ablation")

STATE_DIR = ENV["ops"] / "state"


# ─── TRACE TESTS ──────────────────────────────────────────────────────────────

def t_trace_default_off():
    """trace باید default OFF باشد."""
    import semantic_trace as st
    st.TRACE_PATH = STATE_DIR / "cortex" / "semantic-trace.jsonl"
    os.environ.pop("OCTOPUS_WIRE_SEMANTIC_TRACE", None)
    assert not st._is_enabled(), "باید OFF باشد وقتی flag غایب"


def t_trace_enabled_when_armed():
    """trace باید ON باشد وقتی flag=1."""
    import semantic_trace as st
    os.environ["OCTOPUS_WIRE_SEMANTIC_TRACE"] = "1"
    assert st._is_enabled()
    os.environ.pop("OCTOPUS_WIRE_SEMANTIC_TRACE", None)


def t_trace_never_stores_gist_content():
    """gist_text هرگز در trace ذخیره نمی‌شود — فقط hash/bucket."""
    import semantic_trace as st
    st.TRACE_PATH = STATE_DIR / "cortex" / "semantic-trace-off.jsonl"
    if st.TRACE_PATH.exists():
        st.TRACE_PATH.unlink()
    os.environ["OCTOPUS_WIRE_SEMANTIC_TRACE"] = "1"
    secret_gist = "THIS_IS_SECRET_CONTENT_12345"
    st.record_cycle(
        cycle=1,
        gist_text=secret_gist,
        gist_injected=True,
        router_called=True,
        router_status="ok",
        output_text="OUTPUT_SECRET_67890",
    )
    os.environ.pop("OCTOPUS_WIRE_SEMANTIC_TRACE", None)
    content = st.TRACE_PATH.read_text("utf-8")
    assert "THIS_IS_SECRET_CONTENT_12345" not in content, "gist خام نشت کرده!"
    assert "OUTPUT_SECRET_67890" not in content, "output خام نشت کرده!"
    record = json.loads(content.strip().splitlines()[-1])
    assert record["gist_hash"], "gist_hash باید موجود باشد"
    assert record["gist_length_bucket"] in ("short", "medium", "long", "empty")


def t_trace_records_attempted_vs_read_ok():
    """attempted و read_ok باید مستقل باشند."""
    import semantic_trace as st
    st.TRACE_PATH = STATE_DIR / "cortex" / "semantic-trace-a.jsonl"
    if st.TRACE_PATH.exists():
        st.TRACE_PATH.unlink()
    os.environ["OCTOPUS_WIRE_SEMANTIC_TRACE"] = "1"
    st.record_cycle(cycle=1, semantic_memory_attempted=True,
                    semantic_memory_read_ok=False)
    os.environ.pop("OCTOPUS_WIRE_SEMANTIC_TRACE", None)
    record = json.loads(st.TRACE_PATH.read_text("utf-8").strip())
    assert record["semantic_memory_attempted"] == True
    assert record["semantic_memory_read_ok"] == False


def t_trace_disabled_returns_none():
    """وقتی OFF است، record_cycle باید None برگرداند."""
    import semantic_trace as st
    os.environ.pop("OCTOPUS_WIRE_SEMANTIC_TRACE", None)
    result = st.record_cycle(cycle=1)
    assert result is None


def t_trace_summary_works():
    """summary باید آمار تازه برگرداند."""
    import semantic_trace as st
    st.TRACE_PATH = STATE_DIR / "cortex" / "semantic-trace-s.jsonl"
    if st.TRACE_PATH.exists():
        st.TRACE_PATH.unlink()
    os.environ["OCTOPUS_WIRE_SEMANTIC_TRACE"] = "1"
    for i in range(5):
        st.record_cycle(cycle=i, gist_text=f"gist {i}" * 10,
                        gist_injected=True, router_status="ok")
    os.environ.pop("OCTOPUS_WIRE_SEMANTIC_TRACE", None)
    s = st.summary()
    assert s["n"] == 5
    assert s["injected_rate"] == 1.0


# ─── ABLATION TESTS ───────────────────────────────────────────────────────────

def t_ablation_paired_structure():
    """هر task باید control و treatment داشته باشد (paired)."""
    import semantic_ablation as sa
    result = sa.run_ablation()
    for r in result["per_task"]:
        assert "control_quality" in r
        assert "treatment_quality" in r
        assert "delta" in r
        assert isinstance(r["delta"], (int, float))


def t_ablation_ci_present():
    """bootstrap CI باید موجود و معقول باشد."""
    import semantic_ablation as sa
    result = sa.run_ablation()
    assert "ci_95" in result
    assert len(result["ci_95"]) == 2
    assert result["ci_95"][0] <= result["ci_95"][1]


def t_ablation_deterministic():
    """اجرای مجدد باید نتیجه یکسان بدهد (deterministic stub)."""
    import semantic_ablation as sa
    r1 = sa.run_ablation()
    r2 = sa.run_ablation()
    assert r1["mean_delta"] == r2["mean_delta"], "non-deterministic!"
    assert r1["ci_95"] == r2["ci_95"]


def t_ablation_output_changed_tracked():
    """output_changed باید مستقل از delta tracked شود."""
    import semantic_ablation as sa
    result = sa.run_ablation()
    assert "n_output_changed" in result
    assert result["n_output_changed"] <= result["n_tasks"]


def t_ablation_no_network():
    """harness نباید شبکه/مدل واقعی صدا بزند (deterministic stub)."""
    import semantic_ablation as sa
    # The default model_fn is the stub — no network calls
    result = sa.run_ablation()
    assert result["note"].startswith("Harness test")


def t_ablation_mean_delta_calculated():
    """mean_delta باید میانگینِ deltaها باشد."""
    import semantic_ablation as sa
    result = sa.run_ablation()
    deltas = [r["delta"] for r in result["per_task"]]
    expected = round(sum(deltas) / len(deltas), 4)
    assert abs(result["mean_delta"] - expected) < 0.001


def t_ablation_custom_model_fn():
    """باید model_fn سفارشی قبول کند (for real model injection later)."""
    import semantic_ablation as sa

    calls = []

    def fake_fn(prompt, task):
        calls.append((prompt[:20], task[:20]))
        # treatment prompt has "بازتاب" (the Persian marker for gist injection)
        q = 0.5 if "بازتاب" in prompt else 0.4
        return f"out_{task[:5]}", q

    result = sa.run_ablation(model_fn=fake_fn)
    assert len(calls) == len(sa.TASKS) * 2  # control + treatment
    assert result["mean_delta"] > 0  # treatment always higher in this fake


def t_ablation_gist_absent_means_no_treatment():
    """اگر gist غایب، treatment باید برابر control باشد."""
    import semantic_ablation as sa
    # Remove all gists
    empty_gists = {t["task_id"]: "" for t in sa.TASKS}
    result = sa.run_ablation(gists=empty_gists)
    for r in result["per_task"]:
        assert not r["gist_present"], "gist باید غایب باشد"
        assert r["delta"] == 0.0, f"delta باید 0 باشد نه {r['delta']}"


# ─── RUN ──────────────────────────────────────────────────────────────────────

CHECKS = [
    ("trace-default-off", t_trace_default_off),
    ("trace-enabled-when-armed", t_trace_enabled_when_armed),
    ("trace-never-stores-gist-content", t_trace_never_stores_gist_content),
    ("trace-attempted-vs-read-ok", t_trace_records_attempted_vs_read_ok),
    ("trace-disabled-returns-none", t_trace_disabled_returns_none),
    ("trace-summary-works", t_trace_summary_works),
    ("ablation-paired-structure", t_ablation_paired_structure),
    ("ablation-ci-present", t_ablation_ci_present),
    ("ablation-deterministic", t_ablation_deterministic),
    ("ablation-output-changed-tracked", t_ablation_output_changed_tracked),
    ("ablation-no-network", t_ablation_no_network),
    ("ablation-mean-delta-calculated", t_ablation_mean_delta_calculated),
    ("ablation-custom-model-fn", t_ablation_custom_model_fn),
    ("ablation-gist-absent-no-treatment", t_ablation_gist_absent_means_no_treatment),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
