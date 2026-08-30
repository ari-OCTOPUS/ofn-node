#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_self_loop_ingest.py — self-awareness/heal/auto-improve durable ingest."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "memory"),
           str(_HERE.parent / "outcomes"), str(_HERE.parent / "budget"),
           str(_HERE.parent / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
harness.setup("self-loop-ingest")

import self_loop_ingest as sli  # noqa: E402
import memory_store as ms  # noqa: E402


def t_improve_and_part_loops_trail():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        state = Path(td) / "state"
        state.mkdir(parents=True)
        os.environ["OCTOPUS_STATE_DIR"] = str(state)
        os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
        imp = sli.ingest_improve({
            "ts": "2026-08-11T00:00:00Z",
            "top": [{
                "id": "up-1", "title": "fix observability",
                "suggested_action": "restart limb", "source": "smallest_fix",
            }],
            "brain_note": "do observability first",
        }, root=state)
        assert imp["ok"] and imp["n_items"] >= 1 and imp["may_authorize"] is False
        assert imp["committed"] >= 1, imp
        pl = sli.ingest_part_loops({
            "ts": "2026-08-11T00:00:00Z",
            "proposals": [{"part": "قلب", "title": "period tune", "action": "lower period"}],
            "parts": [{"id": "heart", "name": "قلب", "status": "🟡", "detail": "slow"}],
        }, root=state)
        assert pl["ok"] and pl["n_items"] >= 2
        trail = Path(imp["trail"])
        assert trail.exists()
        hits = sli.recall_recent("observability", k=5, root=state)
        assert hits and hits[0]["may_authorize"] is False
        st = ms.MemoryStore()
        try:
            row = st.get("episodic", hits[0]["mkey"]) if hits[0].get("mkey") else None
            assert row or hits[0]["provenance"] in ("memory_store", "self-loop-ingest.jsonl")
        finally:
            st.close()


def t_self_knowledge_and_selfheal_gate_off_still_trails():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        state = Path(td) / "state"
        state.mkdir(parents=True)
        os.environ["OCTOPUS_STATE_DIR"] = str(state)
        os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "0"
        sk = sli.ingest_self_knowledge({
            "ts": "2026-08-11T00:00:00Z",
            "deep_dive": {"smallest_fix": "wire ingest into improve"},
            "understanding": {
                "anatomy": "doctor deep dive loop",
                "pathology": [{"root_cause": "overwrite pulse", "symptom": "lost fix"}],
                "prescription": [{"action": "ingest", "why": "durable"}],
            },
        }, root=state)
        assert sk["ok"] and sk["committed"] == 0 and sk["n_items"] >= 2
        sh = sli.ingest_selfheal_event({
            "leg": "lead-naghshi", "reason": "phi-timeout:no-ack", "phi": 17.2, "beat": 9,
        }, root=state)
        assert sh["ok"] and sh["n_items"] == 1
        hits = sli.recall_recent("overwrite", k=5, root=state)
        assert any("overwrite" in (h.get("content") or "").lower()
                   or "pathology" in (h.get("content") or "").lower() for h in hits)


def t_synthesis_channel():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        state = Path(td) / "state"
        state.mkdir(parents=True)
        os.environ["OCTOPUS_STATE_DIR"] = str(state)
        os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "0"
        r = sli.ingest_synthesis({
            "ts": "t", "tier": "local",
            "proposals": [{"title": "add memory bridge", "why": "stop orphan digests",
                           "first_step": "hook run_and_persist"}],
        }, root=state)
        assert r["ok"] and r["n_items"] == 1 and r["may_authorize"] is False


def run():
    t_improve_and_part_loops_trail()
    t_self_knowledge_and_selfheal_gate_off_still_trails()
    t_synthesis_channel()
    print("PASS self_loop_ingest")


if __name__ == "__main__":
    run()
