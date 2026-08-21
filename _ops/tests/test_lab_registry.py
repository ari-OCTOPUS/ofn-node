#!/usr/bin/env python3
"""Laboratory registry schema contract — fixture-only, isolated state."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import harness

ENV = harness.setup("lab-registry")
_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "lab") not in sys.path:
    sys.path.insert(0, str(_OPS / "lab"))

import registry as lab  # noqa: E402


def _card(eid="exp_fixture", **overrides):
    card = {
        "experiment_id": eid, "loop_id": "LOOP-LAB-FIXTURE",
        "question": "Is the fixture card schema enforced?",
        "hypothesis": "missing fields are rejected",
        "null_hypothesis": "missing fields pass",
        "falsifier": "a card without metrics is registered",
        "metrics": ["schema errors"], "denominator": "fixture cards",
        "controls": ["isolated state"], "sample_plan": {"min_runs": 1},
        "stop_conditions": ["any error"], "budgets": {"max_runs": 1},
        "rollback": "temp state", "kill_switch": "isolated env",
        "negative_outcome_policy": "retain", "execution_mode": "FIXTURE_ONLY",
        "result": "PENDING", "preregistered_at": "2026-08-21T00:00:00Z",
        "code_head": "a" * 40, "fixture_hash": "h" * 64,
        "telegram_surface": "STATUS", "miniapp_route": "/lab/experiments/x",
    }
    card.update(overrides)
    return card


def t_a_card_validation_rejects_missing_required_fields():
    errors = lab.validate_experiment_card({})
    for field in ("question", "hypothesis", "null_hypothesis", "falsifier",
                  "metrics", "sample_plan", "stop_conditions", "budgets",
                  "rollback", "kill_switch", "negative_outcome_policy"):
        assert f"missing-{field}" in errors, (field, errors)
    assert "missing-falsifier" in errors


def t_b_valid_card_passes_and_preregistration_hash_is_canonical():
    card = _card()
    assert lab.validate_experiment_card(card) == []
    h1 = lab.preregister_hash(card)
    h2 = lab.preregister_hash(dict(card))
    assert h1 == h2 and len(h1) == 64
    # result/evidence/verifier must not change the preregistration hash
    changed = dict(card); changed["result"] = "SUPPORTED"
    changed["evidence_refs"] = ["x"]
    assert lab.preregister_hash(changed) == h1


def t_c_amendment_changes_preregistration_hash():
    card = _card()
    h_before = lab.preregister_hash(card)
    amended = dict(card); amended["falsifier"] = "different falsifier"
    assert lab.preregister_hash(amended) != h_before


def t_d_registration_writes_append_only_ledger():
    card = _card(eid="exp_append")
    out = lab.register_experiment(card)
    assert out["ok"] and out["preregistration_hash"]
    path = lab._ledger("EXPERIMENT")
    lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert lines and lines[-1]["card"]["experiment_id"] == "exp_append"
    assert lines[-1]["preregistration_hash"] == out["preregistration_hash"]


def t_e_records_require_experiment_id_and_ts():
    assert lab.append_record("OBSERVATION", {"metric": "x"})["ok"] is False
    ok = lab.append_record("OBSERVATION", {"experiment_id": "exp_append",
                                           "ts": "2026-08-21T00:00:00Z", "metric": "x"})
    assert ok["ok"]


def t_f_invalid_execution_mode_and_result_rejected():
    errors = lab.validate_experiment_card(_card(execution_mode="LIVE"))
    assert any("invalid-execution-mode" in e for e in errors)
    errors = lab.validate_experiment_card(_card(result="GREEN"))
    assert any("invalid-result" in e for e in errors)


def t_g_owner_experiment_seed_registers():
    results = lab.seed_owner_experiments()
    assert results["errors"] == [], results
    assert results["ok"] >= 24, results


def t_h_seed_cards_are_fixture_or_canary_proposed_only():
    path = lab._ledger("EXPERIMENT")
    modes = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        card = row.get("card", {})
        if str(card.get("experiment_id", "")).startswith("EXP-"):
            modes.add(card.get("execution_mode"))
    assert modes <= {"FIXTURE_ONLY", "CANARY_PROPOSED"}, modes


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_lab_registry: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
