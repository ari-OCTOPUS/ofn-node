#!/usr/bin/env python3
"""Deterministic snapshots of the real model_router decision path, fully mocked."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (_OPS, _OPS / "budget", _OPS / "cortex"):
    sys.path.insert(0, str(_p))

import harness  # noqa: E402
ENV = harness.setup("ti-router-snapshot")

import model_router as mr  # noqa: E402
from test_intelligence.adapters.model_router_adapter import (  # noqa: E402
    RouterScenario, run,
)
from test_intelligence.trace_schema import SCHEMA, TraceSink  # noqa: E402

ROOT = Path(ENV["root"])


def _paid(tier, model):
    return {"text": "mocked result", "tier": tier, "model": model,
            "cost_usd": 0.0, "finish_reason": "stop"}


def t_a_local_task_uses_only_mocked_local_seam():
    obs = run(mr, task="classify", prompt="raw prompt must not persist",
              scenario=RouterScenario(local_result={
                  "text": "local", "tier": "local", "model": "mock-local"}))
    assert obs.snapshot() == {
        "ok": True, "tier": "local", "model": "mock-local",
        "fallback_from": None, "reason": None,
        "paid_attempts": [], "local_attempts": 1,
    }


def t_b_secondary_selects_secondary_when_mock_succeeds():
    obs = run(mr, task="research", prompt="p",
              scenario=RouterScenario(
                  keys={"deepseek": True}, local_result=None,
                  paid_results={"secondary": _paid("secondary", "mock-secondary")}))
    assert obs.snapshot() == {
        "ok": True, "tier": "secondary", "model": "mock-secondary",
        "fallback_from": None, "reason": None,
        "paid_attempts": ["secondary"], "local_attempts": 0,
    }


def t_c_primary_selects_primary_when_mock_succeeds():
    obs = run(mr, task="orchestrate", prompt="p",
              scenario=RouterScenario(
                  keys={"fugu": True}, local_result=None,
                  paid_results={"primary": _paid("primary", "mock-primary")}))
    assert obs.snapshot()["tier"] == "primary"
    assert obs.snapshot()["paid_attempts"] == ["primary"]
    assert obs.local_attempts == 0


def t_d_primary_failure_falls_to_secondary_in_stable_order():
    obs = run(mr, task="deep", prompt="p",
              scenario=RouterScenario(
                  keys={"fugu": True, "deepseek": True}, local_result=None,
                  paid_results={"primary": None,
                                "secondary": _paid("secondary", "mock-secondary")}))
    assert obs.paid_attempts == ("primary", "secondary")
    assert obs.result["ok"] is True and obs.result["tier"] == "secondary"


def t_e_paid_failure_records_fallback_reason_then_uses_local():
    obs = run(mr, task="deep", prompt="p",
              scenario=RouterScenario(
                  keys={"fugu": True},
                  local_result={"text": "local fallback", "tier": "local",
                                "model": "mock-local"},
                  paid_results={"primary": None}))
    snap = obs.snapshot()
    assert snap["paid_attempts"] == ["primary"]
    assert snap["tier"] == "local" and snap["local_attempts"] == 1
    assert snap["fallback_from"] == "primary: paid-call-failed"


def t_f_closed_paid_gate_never_attempts_paid_provider():
    obs = run(mr, task="research", prompt="p",
              scenario=RouterScenario(
                  keys={"deepseek": True}, paid_gate_open=False,
                  paid_gate_reason="activation-missing",
                  local_result={"text": "local", "tier": "local", "model": "mock-local"}))
    assert obs.paid_attempts == ()
    assert obs.result["fallback_from"] == "secondary: activation-missing"


def t_g_trace_is_digest_only_append_only_and_stable_shape():
    path = ROOT / "trace" / "router.jsonl"
    sink = TraceSink(path)
    secret = "prompt-should-never-appear"
    run(mr, task="classify", prompt=secret,
        scenario=RouterScenario(local_result={
            "text": "private-output", "tier": "local", "model": "mock-local"}),
        trace_sink=sink, trace_id="tr-router", event_id="ev-1")
    run(mr, task="classify", prompt=secret,
        scenario=RouterScenario(local_result={
            "text": "private-output", "tier": "local", "model": "mock-local"}),
        trace_sink=sink, trace_id="tr-router", event_id="ev-2")
    raw = path.read_text("utf-8")
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == 2
    assert secret not in raw and "private-output" not in raw
    assert rows[0]["schema"] == SCHEMA
    assert rows[0]["component"] == "octopus.cortex.model_router"
    assert rows[0]["attempted"] is True
    assert rows[0]["authorized"] is True
    assert rows[0]["executed"] is True
    assert rows[0]["tool_call_count"] == 1
    assert rows[0]["input_digest"].startswith("sha256:")


def t_h_adapter_restores_every_patched_production_global():
    before = (mr.local_llm.ask, mr.keys_present, mr.paid_gate, mr._ask_paid,
              mr.opslib.STOP_ORGANISM, mr.opslib.halted, mr.opslib.alert)
    run(mr, task="classify", prompt="p",
        scenario=RouterScenario(local_result={
            "text": "x", "tier": "local", "model": "mock-local"}))
    after = (mr.local_llm.ask, mr.keys_present, mr.paid_gate, mr._ask_paid,
             mr.opslib.STOP_ORGANISM, mr.opslib.halted, mr.opslib.alert)
    assert before == after


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_ti_router_snapshot: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
