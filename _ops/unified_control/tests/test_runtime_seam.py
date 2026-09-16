#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

OPS = Path(__file__).resolve().parents[2]
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from unified_control import pipeline


def _pre(pid="cycle-A:g"):
    return {"prereg_id": pid, "goal": "اولین پول مطالبه‌شده",
            "goal_key": "g", "direction": "درآمد", "method": "بررسی لید",
            "method_index": 0, "metric_path": "fitness-latest.json",
            "metric_key": "attribution.claimed", "baseline": 0,
            "target": {"op": ">", "value": 0}}


def t_exact_prereg_is_threaded_to_request_and_mission():
    p = _pre()
    r = pipeline.prepare_records(
        directions=["درآمد"], prereg=p,
        heart={"authority": "ADVISORY_SHADOW", "production_open": False,
               "data": {"period_s": 50}},
        self_model_authority="STALE", innervation={"coverage_pct": 80}, now=1)
    assert r["ok"]
    assert r["request"]["prereg_id"] == p["prereg_id"]
    assert r["mission"]["trace_id"] == r["graph"]["trace_id"]


def t_different_prereg_produces_different_action_identity():
    a = pipeline.prepare_records(directions=["درآمد"], prereg=_pre("A:g"),
        heart={"authority": "ADVISORY_SHADOW", "production_open": False,
               "data": {"period_s": 50}}, now=1)
    b = pipeline.prepare_records(directions=["درآمد"], prereg=_pre("B:g"),
        heart={"authority": "ADVISORY_SHADOW", "production_open": False,
               "data": {"period_s": 50}}, now=1)
    assert a["request"]["action_id"] != b["request"]["action_id"]
    assert a["mission"]["mission_id"] != b["mission"]["mission_id"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for fn in tests:
        fn()
    print(f"OK {len(tests)}")
