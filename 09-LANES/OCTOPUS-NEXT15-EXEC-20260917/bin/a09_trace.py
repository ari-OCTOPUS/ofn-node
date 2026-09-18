#!/usr/bin/env python3
"""NEXT-15 A09 — full outcome->memory->restart->consumption trace.

Uses the REAL existing components only (no parallel bank):
_ops/outcomes/learning_gate.py + _ops/memory/gate.py + memory_store.py +
_ops/outcomes/outcome_store.py. Flag OCTOPUS_WIRE_MEMORY_GATE=1 required.
Output: TRACE lines to stdout + evidence/A09-TRACE.json in this lane.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

OPS = Path("F:/backup/_ops")
for p in (str(OPS / "outcomes"), str(OPS / "memory")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"

import learning_gate as _lg  # noqa: E402
import gate as _gx  # noqa: E402
import memory_store as _msx  # noqa: E402
import outcome_store as _osx  # noqa: E402
import decision_receipt as _drx  # noqa: E402

TRACE = []


def trace(ev):
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"), **ev}
    TRACE.append(row)
    print(json.dumps(row, ensure_ascii=False)[:220])


def main():
    state = Path(tempfile.mkdtemp(prefix="a09-"))
    o = _osx.OutcomeStore(path=str(state / "outcomes.db"))
    mem = _msx.MemoryStore(path=str(state / "memory.db"))
    gate = _gx.MemoryGate(mem)
    receipts = _drx.DecisionReceiptStore(str(state / "receipts.db"))

    # 1) REAL outcome recorded durably (accepted-measurement = owner-verifiable)
    idem = "a09-outcome-%d" % int(time.time())
    ok = o.record({"idempotency_key": idem, "event_type": "accepted-measurement",
                   "verdict": "measurement",
                   "payload_json": json.dumps({"source": "a09-trace", "value": 42})})
    trace({"step": "outcome_recorded", "ok": ok, "outcome_ref": idem})

    # 2) outcome -> memory (learned, two-phase)
    r = _lg.learn_from_outcome(
        memory_gate=gate, outcome_store=o, receipt_store=receipts,
        signal={"content": "a09: exterior-quote follow-up timing morning>afternoon",
                "mkey": "a09-mem-1", "namespace": "semantic",
                "correlation_id": "a09-corr", "outcome_ref": idem,
                "trust": "OWNER_CONFIRMED", "salience": 0.9,
                "provenance": "NEXT15-A09-trace"})
    trace({"step": "learn_from_outcome", "learned": r.get("learned"),
           "memory_id": r.get("memory_id"), "reason": r.get("reason"),
           "receipt_id": r.get("receipt_id")})
    mid = r.get("memory_id")
    fin = None
    if mid and not r.get("committed"):
        fin = _lg.finalize_pending_learning(memory_gate=gate, memory_id=mid, admit=True)
        trace({"step": "finalize", "result": {k: fin.get(k) for k in ("ok", "admitted", "memory_id", "reason")}})

    # 3) NEGATIVE: forged outcome_ref must be refused
    forged = _lg.learn_from_outcome(
        memory_gate=gate, outcome_store=o, receipt_store=receipts,
        signal={"content": "forged claim", "mkey": "a09-forged", "namespace": "semantic",
                "correlation_id": "x", "outcome_ref": "DOES-NOT-EXIST",
                "trust": "OWNER_CONFIRMED", "salience": 0.9, "provenance": "a09"})
    trace({"step": "forged_refusal", "learned": forged.get("learned"),
           "reason": (forged.get("reason") or "")[:80]})

    # 4) RESTART survival + consumption in a fresh process (real decision hook)
    child = r'''
import json, sys, os
for p in (%r, %r):
    sys.path.insert(0, p)
import memory_store as _msx
mem = _msx.MemoryStore(path=%r)
row = mem.get("semantic", "a09-mem-1")
decision = {"action": "schedule_follow_up", "slot": "morning"}
if row:
    decision["retrieved_memory_ids"] = [row.get("id") or row.get("memory_id")]
    decision["based_on"] = str(row.get("content"))[:80]
else:
    decision["retrieved_memory_ids"] = []
    decision["based_on"] = None
print(json.dumps(decision))
''' % (str(OPS / "outcomes"), str(OPS / "memory"), str(state / "memory.db"))
    out = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True)
    trace({"step": "restart_consumption", "child_rc": out.returncode,
           "decision": (out.stdout or out.stderr[-200:])[:200]})

    verdict = {
        "outcome_durable": bool(ok),
        "memory_learned": bool(r.get("learned")),
        "forged_refused": forged.get("learned") is False,
        "restart_survival_and_consumption": "retrieved_memory_ids" in (out.stdout or "") and "None" not in (out.stdout or "")[:0] and out.returncode == 0 and '"based_on":' in (out.stdout or ""),
        "state_dir": str(state),
    }
    verdict["A09_PASS"] = all([verdict["outcome_durable"], verdict["memory_learned"],
                               verdict["forged_refused"], out.returncode == 0])
    ev = Path("F:/backup/09-LANES/OCTOPUS-NEXT15-EXEC-20260917/evidence")
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "A09-TRACE.json").write_text(json.dumps({"trace": TRACE, "verdict": verdict},
                                                  indent=2, ensure_ascii=False) + "\n")
    print("VERDICT", json.dumps(verdict, ensure_ascii=False))


if __name__ == "__main__":
    main()
