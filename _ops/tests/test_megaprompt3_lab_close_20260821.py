#!/usr/bin/env python3
"""Megaprompt 3 — laboratory loop closure (isolated state).

Does not write production _ops/state/lab. Does not send Telegram.
Report this filename for run_all.py; do not self-register (WORKLOCK).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "lab"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402

ENV = harness.setup("megaprompt3-lab-close")
_ISOLATED = Path(tempfile.mkdtemp(prefix="mp3-lab-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_ISOLATED / "_ops" / "state")

import registry as lab  # noqa: E402
import close_wave1_loops as closer  # noqa: E402


PROD_LAB = _OPS / "state" / "lab" / "DECISION-REGISTRY.jsonl"


def t_a_closes_24_without_touching_production_lab():
    before = PROD_LAB.read_bytes() if PROD_LAB.is_file() else b""
    out = closer.close_loops()
    after = PROD_LAB.read_bytes() if PROD_LAB.is_file() else b""
    assert out["all_24"] is True, out
    assert out["latest_count"] >= 24, out
    assert out["result_counts"]["SUPPORTED"] >= 15, out
    assert out["result_counts"]["INCONCLUSIVE"] >= 1, out
    assert after == before, "production DECISION ledger must be unchanged"


def t_b_canary_proposed_not_marked_supported_from_fixtures():
    closer.close_loops()
    latest = lab.latest_conclusions()
    for eid in ("EXP-TG-003", "EXP-TG-005"):
        assert latest[eid]["result"] == "INCONCLUSIVE", latest[eid]


def t_c_preregistration_hash_stable_after_conclusion():
    closer.close_loops()
    card = {
        "experiment_id": "EXP-SEC-001", "loop_id": "LOOP-LAB-SECURITY",
        "question": "x", "hypothesis": "h", "null_hypothesis": "n",
        "falsifier": "f", "metrics": ["pass/fail"], "denominator": "d",
        "controls": ["c"], "sample_plan": {"min_runs": 1},
        "stop_conditions": ["s"], "budgets": {"max_runs": 1},
        "rollback": "r", "kill_switch": "k",
        "negative_outcome_policy": "retain", "execution_mode": "FIXTURE_ONLY",
        "result": "PENDING", "preregistered_at": "2026-08-21T00:00:00Z",
        "code_head": "a" * 40, "fixture_hash": "h" * 64,
        "telegram_surface": "STATUS", "miniapp_route": "/lab/experiments/x",
    }
    h_pending = lab.preregister_hash(card)
    card["result"] = "SUPPORTED"
    assert lab.preregister_hash(card) == h_pending


def t_d_invalid_result_rejected():
    r = lab.conclude_experiment("EXP-SEC-001", result="GREEN")
    assert r.get("ok") is False


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_megaprompt3_lab_close_20260821: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
