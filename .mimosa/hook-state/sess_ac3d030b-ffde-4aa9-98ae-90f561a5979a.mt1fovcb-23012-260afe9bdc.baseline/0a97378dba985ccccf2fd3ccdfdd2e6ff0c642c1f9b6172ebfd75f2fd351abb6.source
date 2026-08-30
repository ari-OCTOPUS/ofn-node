#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_e2e_gate.py — گیتِ E2E که Core کم داشت (audit E14) — پورتِ اثبات‌شدهٔ TEAM-C جزیره.
گیت ۴تایی: valid_pairs_increment=4 · baseline_failure=0 · judge_unreadable=0 ·
شناسهٔ یکتا · رسید کامل. Run: python -X utf8 test_e2e_gate.py"""
import sys
from pathlib import Path


def gate_e2e(records):
    g = {"pass": True, "n": len(records), "valid": 0, "baseline_failure": 0,
         "judge_unreadable": 0, "duplicate_ids": 0, "receipt_incomplete": 0}
    ids = set()
    for r in records:
        if r.get("pair_id") in ids:
            g["duplicate_ids"] += 1
        ids.add(r.get("pair_id"))
        rec = r.get("receipt") or {}
        if not (rec.get("status") == "COMPLETE" and rec.get("trace_id")):
            g["receipt_incomplete"] += 1
        if r.get("void"):
            why = str(r.get("why", ""))
            if "judge" in why:
                g["judge_unreadable"] += 1
            elif "base" in why:
                g["baseline_failure"] += 1
        else:
            g["valid"] += 1
    g["pass"] = (g["n"] == 4 and g["valid"] == 4 and g["baseline_failure"] == 0
                 and g["judge_unreadable"] == 0 and g["duplicate_ids"] == 0
                 and g["receipt_incomplete"] == 0)
    return g


def _mk(pid, void=False, why="", won=True, receipt_ok=True):
    return {"pair_id": pid, "batch": 9, "void": void, "why": why, "cond_won": won,
            "receipt": {"status": "COMPLETE" if receipt_ok else "PARTIAL",
                        "trace_id": "t-" + pid},
            "judge": {"verdict": "A"}}


if __name__ == "__main__":
    F = []

    def check(n, c):
        print(("PASS " if c else "FAIL ") + n)
        if not c:
            F.append(n)

    check("4 clean -> PASS", gate_e2e([_mk("p" + str(i)) for i in range(4)])["pass"] is True)
    check("1 judge-void -> FAIL",
          gate_e2e([_mk("p1"), _mk("p2"), _mk("p3"),
                    _mk("p4", void=True, why="judge")])["pass"] is False)
    check("baseline void -> FAIL",
          gate_e2e([_mk("p1"), _mk("p2"), _mk("p3"),
                    _mk("p4", void=True, why="base arm failure")])["pass"] is False)
    check("duplicate id -> FAIL",
          gate_e2e([_mk("p1"), _mk("p1"), _mk("p3"), _mk("p4")])["pass"] is False)
    check("receipt incomplete -> FAIL",
          gate_e2e([_mk("p1", receipt_ok=False), _mk("p2"), _mk("p3"),
                    _mk("p4")])["pass"] is False)
    print("ALL PASS" if not F else "FAILURES: " + str(F))
    sys.exit(1 if F else 0)
