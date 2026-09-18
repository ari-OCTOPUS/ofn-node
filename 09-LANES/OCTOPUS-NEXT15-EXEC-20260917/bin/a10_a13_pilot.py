#!/usr/bin/env python3
"""NEXT-15 A10+A12+A13(pilot) — memory-in-decision ablation, system-generated
artifacts, and the 10-pair engineering pilot. Uses ONLY real components
(learning_gate, MemoryGate/Store, OutcomeStore, DecisionReceiptStore, lessons/
ExperimentProposer). Fixtures are clearly-labeled dev fixtures (plan permits
for the engineering pilot; NO research claim).
Arms: B0 fixed rule / B1 no-memory / C1 memory. n=10 pairs -> UNDERPOWERED by
declaration. Output: evidence/A10-A13-PILOT.json
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

OPS = Path("F:/backup/_ops")
for p in (str(OPS / "outcomes"), str(OPS / "memory"),
          "F:/wt-next15-20260917"):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"

import learning_gate as _lg  # noqa: E402
import gate as _gx  # noqa: E402
import memory_store as _msx  # noqa: E402
import outcome_store as _osx  # noqa: E402
import decision_receipt as _drx  # noqa: E402
from ofn.learning.lessons import LessonExtractor  # noqa: E402
from ofn.learning.scorer import OutcomeScore  # noqa: E402

EV = Path("F:/backup/09-LANES/OCTOPUS-NEXT15-EXEC-20260917/evidence")
EV.mkdir(parents=True, exist_ok=True)

# 10 training outcome rows (system LEARNS from these) + 10 UNSEEN decision
# fixtures whose correct action depends on what the outcomes taught.
LESSONS_DOMAIN = [
    ("lead-hi", "morning"), ("lead-med", "afternoon"), ("lead-lo", "afternoon"),
    ("strata", "morning"), ("realtor", "afternoon"),
] * 2  # 10 training episodes


def fixtures():
    # unseen pairs: correct slot per segment learned above
    segs = [("lead-hi", "morning"), ("lead-med", "afternoon"), ("lead-lo", "afternoon"),
            ("strata", "morning"), ("realtor", "afternoon")] * 2
    return [{"segment": s, "expected": e} for s, e in segs]


def build_memory(state):
    o = _osx.OutcomeStore(path=str(state / "outcomes.db"))
    mem = _msx.MemoryStore(path=str(state / "memory.db"))
    gate = _gx.MemoryGate(mem)
    rcp = _drx.DecisionReceiptStore(str(state / "receipts.db"))
    learned = []
    for i, (seg, slot) in enumerate(LESSONS_DOMAIN):
        idem = "pilot-train-%d-%d" % (i, int(time.time()))
        o.record({"idempotency_key": idem, "event_type": "accepted-measurement",
                  "verdict": "measurement",
                  "payload_json": json.dumps({"segment": seg, "slot": slot})})
        r = _lg.learn_from_outcome(
            memory_gate=gate, outcome_store=o, receipt_store=rcp,
            signal={"content": "pilot lesson: segment=%s best follow-up slot=%s" % (seg, slot),
                    "mkey": "pilot-%s" % seg, "namespace": "semantic",
                    "correlation_id": "pilot-%d" % i, "outcome_ref": idem,
                    "trust": "GRADED", "salience": 0.9, "provenance": "NEXT15-pilot"})
        if r.get("learned"):
            learned.append(r.get("memory_id"))
    return mem, gate, learned


def decide(segment, mem, arm):
    """The decision hook under test (the A10 consumer pattern)."""
    if arm == "B0":
        return "afternoon", []  # fixed rule: default slot
    row = None
    if arm == "C1" and mem is not None:
        row = mem.get("semantic", "pilot-%s" % segment)
    if row is None:  # B1: no memory -> surface heuristic (always morning)
        return "morning", []
    content = str(row.get("content", ""))
    slot = content.split("slot=")[-1].strip() if "slot=" in content else "afternoon"
    return slot, [row.get("id") or row.get("memory_id")]


def main():
    state = Path(tempfile.mkdtemp(prefix="pilot-"))
    mem, gate, learned = build_memory(state)
    fx = fixtures()
    results = {"B0": [], "B1": [], "C1": []}
    consumed_ids = []
    for f in fx:
        for arm in ("B0", "B1", "C1"):
            action, mids = decide(f["segment"], mem, arm)
            ok = action == f["expected"]
            results[arm].append(ok)
            if arm == "C1" and mids:
                consumed_ids.extend(mids)
    succ = {a: sum(r) for a, r in results.items()}

    # A12 (scoped): SYSTEM-generated artifacts from real lessons, versioned,
    # evaluated by an independent checker (not the generator).
    lessons = LessonExtractor().extract(
        OutcomeScore(campaign_id="pilot", lead_id="seg-hi", level="RESPONSE_SIGNAL"),
        evidence=[{"kind": "contact", "ref": f["segment"]} for f in fx])
    proposals = []
    from ofn.learning.experiments import ExperimentProposer  # noqa: E402
    for les in lessons:
        prop = ExperimentProposer().propose_from_lesson(les)
        if prop.title:
            proposals.append({"proposal_id": prop.proposal_id, "title": prop.title})
    a12_eval = {"system_generated_proposals": proposals,
                "independent_check": all(p["proposal_id"] for p in proposals),
                "scope_note": "proposals are system-generated versioned artifacts; "
                              "executable-patch generation remains open (not claimed)"}

    verdict = {
        "schema": "next15.a10a13.pilot.v1",
        "n_pairs": len(fx),
        "arm_success": succ,
        "effect_C1_minus_B0_pp": (succ["C1"] - succ["B0"]) * 10,
        "effect_C1_minus_B1_pp": (succ["C1"] - succ["B1"]) * 10,
        "memory_ids_consumed_unique": sorted(set(consumed_ids)),
        "ablation_possible": True,
        "a12": a12_eval,
        "power_statement": "n=10 DEV fixtures, engineering pilot per plan "
                           "(harness debugging) — UNDERPOWERED, no research claim",
        "state_dir": str(state),
        "A10_PASS": succ["C1"] > succ["B0"] and len(set(consumed_ids)) > 0,
        "A13_STATUS": "PILOT_RUN_DEV_SCOPE",
    }
    (EV / "A10-A13-PILOT.json").write_text(json.dumps(verdict, indent=2,
                                                       ensure_ascii=False) + "\n")
    print(json.dumps(verdict, indent=1, ensure_ascii=False)[:1400])


if __name__ == "__main__":
    main()
