#!/usr/bin/env python3
"""Phase 1 (shadow placement) acceptance tests.

The scan names three acceptance criteria for shadow placement:
  1. no task is assigned to a stale, hot or memory-pressured node
  2. deterministic replay yields the same placement from the same snapshot
  3. owner pause blocks all new leases

These tests pin those three, plus the anti-copy rule that an unverifiable node
is never chosen.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import compute_core as cc  # noqa: E402

POLICY = dict(cc.DEFAULT_POLICY)


def telemetry(node_utc=None, **over) -> dict:
    t = {
        "ok": True,
        "node_utc": node_utc or cc.utc_now(),
        "nproc": 8,
        "load1": 0.1,
        "cpu_pct": 0.5,
        "mem_used_pct": 7.0,
        "mem_avail_kb": 3_600_000,
        "hottest_millic": 24_100,
        "disk_root_used_pct": "5%",
        "liveness_proven": True,
    }
    t.update(over)
    return t


def snapshot() -> list[dict]:
    """A realistic four-node arrival snapshot, mirroring a live decision record."""
    return [
        {"node_id": "114", "capability": {"schema": "worker_capability.v1"}, "failure_count": 0,
         "telemetry": telemetry(hottest_millic=24_071, cpu_pct=1.0, load1=0.07)},
        {"node_id": "160", "capability": {"schema": "worker_capability.v1"}, "failure_count": 0,
         "telemetry": telemetry(hottest_millic=24_071, cpu_pct=0.5, load1=0.27)},
        {"node_id": "100", "capability": {"schema": "worker_capability.v1"}, "failure_count": 0,
         "telemetry": telemetry(hottest_millic=28_692, cpu_pct=6.3, load1=0.08)},
        {"node_id": "193", "capability": {"schema": "worker_capability.v1"}, "failure_count": 0,
         "telemetry": telemetry(hottest_millic=25_923, cpu_pct=0.4, load1=0.02)},
    ]


class TestShadowAcceptance(unittest.TestCase):
    def test_deterministic_replay_same_snapshot_same_placement(self):
        """Criterion 2: replaying one snapshot must not drift."""
        first = cc.select_placement(snapshot(), POLICY, require_capability=True)
        second = cc.select_placement(snapshot(), POLICY, require_capability=True)
        self.assertEqual(first["chosen"]["node_id"], second["chosen"]["node_id"])
        self.assertEqual(
            [(e["node_id"], e["score"]) for e in first["evaluated"]],
            [(e["node_id"], e["score"]) for e in second["evaluated"]],
        )

    def test_stale_node_never_chosen_even_if_coldest(self):
        """Criterion 1: a stale measurement is UNKNOWN, not an invitation."""
        stale = cc.plus_seconds(cc.utc_now(), -900)
        cands = snapshot()
        cands[0]["telemetry"] = telemetry(node_utc=stale, hottest_millic=15_000, cpu_pct=0.0, load1=0.0)
        res = cc.select_placement(cands, POLICY, require_capability=True)
        self.assertNotEqual(res["chosen"]["node_id"], "114")
        v114 = [e for e in res["evaluated"] if e["node_id"] == "114"][0]
        self.assertFalse(v114["admit"])
        self.assertTrue(any(r.startswith("STALE_TELEMETRY") for r in v114["reasons"]))

    def test_hot_node_never_chosen(self):
        cands = snapshot()
        cands[0]["telemetry"] = telemetry(hottest_millic=71_500, cpu_pct=0.0)
        res = cc.select_placement(cands, POLICY, require_capability=True)
        v114 = [e for e in res["evaluated"] if e["node_id"] == "114"][0]
        self.assertFalse(v114["admit"])
        self.assertTrue(any(r.startswith("THERMAL") for r in v114["reasons"]))

    def test_memory_pressured_node_never_chosen(self):
        cands = snapshot()
        cands[0]["telemetry"] = telemetry(mem_used_pct=93.0, mem_avail_kb=120_000)
        res = cc.select_placement(cands, POLICY, require_capability=True)
        v114 = [e for e in res["evaluated"] if e["node_id"] == "114"][0]
        self.assertFalse(v114["admit"])

    def test_node_without_agent_not_dispatchable(self):
        """Placement is capability-driven: no capability record, no lease."""
        cands = snapshot()
        cands[0]["capability"] = None
        res = cc.select_placement(cands, POLICY, require_capability=True)
        v114 = [e for e in res["evaluated"] if e["node_id"] == "114"][0]
        self.assertFalse(v114["admit"])
        self.assertIn("AGENT_ABSENT", v114["reasons"])

    def test_owner_pause_blocks_all_placements(self):
        """Criterion 3: owner pause means no leases at all."""
        paused = dict(POLICY, allowed_nodes=[])
        res = cc.select_placement(snapshot(), paused, require_capability=True)
        self.assertIsNone(res["chosen"])
        self.assertEqual(res["reason"], "NO_ADMISSIBLE_NODE")
        for e in res["evaluated"]:
            self.assertFalse(e["admit"])
            self.assertIn("NODE_NOT_ALLOWED", e["reasons"])

    def test_every_verdict_carries_a_reason_when_refused(self):
        """A refusal without a reason code is unusable in an audit."""
        cands = snapshot()
        cands[0]["telemetry"] = telemetry(hottest_millic=80_000, mem_used_pct=95.0, load1=9.9)
        res = cc.select_placement(cands, POLICY, require_capability=True)
        for e in res["evaluated"]:
            if not e["admit"]:
                self.assertTrue(e["reasons"], f"{e['node_id']} refused without a reason")

    def test_decision_record_is_replayable_json(self):
        """The shadow decision log is the Phase 1 artifact; it must be data."""
        res = cc.select_placement(snapshot(), POLICY, require_capability=True)
        decision = {
            "schema": "compute_decision.v1",
            "mode": "shadow",
            "chosen_node": res["chosen"]["node_id"] if res["chosen"] else None,
            "reason": res["reason"],
            "evaluated": [{"node_id": e["node_id"], "admit": e["admit"],
                           "verdict": e["verdict"], "reasons": e["reasons"],
                           "score": e["score"]} for e in res["evaluated"]],
        }
        blob = json.dumps(decision, sort_keys=True)
        again = json.loads(blob)
        self.assertEqual(again["chosen_node"], decision["chosen_node"])
        self.assertEqual(len(again["evaluated"]), 4)


if __name__ == "__main__":
    unittest.main()
