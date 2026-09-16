#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
OPS = PKG.parent
for p in (str(OPS), str(PKG.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from unified_control import compass, snapshot


def t_live_snapshot_never_promotes_closed_shadow_heart():
    s = snapshot.build()
    h = s["heart"]
    assert h["authority"] in ("ADVISORY_SHADOW", "STALE", "MISSING")
    if h.get("production_open") is False:
        assert h["authority"] != "AUTHORITATIVE"
        assert "heart-production-wire-closed" in s["blockers"]


def t_stale_self_model_degrades_compass():
    s = {
        "directions": ["درآمد"],
        "self_model": {"authority": "STALE"},
        "cortex": {"data": {"coherence": .8}},
        "heart": {"authority": "ADVISORY_SHADOW", "data": {"period_s": 50},
                  "production_open": False},
        "innervation": {"coverage_pct": 80},
        "goal_cycle": {"prereg": {"prereg_id": "c:g", "goal": "هدف",
            "goal_key": "g", "direction": "درآمد", "metric_path": "x.json",
            "metric_key": "x", "baseline": 0, "target": {"op": ">", "value": 0},
            "method": "مشاهده", "method_index": 0}},
        "owner_guidance": {"latest": None},
    }
    c = compass.build(s)
    assert c["readiness"] == "DEGRADED"
    assert c["cadence_authority"] == "heart-shadow-advisory"
    assert c["semantic_authority"] == "owner-direction+frozen-prereg"


def t_heart_cannot_replace_semantic_direction():
    s = {
        "directions": ["مالک"], "self_model": {"authority": "AUTHORITATIVE"},
        "cortex": {"data": {}},
        "heart": {"authority": "AUTHORITATIVE", "data": {"period_s": 1,
                  "goal": "قلب"}, "production_open": True},
        "innervation": {"coverage_pct": 100},
        "goal_cycle": {"prereg": {"prereg_id": "p", "goal": "هدف مالک",
            "goal_key": "g", "direction": "جهت مالک", "metric_path": "m",
            "metric_key": "k", "baseline": 0, "target": {"op": ">", "value": 0},
            "method": "روش", "method_index": 0}},
        "owner_guidance": {"latest": None},
    }
    c = compass.build(s)
    assert c["direction"] == "جهت مالک"
    assert c["goal"] == "هدف مالک"
    assert c["heart"]["regulation_only"] is True


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for fn in tests:
        fn()
    print(f"OK {len(tests)}")
