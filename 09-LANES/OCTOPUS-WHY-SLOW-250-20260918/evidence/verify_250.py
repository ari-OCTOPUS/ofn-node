#!/usr/bin/env python3
"""Verify the WHY-SLOW-250 deliverable: contract compliance + anchor reality."""
import csv
import json
import pathlib
import random
import re

LANE = pathlib.Path("09-LANES/OCTOPUS-WHY-SLOW-250-20260918")
J = LANE / "WHY-SLOW-250.json"
M = LANE / "MATRIX-250.csv"
MD = LANE / "WHY-SLOW-250.md"
TERR = LANE / "territory"

print("== 1. files ==")
for p in (J, M, MD, LANE / "BASELINE-GROWTH-CURVE.md", LANE / "BASELINE-GROWTH-CURVE.json",
          LANE / "CAUSAL-CHAIN.md", LANE / "OWNER-DECISIONS-PENDING.md", LANE / "LANE-REPORT.md"):
    print("  %-28s %s" % (p.name, "OK" if p.exists() else "MISSING"))
print("  territory reports:", len(list(TERR.glob("TERRITORY-REPORT-*.md"))), "/ 12")

print("\n== 2. JSON contract ==")
d = json.loads(J.read_text(encoding="utf-8"))
e = d["entries"]
print("  total:", len(e), "| declared:", d["total"], "| schema:", d["schema"])
ids = [r["id"] for r in e]
print("  unique ids:", len(set(ids)) == len(ids), "| seeds:", sum(1 for r in e if r["seeded"]),
      "| non-seed:", sum(1 for r in e if not r["seeded"]))
REQ = ("id", "territory", "hypothesis", "reason", "verify_against", "verdict", "grade",
       "impact_1_5", "fixability_1_5")
bad = [r["id"] for r in e if any(not r.get(k) for k in REQ)
       and not (r["verdict"] == "REFUTED" and r.get("impact_1_5") == 0)]
print("  entries missing a mandatory field:", len(bad), bad[:5])
VER = {"CONFIRMED_BLOCKER", "PARTIAL", "REFUTED", "UNVERIFIED"}
print("  verdict enum ok:", all(r["verdict"] in VER for r in e))
print("  grade enum ok:", all(re.fullmatch(r"E[0-5]", r["grade"]) for r in e))
print("  unblock present for C/P:",
      all(r["unblock_2liner"] for r in e if r["verdict"] in ("CONFIRMED_BLOCKER", "PARTIAL")))
# quota
per = {}
for r in e:
    per[r["territory_code"]] = per.get(r["territory_code"], 0) + 1
qbad = [t for t, q in d["quota_check"].items() if per.get(t.split("-")[0], 0) < q["min"]]
print("  quotas met:", not qbad, "| per-territory:", sorted(per.items()))

print("\n== 3. CSV / dashboard consistency ==")
rows = list(csv.DictReader(M.open(encoding="utf-8-sig")))
print("  csv rows:", len(rows), "| matches json:", len(rows) == len(e))
md = MD.read_text(encoding="utf-8")
for num in ("۲۵۰", "۷۹", "۶۷", "۱۰۰", "۲۳۵", "۱۰۸", "۵۶"):
    print("   dashboard mentions %s: %s" % (num, num in md))

print("\n== 4. anchor reality check (sample 20) ==")
random.seed(7)
sample = random.sample(e, 20)
exists = miss = remote = 0
missing_list = []
for r in sample:
    for a in r["verify_against"]:
        p = re.split(r"\s*@|\s+::", a)[0].strip()
        p = p.split(" + ")[0].strip()
        if p.startswith(("138:", "repo:", "tests/", "ofn/", "tools/", "state/")):
            remote += 1
            continue
        cand = pathlib.Path(p)
        if cand.exists():
            exists += 1
        else:
            miss += 1
            missing_list.append(p)
print("  local anchors existing: %d | missing: %d | remote/runtime refs: %d" % (exists, miss, remote))
if missing_list:
    print("  MISSING sample:", missing_list[:6])

print("\n== 5. per-entry reason length (contract: a real reason, not a stub) ==")
short = [r["id"] for r in e if len(r["reason"]) < 25]
print("  suspiciously short reasons:", len(short), short[:5])
print("  median reason length:", sorted(len(r["reason"]) for r in e)[len(e) // 2])
