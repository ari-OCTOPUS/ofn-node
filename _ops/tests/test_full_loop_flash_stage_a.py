# -*- coding: utf-8 -*-
"""Stage A full-loop flash: no network, sidecar only, memory read-back, fail-closed."""
from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from lab.full_loop_flash import adapter, budget as flash_budget, gateway, judge, memory_lab, telemetry
from lab.full_loop_flash.stages import six_gates
from shadow_homeostasis.observation import Observation, Quality
from shadow_homeostasis.pipeline import run_shadow_pipeline
from shadow_homeostasis.replay import T0, fixtures

PKG = _OPS / "lab" / "full_loop_flash"


def _task_file(tmp: Path) -> Path:
    p = tmp / "task.md"
    p.write_text("# frontmatter debt OPEN\n", encoding="utf-8")
    return p


def _pulse_tree(tmp: Path) -> dict[str, Path]:
    org = tmp / "ORGANISM-STATE.json"
    arb = tmp / "arbiter-latest.json"
    life = tmp / "life-currency-latest.json"
    ident = tmp / "identities-latest.json"
    org.write_text(json.dumps({
        "ts": "2026-08-20T13:04:32", "started": "2026-08-20T11:47:04",
        "beat": 42855, "halted": None, "frozen": False,
        "math_control": {"identity_health": 0.672},
        "arbiter": {"effective_period_s": 113.73, "color": "GREEN"},
    }), encoding="utf-8")
    arb.write_text(json.dumps({
        "effective_period_s": 113.73, "color": "GREEN", "ts": "2026-08-20T13:04:08",
        "beat": 42855, "advisory_only": True, "wire_open": True,
    }), encoding="utf-8")
    life.write_text(json.dumps({
        "daily_cap": 30.0, "unit": "life_credit", "ts": "2026-08-20T13:04:08", "beat": 42855,
        "members": {"organism": {"tokens": 0.003}},
    }), encoding="utf-8")
    ident.write_text(json.dumps({"ts": "2026-08-20T01:49:50Z", "identities": {"learner": {"value": 1.0}}}), encoding="utf-8")
    return {
        "organism": org, "arbiter": arb, "life_currency": life,
        "identities": ident, "inbox_task": _task_file(tmp),
    }


def test_stage_a_pass_no_network(tmp_path):
    paths = _pulse_tree(tmp_path)
    lab = tmp_path / "lab"
    ev = tmp_path / "ev"
    pack = adapter.run_stage_a(lab_dir=lab, evidence_dir=ev, paths=paths, allow_network=False)
    assert pack["pass"] is True
    assert pack["network_sent"] is False
    assert pack["model_calls"] == 0
    assert pack["executable"] is False
    assert pack["executable_true_count"] == 0
    assert pack["k9_mixed"] is False
    assert pack["organism_py_patched"] is False
    assert pack["rendered"]["network"] is False
    assert pack["rendered"]["authorization_header"] == "ABSENT"
    assert "Bearer" not in json.dumps(pack["rendered"])
    assert pack["memory"]["readback"] == "PASS"
    assert pack["memory"]["after_readback"] is True
    assert pack["budget_reservation"]["k9_mixed"] is False
    assert (ev / "STAGE-A.md").exists()
    assert (ev / "RENDERED-REQUEST.json").exists()
    body = json.loads((ev / "RENDERED-REQUEST.json").read_text(encoding="utf-8"))
    assert "sk-" not in json.dumps(body)
    assert "DEEPSEEK_API_KEY" not in json.dumps(body)


def test_stage_a_rejects_network_flag(tmp_path):
    with pytest.raises(RuntimeError):
        adapter.run_stage_a(lab_dir=tmp_path, paths=_pulse_tree(tmp_path), allow_network=True)


def test_memory_write_then_readback(tmp_path):
    rec = memory_lab.write_lab(tmp_path, task_id="t", kind="x", payload={"hello": "world"})
    back = memory_lab.read_lab(tmp_path, rec["id"])
    assert back is not None
    assert back["record_hash"] == rec["record_hash"]
    assert back["payload"]["hello"] == "world"


def test_flash_budget_isolated_from_k9(tmp_path):
    r = flash_budget.reserve(tmp_path, est_aud=0.01, stage="A")
    assert r["ok"] is True
    assert r["k9_mixed"] is False
    b = flash_budget.load(tmp_path)
    assert b.max_calls == 12
    assert b.hard_stop_aud == 0.50
    with pytest.raises(flash_budget.BudgetError):
        flash_budget.reserve(tmp_path, est_aud=0.60, stage="A")


def test_metacontrol_fail_closed_future():
    obs = fixtures()["future"]
    pipe = run_shadow_pipeline(obs, decision_time=T0)
    assert pipe["executable"] is False
    assert judge.count_executable_true(pipe) == 0
    modes = {g["domain"]: g["mode"] for g in pipe["gate_decisions"]}
    assert any(m == "BLOCK" for m in modes.values())
    j = judge.advisory(pipeline=pipe, rendered={"evidence_ids": ["x"], "executable": False})
    assert j["executable"] is False
    assert j["confirmatory"] is False
    assert j["d6"] == "BETWEEN_RUN_VARIANCE"


def test_gateway_render_has_prompt_and_skills(tmp_path):
    pack = adapter.run_stage_a(lab_dir=tmp_path / "lab", paths=_pulse_tree(tmp_path))
    r = pack["rendered"]
    assert r["endpoint"] == "https://api.deepseek.com/chat/completions"
    assert r["body"]["model"] == "deepseek-v4-flash"
    assert r["skill_scores"]
    assert r["homeostatic_state"]
    assert r["budget_reservation"]["est_aud"] == 0.01
    user = r["body"]["messages"][1]["content"]
    assert "request_id" in user
    assert "executable=false" in user.lower() or "executable=false" in r["body"]["messages"][0]["content"].lower()


def test_six_gates_not_green_without_stage_b(tmp_path):
    pack = adapter.run_stage_a(lab_dir=tmp_path / "lab", paths=_pulse_tree(tmp_path))
    g = six_gates(pack, None)
    assert g["organism adapter"] == "READY"
    assert g["memory read-back"] == "PASS"
    assert g["DeepSeek handshake"] == "NOT_STARTED"
    assert g["external action"] == "OFF"
    assert g["Metacontrol fail-closed"] == "PASS"
    from lab.full_loop_flash.stages import all_green
    assert all_green(g) is False


def test_package_does_not_import_organism_or_credits():
    names = []
    blob = []
    for p in PKG.glob("*.py"):
        text = p.read_text("utf-8")
        blob.append(text)
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(a.name.split(".")[0] for a in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module.split(".")[0])
    text = "\n".join(blob)
    assert "organism" not in names
    assert "model_router" not in names
    assert "credits_to_aud" not in names


def test_hops_not_claimed_full_octopus(tmp_path):
    pack = adapter.run_stage_a(lab_dir=tmp_path / "lab", paths=_pulse_tree(tmp_path))
    assert pack["hops"]["full_octopus"] is False
    assert pack["hops"]["deepseek_flash_api"] is False
    assert pack["hops"]["label"] == "sidecar_preflight_no_network"
