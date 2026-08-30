#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""record_merge.py — durable record that the first self-improvement cycle reached master.

Appends to the research-journal (restart-safe), the research ledger, and writes a
DecisionReceipt for the OWNER-APPROVED merge. Sandboxed: env points at
governed_state_final; never touches live organism state.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
_WT = _HERE.parent.parent
_SBX = _HERE / "governed_state_final"
_STATE = _SBX / "_ops" / "state"

os.environ["ORG_ROOT"] = str(_SBX)
os.environ["OPS_DIR"] = str(_SBX / "_ops")
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE)
os.environ["GENOME_DIR"] = str(_SBX / "genome")

for _p in (str(_WT / "_ops"), str(_WT / "_ops" / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import decision_receipt as dr  # noqa: E402

MASTER_SHA = sys.argv[1] if len(sys.argv) > 1 else "d56597c"
PREV_SHA = sys.argv[2] if len(sys.argv) > 2 else "a1c3ff6"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
CID = "rc_19b8baf45b437f94"

rec = {
    "run_id": f"research-{CID}", "step": "merge", "status": "ok", "ts": NOW,
    "event": "first self-improvement cycle merged to trunk",
    "master_before": PREV_SHA, "master_after": MASTER_SHA,
    "rollback_ref": "backup/pre-c6-merge",
    "change": "_ops/memory/memory_store.py search(): N+1 -> batched IN() hydration (+15/-3)",
    "evidence": {"roundtrips": "21->2 (10.5x)", "latency_n5000": "~24% faster (bias-controlled)",
                 "correctness": "byte-identical, ~5160 checks, 0 mismatches",
                 "suite": "2232 pass / 3 fail — 3 fails PRE-EXISTING, identical on clean baseline"},
    "authorization": "owner-approved in chat (Approve card -> explicit 'Merge کن')",
    "live_execution_status": ("trunk(master) UPDATED; live working tree F:/backup is on branch "
                              "claude/c7-continuity and does NOT yet execute this code"),
}

jp = _STATE / "journal" / "research-journal.jsonl"
jp.parent.mkdir(parents=True, exist_ok=True)
with open(jp, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

lp = _STATE / "research" / "ledger.jsonl"
with open(lp, "a", encoding="utf-8") as f:
    f.write(json.dumps({
        "contract_id": CID, "verdict": "merged-to-trunk", "ts": NOW,
        "reason": f"owner-approved merge {PREV_SHA}..{MASTER_SHA}; zero regression",
        "live_execution_pending": True}, ensure_ascii=False, sort_keys=True) + "\n")

rp = _STATE / "receipts" / "rec.db"
store = dr.DecisionReceiptStore(rp)
try:
    rid = store.record({
        "receipt_id": "dr_merge_" + MASTER_SHA[:10],
        "trace_id": CID, "mission_id": "research", "effect_class": "E0",
        "objective": "merge owner-approved batched-hydration recall optimization into trunk",
        "alternatives": ["merge", "hold on branch"], "selected_alternative": "merge",
        "reason_codes": ["OWNER_APPROVED", "ZERO_REGRESSION", "FAST_FORWARD", "ROLLBACK_REF_KEPT"],
        "assumptions": ["3 suite failures are pre-existing (verified identical on clean baseline)",
                        "live tree on c7-continuity does not execute trunk code yet"],
        "memories_used": [], "predicted_outcome": {"recall_speedup_frac": 0.235}})
finally:
    store.close()

print("recorded merge:")
print("  research-journal:", jp, f"({len(jp.read_text('utf-8').splitlines())} lines)")
print("  research ledger :", lp, f"({len(lp.read_text('utf-8').splitlines())} lines)")
print("  decision receipt:", rid)
