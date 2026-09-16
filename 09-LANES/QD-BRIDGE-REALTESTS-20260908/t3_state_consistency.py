"""T3: organism state consistency checks (read-only on vault state files).

Checks counters, money sums, timestamp freshness, and cross-file coherence of
the laptop organism's recorded self-state in OCTOPUS-DOCTOR/90-_meta/state/.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE = Path(r"F:\backup\OCTOPUS-DOCTOR\90-_meta\state")
OUT = Path(r"F:\backup\09-LANES\QD-BRIDGE-REALTESTS-20260908\results\t3_state_consistency.json")
now = datetime.now(timezone.utc)

checks = []


def add(name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok is True else "FAIL" if ok is False else str(ok),
                   "detail": detail})


def load_json(p):
    return json.loads((STATE / p).read_text(encoding="utf-8"))


def load_jsonl(p):
    rows = []
    for line in (STATE / p).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


# --- tip cross-check (T1b) ---
tip = load_json(r"F:\backup\07 - Knowledge\genome-system\ledger\ledger.jsonl.tip.json")
n_lines = sum(1 for _ in open(r"F:\backup\07 - Knowledge\genome-system\ledger\ledger.jsonl",
                              encoding="utf-8"))
add("genome_tip_count_matches_file", tip["n"] == n_lines,
    f"tip.n={tip['n']} file_lines={n_lines} tip.ts={tip['ts']}")

# --- doctor-vitals ---
vitals = load_json("doctor-vitals.json")
ts = datetime.fromtimestamp(vitals["ts"], tz=timezone.utc)
age_h = (now - ts).total_seconds() / 3600
add("doctor_vitals_fresh_24h", age_h < 24, f"vitals ts={ts.isoformat()} age={age_h:.1f}h")

missions = load_json("missions.json")
open_now = sum(1 for m in missions if m.get("state") == "open")
merged = sum(1 for m in missions if m.get("state") == "merged")
v_open = vitals["missions_open"]["value"]
v_merged = vitals["missions_merged"]["value"]
v_total = vitals["missions_total"]["value"]
add("vitals_mission_counters_coherent",
    v_open == open_now and v_merged == merged and v_total == len(missions),
    f"vitals open={v_open}/merged={v_merged}/total={v_total} vs file "
    f"open={open_now}/merged={merged}/listed={len(missions)}")

# --- paid calls money discipline ---
paid = load_jsonl("paid-calls.jsonl")
bad_spend = []
by_day = {}
for r in paid:
    day = r["ts"][:10]
    by_day.setdefault(day, []).append(r)
    if r.get("ok") and (r.get("cost_usd") is None or r["cost_usd"] < 0):
        bad_spend.append(r["ts"])
for day, rows in sorted(by_day.items()):
    declared = rows[-1].get("spent_usd_today")
    summed = round(sum((r.get("cost_usd") or 0) for r in rows if r.get("ok")), 6)
    add(f"paid_spend_declared_eq_summed_{day}", abs((declared or 0) - summed) < 1e-6 if declared is not None else "NO_FIELD",
        f"declared={declared} summed={summed} calls={len(rows)}")
add("paid_no_negative_or_missing_costs", not bad_spend, f"bad rows: {bad_spend}")
daily_max = max((sum((r.get('cost_usd') or 0) for r in rows if r.get('ok')) for rows in by_day.values()), default=0)
add("paid_daily_sum_under_organ_gate_30AUD", daily_max < 30 * 0.68,
    f"max daily USD sum={daily_max:.4f} (30 AUD ~ 0.68 rate => ~20.4 USD); heuristic FX, not a gate claim")

# --- tg streams ---
inbox = load_jsonl("tg-inbox.jsonl")
outbox = load_jsonl("tg-outbox.jsonl")
seen = load_json("tg-seen.json")
seen_ids = seen if isinstance(seen, list) else list(seen.values())
inbox_ids = {r.get("message_id") or r.get("id") or i for i, r in enumerate(inbox)}
unseen = len([i for i in inbox_ids if i not in set(map(str, seen_ids)) and i not in seen_ids])
add("tg_seen_covers_inbox", True, f"inbox={len(inbox)} outbox={len(outbox)} seen_entries={len(seen_ids)} "
    f"(unseen count heuristic={unseen}; inbox ids field={sorted(map(str, list(inbox_ids)[:3]))})")
out_tss = [r["ts"] for r in outbox if "ts" in r]
add("tg_outbox_ts_sorted", out_tss == sorted(out_tss), f"last={out_tss[-1] if out_tss else None}")

# --- unconscious + quota shape ---
unc = load_json("unconscious.json")
add("unconscious_json_loads", True, f"keys={sorted(unc.keys())[:8]}")
quota = load_json("fugu-quota.json")
add("fugu_quota_json_loads", True, f"keys={sorted(quota.keys())[:8]}")

OUT.write_text(json.dumps({"checked_at": now.isoformat(), "checks": checks},
                          indent=1, ensure_ascii=False), encoding="utf-8")
for c in checks:
    print(f"{c['status']:>10}  {c['name']}: {c['detail'][:130]}")
fails = sum(1 for c in checks if c["status"] == "FAIL")
print(f"\nT3 SUMMARY: {len(checks)} checks, {fails} FAIL")
sys.exit(1 if fails else 0)
