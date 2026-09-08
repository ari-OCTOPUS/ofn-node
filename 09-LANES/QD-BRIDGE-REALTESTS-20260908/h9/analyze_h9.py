"""OQD-H9 analyzer — reads three-role receipts, splits arms, applies preregistered rules.

Prereg: 09-LANES/QD-BRIDGE-REALTESTS-20260908/h9/study_h9.json (sha256 4938d82e...)
Rules: verdict evaluated only when >=30 runs per arm OR at 2026-09-22T23:59Z.
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

RECEIPTS = Path(r"F:\backup\09-LANES\MP-CAPABILITY-GAP-01-20260907\evidence\three-role-receipts.jsonl")
OUT = Path(r"F:\backup\09-LANES\QD-BRIDGE-REALTESTS-20260908\h9\h9_status.json")
DEADLINE = "2026-09-22T23:59Z"
MIN_N = 30

rows = [json.loads(l) for l in RECEIPTS.read_text(encoding="utf-8").splitlines() if l.strip()]
pre = [r for r in rows if "h9" not in r]
post = [r for r in rows if "h9" in r]
arms = {a: [r for r in post if r["h9"].get("arm") == a] for a in ("T", "R")}


def stats(rs):
    n = len(rs)
    if not n:
        return {"n": 0}
    pv = [bool(r.get("director_pick", {}).get("pick_valid")) for r in rs]
    fc = [r.get("director_final", {}).get("final_call") for r in rs]
    decisive = sum(1 for x in fc if x in ("yes", "no"))
    brain_ok = [bool(r.get("director_pick", {}).get("brain", {}).get("ok")) for r in rs]
    seeded = [bool(r["h9"].get("seeded")) for r in rs]
    return {"n": n,
            "decisiveness": round(decisive / n, 4),
            "pick_valid": round(sum(pv) / n, 4),
            "brain_ok": round(sum(brain_ok) / n, 4),
            "final_call_dist": dict(Counter(fc)),
            "t_actually_seeded": sum(seeded),
            "mission_mix": dict(Counter(r.get("executor", {}).get("mission") for r in rs)),
            "mean_duration_ms": round(sum(r.get("duration_ms", 0) for r in rs) / n)}


st = {a: stats(v) for a, v in arms.items()}
verdict = "PENDING_CONTINUE"
detail = ""
if st["T"]["n"] >= MIN_N and st["R"]["n"] >= MIN_N:
    d_t, d_r = st["T"]["decisiveness"], st["R"]["decisiveness"]
    guard = st["T"]["pick_valid"] >= 0.7
    if d_t >= d_r + 0.10 and guard:
        verdict = "SUPPORTED_IN_THIS_LAB"
    elif d_t < d_r - 0.10:
        verdict = "REJECTED_BY_THRESHOLD (kill: archive_consumption_harmful_for_this_loop)"
    elif d_t <= d_r:
        verdict = "REJECTED_BY_THRESHOLD"
    else:
        verdict = "UNKNOWN (guard failed or between bands)"
    detail = f"T={d_t} R={d_r} guard_pick_valid_T={st['T']['pick_valid']}"

record = {"checked_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "prereg_sha256_16": "4938d82e740ef6ce",
          "runs_pre_intervention": len(pre),
          "runs_post_wiring": len(post),
          "arms": st,
          "verdict": verdict, "verdict_detail": detail,
          "window_rule": f"n>={MIN_N}/arm or {DEADLINE}"}
OUT.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(record, ensure_ascii=False, indent=1))
sys.exit(0)
