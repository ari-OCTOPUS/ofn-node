#!/usr/bin/env python3
"""R-3 drill — DUAL-VETO-DRILL.json (runs ONLY after owner approval + install).

Proves the mutual-veto gate behaves: a money-class action with a SINGLE
approval must be DENIED; the same action with two approvals from two
different approvers passes. Pure fixture — no real actions touched.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def dual_veto_approve(approvals: list[dict], action_class: str = "money") -> tuple:
    """Two DISTINCT approvers required for money-class; else DENY."""
    if action_class != "money":
        return True, "not-money-class"
    ids = {a["approver_id"] for a in approvals if a.get("approved")}
    if len(ids) >= 2:
        return True, "dual-approval-ok"
    return False, "DENY:single-approval" if ids else "DENY:no-approval"


def main() -> int:
    cases = [
        {"case": "single_approval", "approvals": [{"approver_id": "A", "approved": True}],
         "expect": "DENY"},
        {"case": "no_approval", "approvals": [], "expect": "DENY"},
        {"case": "same_approver_twice",
         "approvals": [{"approver_id": "A", "approved": True},
                       {"approver_id": "A", "approved": True}], "expect": "DENY"},
        {"case": "two_distinct_approvers",
         "approvals": [{"approver_id": "A", "approved": True},
                       {"approver_id": "B", "approved": True}], "expect": "ALLOW"},
        {"case": "one_approved_one_refused",
         "approvals": [{"approver_id": "A", "approved": True},
                       {"approver_id": "B", "approved": False}], "expect": "DENY"},
    ]
    results = []
    for c in cases:
        ok, why = dual_veto_approve(c["approvals"])
        got = "ALLOW" if ok else "DENY"
        results.append({"case": c["case"], "expect": c["expect"], "got": got,
                        "verdict": "PASS" if got == c["expect"] else "FAIL", "why": why})
    all_pass = all(r["verdict"] == "PASS" for r in results)
    drill = {
        "schema": "dual-veto-drill/1",
        "id": "DUAL-VETO-DRILL",
        "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "order": "MP-ROOTFIX R-3 (RCA-3), gate for GOV-V8 pre-L2 insurance",
        "cases": results,
        "verdict": "PASS" if all_pass else "FAIL",
        "self_sha256": None,
    }
    body = json.dumps(drill, indent=1, sort_keys=True)
    drill["self_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    out = REPO / "rca" / "DUAL-VETO-DRILL.json"
    out.write_text(json.dumps(drill, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": drill["verdict"],
                      "cases": f"{sum(1 for r in results if r['verdict']=='PASS')}/{len(results)}"}))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
