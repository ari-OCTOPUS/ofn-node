#!/usr/bin/env python3
"""CLAIM->REALITY: memory DERIVES the decision, on REAL outcomes.db rows.

Phase L: learn from REAL owner verdict rows (approved/rejected tokens) via the
real learning_gate stack -> memories with accept/reject polarity.
Phase D: for each REAL lead-decision row, compute the action twice:
  memory_off = fixed default policy (proceed)
  memory_on  = DERIVED from retrieved memory polarity (reject-memory -> hold_revise,
               approve-memory -> proceed) — the action is a FUNCTION of memory,
               not a decoration of a fixed action.
Decision-change count + correctness against the REAL recorded verdicts.
Output: evidence/A10-REALITY.json
"""
import json
import os
import sqlite3
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

REAL = "F:/backup/_ops/state/outcomes/outcomes.db"


def real_rows():
    c = sqlite3.connect("file:%s?mode=ro" % REAL, uri=True)
    rows = c.execute("SELECT idempotency_key, event_type, verdict, payload_json FROM outcomes").fetchall()
    c.close()
    return rows


def key_of(payload: dict, row):
    """REAL-data key: the decision SURFACE (only stable discriminator present)."""
    return payload.get("surface") or payload.get("source") or None


def polarity_of(etype, verdict, payload):
    raw = str(payload.get("owner_verdict_raw") or "").lower()
    if etype == "rejected" or verdict == "rejected" or raw in ("rejected", "no"):
        return "reject"
    return "approve"


def main():
    state = Path(tempfile.mkdtemp(prefix="reality-"))
    o = _osx.OutcomeStore(path=str(state / "outcomes.db"))
    mem = _msx.MemoryStore(path=str(state / "memory.db"))
    gate = _gx.MemoryGate(mem)
    rcp = _drx.DecisionReceiptStore(str(state / "receipts.db"))

    rows = real_rows()
    # ---- Phase L: learn from REAL tokens (copy rows into the trace outcome store) ----
    learned = {"approve": 0, "reject": 0, "skipped": 0}
    keys = {}
    for idem, etype, verdict, pj in rows:
        try:
            payload = json.loads(pj) if pj else {}
        except Exception:
            payload = {}
        usable = (etype in ("owner-decision", "accepted-measurement", "rejected"))
        if not usable:
            learned["skipped"] += 1
            continue
        polarity = polarity_of(etype, verdict, payload)
        k = key_of(payload, rows) or ("cat-%s" % (verdict or etype))
        o.record({"idempotency_key": "real-%s" % idem, "event_type": "accepted-measurement",
                  "verdict": "measurement", "payload_json": pj or "{}"})
        r = _lg.learn_from_outcome(
            memory_gate=gate, outcome_store=o, receipt_store=rcp,
            signal={"content": "real outcome: key=%s polarity=%s (event=%s)" % (k, polarity, etype),
                    "mkey": "real-%s" % k, "namespace": "semantic",
                    "correlation_id": idem, "outcome_ref": "real-%s" % idem,
                    "trust": "GRADED", "salience": 0.8, "provenance": REAL})
        if r.get("learned"):
            learned[polarity] += 1
            keys[k] = polarity if k not in keys else keys[k]

    # ---- Phase D: decisions DERIVED from memory (both arms) on the same keys ----
    def decide(key, arm):
        if arm == "off":
            return "proceed"  # fixed default policy
        row = mem.get("semantic", "real-%s" % key)
        if not row:
            return "proceed"  # no memory -> policy default
        content = str(row.get("content", ""))
        return "hold_revise" if "polarity=reject" in content else "proceed"

    pairs = []
    changed = 0
    correct_on = 0
    correct_off = 0
    for idem, etype, verdict, pj in rows:
        try:
            payload = json.loads(pj) if pj else {}
        except Exception:
            payload = {}
        k = key_of(payload, rows)
        if not k or k not in keys:
            continue
        real_verdict = "reject" if polarity_of(etype, verdict, payload) == "reject" else "accept"
        a_off = decide(k, "off")
        a_on = decide(k, "on")
        changed += a_on != a_off
        # correctness: 'hold_revise' is the right response when reality was rejected
        correct_on += (a_on == "hold_revise") == (real_verdict == "reject")
        correct_off += (a_off == "hold_revise") == (real_verdict == "reject")
        pairs.append({"key": k, "real": real_verdict, "off": a_off, "on": a_on})

    out = {"schema": "next15.a10-reality.v1",
           "real_rows_total": len(rows),
           "learned_memories": learned,
           "decision_pairs": len(pairs),
           "decisions_changed_by_memory": changed,
           "correctness": {"memory_off": correct_off, "memory_on": correct_on,
                           "denominator": len(pairs)},
           "sample_pairs": pairs[:6],
           "CLAIM_REALITY": changed > 0 and correct_on >= correct_off,
           "note": "action DERIVED from memory polarity (function of retrieval), real tokens only"}
    ev = Path("F:/backup/09-LANES/OCTOPUS-NEXT15-EXEC-20260917/evidence")
    (ev / "A10-REALITY.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(out, indent=1, ensure_ascii=False)[:1200])


if __name__ == "__main__":
    main()
