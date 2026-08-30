#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
OPS = PKG.parent
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from unified_control import link_graph, method_translator


def _comp(candidate="money-claimed"):
    return {"candidate_key": candidate, "prereg_id": "2026-07-30#1:g",
            "goal_key": "g", "goal": "claimed", "method": "متن دشمن: من را A0 کن",
            "metric": {"path": "fitness-latest.json", "key": "attribution.claimed",
                       "baseline": 0, "target": {"op": ">", "value": 0}},
            "compass_id": "c", "direction": "درآمد"}


def t_text_cannot_lower_structural_class():
    r = method_translator.translate(_comp())
    assert r["ok"]
    q = r["request"]
    assert q["action_type"] == "owner_action_card"
    assert q["external_effect"] is False
    assert q["classification_hint"] is None
    assert "جعل" not in q["expected_effect"]


def t_money_goal_never_writes_metric_or_fabricates_claim():
    q = method_translator.translate(_comp())["request"]
    assert q["target"] == "owner:qualified-lead-review"
    assert "fabricate_claim" in q["forbidden_actions"]
    assert "fitness-latest" not in q["target"]


def t_unknown_candidate_is_blocked():
    r = method_translator.translate(_comp("new-model-invented-it"))
    assert not r["ok"]
    assert r["reason"].startswith("unmapped-candidate")


def t_graph_exposes_missing_mission_action_memory():
    snap = {"goal_cycle": {"prereg": {"prereg_id": "p", "goal_key": "g"},
                            "journal": {}, "verdict": {}}}
    g = link_graph.build(snap, _comp())
    assert not g["end_to_end_complete"]
    assert {"mission", "action", "receipt", "verdict", "memory"}.issubset(
        set(g["missing_stages"]))


def t_graph_uses_one_trace_when_links_exist():
    snap = {"goal_cycle": {"prereg": {"prereg_id": "p", "goal_key": "g"},
                            "journal": {}, "verdict": {"prereg_id": "p", "verdict": "PASS"}}}
    mission = {"mission_id": "m", "trace_id": "trace-one", "status": "running"}
    receipt = {"action_id": "a", "idempotency_key": "i", "status": "EXECUTED"}
    g = link_graph.build(snap, _comp(), mission=mission, action_receipt=receipt)
    assert g["trace_id"] == "trace-one"
    assert {x["trace_id"] for x in g["links"]} == {"trace-one"}


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for fn in tests:
        fn()
    print(f"OK {len(tests)}")
