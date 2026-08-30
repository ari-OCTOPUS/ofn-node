# -*- coding: utf-8 -*-
"""T26 replay eight scenarios + T27 architecture / no-executable traverse."""
from pathlib import Path
import ast
import json
import sys

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from shadow_homeostasis.metacontrol import assert_no_executable
from shadow_homeostasis.replay import run_all
from shadow_homeostasis.pipeline import run_shadow_pipeline
from shadow_homeostasis.replay import fixtures, T0

PKG = _OPS / "shadow_homeostasis"
FORBIDDEN = {
    "planner", "policy", "policy_gate", "money_gate", "model_router",
    "actuator", "credits_to_aud", "cron", "schedule",
}


def test_replay_eight_scenarios(tmp_path):
    summary = run_all(tmp_path)
    assert set(summary["scenarios"]) >= {
        "healthy", "restart_hrv", "period_conflict", "latest_only",
        "future", "missing_identity", "c042", "color_empty_reasons",
    }
    r = summary["scenarios"]["restart_hrv"]
    assert r["global_state"] in ("WARMUP", "UNKNOWN", "AMBER")
    # cardiac warmup should dominate or appear
    assert r["assessment_reasons_n"] > 0
    c042 = summary["scenarios"]["c042"]
    assert any(g["executable"] is False for g in c042["gates"])
    fut = summary["scenarios"]["future"]
    assert fut["excluded_n"] >= 1
    miss = summary["scenarios"]["missing_identity"]
    assert miss["global_state"] in ("UNKNOWN", "AMBER", "WARMUP", "GREEN")
    conf = summary["scenarios"]["period_conflict"]
    assert all(g["executable"] is False for g in conf["gates"])
    # deterministic
    s2 = run_all(tmp_path / "b")
    assert s2["scenarios"]["healthy"]["output_hash"] == summary["scenarios"]["healthy"]["output_hash"]


def test_no_executable_anywhere():
    for name, obs in fixtures().items():
        pipe = run_shadow_pipeline(obs, decision_time=T0)
        blob = json.dumps(pipe, default=str)
        assert '"executable": true' not in blob.lower().replace(" ", "")
        assert pipe["executable"] is False
        assert pipe["homeostatic_assessment"]["executable"] is False
        assert pipe["world_state"]["executable"] is False
        assert assert_no_executable(pipe["gate_decisions"]) == 0


def test_forbidden_imports_ast():
    hits = []
    for p in PKG.glob("*.py"):
        tree = ast.parse(p.read_text("utf-8"), filename=str(p))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for n in names:
                if n in FORBIDDEN:
                    hits.append(f"{p.name}:{n}")
    assert hits == [], hits
