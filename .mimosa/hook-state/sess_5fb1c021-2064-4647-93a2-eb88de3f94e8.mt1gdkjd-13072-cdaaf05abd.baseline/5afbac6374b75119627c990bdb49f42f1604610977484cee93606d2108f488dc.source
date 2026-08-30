#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
OPS = PKG.parent
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from unified_control import pipeline


def t_prepare_live_goal_without_execution():
    r = pipeline.prepare()
    assert r["ok"], r.get("translation")
    assert r["status"] == "PREPARED_NOT_EXECUTED"
    assert r["mission"]["trace_id"] == r["graph"]["trace_id"]
    assert r["request"]["prereg_id"] == r["compass"]["prereg_id"]
    assert r["plan"]["decision"] in ("OWNER_GATE", "BLOCK", "ALLOW")
    assert r["graph"]["end_to_end_complete"] is False


def t_current_claimed_goal_requires_owner_gate():
    r = pipeline.prepare()
    assert r["request"]["action_type"] == "owner_action_card"
    assert r["plan"]["classification"] == "A3"
    assert r["plan"]["decision"] == "OWNER_GATE"


def t_prepare_has_zero_external_effect_and_cost():
    r = pipeline.prepare()
    assert r["request"]["external_effect"] is False
    assert r["request"]["estimated_cost"] == 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for fn in tests:
        fn()
    print(f"OK {len(tests)}")
