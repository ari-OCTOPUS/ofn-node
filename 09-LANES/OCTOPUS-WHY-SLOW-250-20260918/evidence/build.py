# -*- coding: utf-8 -*-
"""Build WHY-SLOW-250.json + MATRIX-250.csv from the four authored data batches.
Reads only local authored data; no runtime access. Deterministic."""
import json, csv, importlib.util, sys, os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ENTRIES

BATCHES = ["data_t1_t3", "data_t4_t5", "data_t6_t8", "data_t9_t12"]
DROPS = {"W-130", "W-145", "W-163"}  # weakest/overlapping entries, dropped to hit exact quotas

TERR = {
 "T1": "T1-money-path", "T2": "T2-demand-market", "T3": "T3-offer-product",
 "T4": "T4-owner-dependency", "T5": "T5-governance-friction", "T6": "T6-learning",
 "T7": "T7-agent-architecture", "T8": "T8-knowledge-debt", "T9": "T9-attention-priority",
 "T10": "T10-infra-fleet", "T11": "T11-channels", "T12": "T12-buffer-external",
}
QUOTA = {"T1":35,"T2":30,"T3":20,"T4":30,"T5":20,"T6":15,"T7":20,"T8":20,"T9":15,"T10":25,"T11":10,"T12":10}
VMAP = {"C":"CONFIRMED_BLOCKER","P":"PARTIAL","R":"REFUTED","U":"UNVERIFIED"}

rows = []
seen = set()
for b in BATCHES:
    for e in load(b):
        (eid, tcode, hyp, reason, anchors, verdict, grade, impact, fix, owner_needed, unblock, vts, seeded) = e
        if eid in DROPS:
            continue
        if eid in seen:
            print("DUP ID:", eid); sys.exit(1)
        seen.add(eid)
        rows.append({
            "id": eid, "territory": TERR[tcode], "territory_code": tcode,
            "hypothesis": hyp, "reason": reason,
            "verify_against": [a.strip() for a in anchors.split(" + ") if a.strip()],
            "verdict": VMAP[verdict], "verdict_code": verdict, "grade": grade,
            "impact_1_5": impact, "fixability_1_5": fix,
            "rank_IxF": impact * fix,
            "owner_decision_needed": owner_needed,
            "unblock_2liner": unblock if verdict in ("C","P") else "",
            "verified_this_session": vts, "seeded": seeded,
        })

# ---- validation ----
per = Counter(r["territory_code"] for r in rows)
print("TOTAL:", len(rows))
ok = True
for t in QUOTA:
    n = per.get(t, 0)
    flag = "OK " if n >= QUOTA[t] else "SHORT"
    if n < QUOTA[t]: ok = False
    print(f"  {t:4} {TERR[t]:22} {n:3} / min {QUOTA[t]:3}  {flag}")
print("verdicts:", Counter(r["verdict"] for r in rows).most_common())
print("grades  :", Counter(r["grade"] for r in rows).most_common())
print("seeded  :", sum(1 for r in rows if r["seeded"]), "non-seed:", sum(1 for r in rows if not r["seeded"]))
print("owner-needed:", sum(1 for r in rows if r["owner_decision_needed"]))
print("verified this session:", sum(1 for r in rows if r["verified_this_session"]))
if len(rows) != 250: ok = False; print("TOTAL != 250")

# ---- emit ----
rows_sorted = sorted(rows, key=lambda r: (-r["rank_IxF"], r["territory_code"], r["id"]))
out = {
 "schema": "octopus.why-slow-250.v1",
 "generated_at": "2026-09-18T00:40:00Z",
 "lane": "OCTOPUS-WHY-SLOW-250-20260918",
 "mission": "کشف علت رشد کند اختاپوس — چک‌لیست ۲۵۰ موردی با دلیل",
 "quota_check": {TERR[t]: {"count": per.get(t,0), "min": QUOTA[t], "ok": per.get(t,0) >= QUOTA[t]} for t in QUOTA},
 "total": len(rows),
 "verdict_counts": dict(Counter(r["verdict"] for r in rows)),
 "grade_counts": dict(Counter(r["grade"] for r in rows)),
 "seeds": sum(1 for r in rows if r["seeded"]),
 "non_seeds": sum(1 for r in rows if not r["seeded"]),
 "entries": rows_sorted,
}
with open(os.path.join(HERE, "..", "WHY-SLOW-250.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

with open(os.path.join(HERE, "..", "MATRIX-250.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id","territory","verdict","grade","impact","fixability","rank_IxF","owner_decision_needed","verified_this_session","seeded","hypothesis"])
    for r in rows_sorted:
        w.writerow([r["id"],r["territory"],r["verdict"],r["grade"],r["impact_1_5"],r["fixability_1_5"],r["rank_IxF"],r["owner_decision_needed"],r["verified_this_session"],r["seeded"],r["hypothesis"]])

print("WROTE WHY-SLOW-250.json + MATRIX-250.csv")
sys.exit(0 if ok else 2)
