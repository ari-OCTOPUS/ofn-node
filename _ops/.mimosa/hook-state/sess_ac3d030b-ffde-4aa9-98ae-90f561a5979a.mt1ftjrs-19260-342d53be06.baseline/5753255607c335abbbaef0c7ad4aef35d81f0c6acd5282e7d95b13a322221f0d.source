#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

OPS = Path(__file__).resolve().parents[2]
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from unified_control import guidance_policy, rhythm_policy


def t_closed_shadow_requires_explicit_advisory_use():
    h = {"authority": "ADVISORY_SHADOW", "production_open": False,
         "data": {"period_s": 50}}
    d = rhythm_policy.decide(h, default_period_s=120, allow_shadow=False)
    assert d["period_s"] == 120
    assert d["authority"] == "DEFAULT"


def t_shadow_use_remains_labelled_shadow():
    h = {"authority": "ADVISORY_SHADOW", "production_open": False,
         "data": {"period_s": 50}}
    d = rhythm_policy.decide(h, allow_shadow=True)
    assert d["period_s"] == 100
    assert d["authority"] == "ADVISORY_SHADOW"


def t_production_heart_is_authoritative_only_when_open():
    h = {"authority": "AUTHORITATIVE", "production_open": True,
         "data": {"period_s": 40}}
    d = rhythm_policy.decide(h)
    assert d["period_s"] == 80
    assert d["authority"] == "AUTHORITATIVE"


def t_guidance_cannot_move_frozen_target():
    p = {"goal_key": "g", "baseline": 0, "target": {"op": ">", "value": 0},
         "metric_key": "x", "goal": "old"}
    r = guidance_policy.apply(p, {"focus": "نقاشی", "goal": "new",
                                  "target": {"op": ">", "value": -1}})
    assert r["effective_now"] == {"focus": "نقاشی"}
    assert set(r["blocked_overrides"]) == {"goal", "target"}
    assert r["frozen"] == p
    assert r["goal_unchanged"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for fn in tests:
        fn()
    print(f"OK {len(tests)}")
