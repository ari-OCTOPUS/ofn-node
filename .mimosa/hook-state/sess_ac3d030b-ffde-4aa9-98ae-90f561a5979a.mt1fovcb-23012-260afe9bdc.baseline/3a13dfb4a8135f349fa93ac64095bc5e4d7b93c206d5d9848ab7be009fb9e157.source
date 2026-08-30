#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ERRORHUNT pass-2: precise counts (read-only). Prints JSON summary to stdout."""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

VAULT = Path(r"F:\backup")
CUTOFF = "2026-08-09"
FIX_TS = "2026-08-16T05:00"


def lines(p: Path):
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            yield line.rstrip("\n")


out = {}

# --- sqlite dashboard_events ---
db = VAULT / "4d_system" / "outputs" / "4d_experiments.db"
con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
con.execute("PRAGMA query_only=ON")
rb = con.execute(
    """SELECT
         SUM(CASE WHEN timestamp < ? THEN 1 ELSE 0 END),
         SUM(CASE WHEN timestamp < ? AND status!='ok' THEN 1 ELSE 0 END),
         SUM(CASE WHEN timestamp >= ? THEN 1 ELSE 0 END),
         SUM(CASE WHEN timestamp >= ? AND status='ok' THEN 1 ELSE 0 END),
         SUM(CASE WHEN timestamp >= ? AND status!='ok' THEN 1 ELSE 0 END)
       FROM dashboard_events
       WHERE event_name='memory.readback' AND timestamp >= ?""",
    (FIX_TS, FIX_TS, FIX_TS, FIX_TS, FIX_TS, CUTOFF),
).fetchone()
out["readback"] = {
    "pre_fix_n": rb[0], "pre_fix_fail": rb[1],
    "post_fix_n": rb[2], "post_fix_ok": rb[3], "post_fix_fail": rb[4],
}
err_status = con.execute(
    """SELECT event_name, status, COUNT(*)
       FROM dashboard_events
       WHERE timestamp >= ? AND lower(coalesce(status,'')) IN
             ('error','fail','failed','blocked','warning')
       GROUP BY 1,2 ORDER BY 3 DESC LIMIT 30""",
    (CUTOFF,),
).fetchall()
out["dash_errorish"] = [{"event": a, "status": b, "n": c} for a, b, c in err_status]
hyp = con.execute("SELECT status, COUNT(*) FROM hypotheses GROUP BY 1").fetchall()
out["hyp_status"] = [{"status": s, "n": n} for s, n in hyp]
con.close()

# --- watchdog precise ---
wd = VAULT / "_ops" / "state" / "watchdog-log.txt"
c = Counter()
first_last = {}
for line in lines(wd):
    if not line.startswith("2026-08-") or line < CUTOFF:
        continue
    if "STOP-CORTEX" in line:
        k = "stop-cortex"
    elif "REVIVE" in line and "no revive" not in line.lower():
        k = "revive"
    elif "dead (miss" in line:
        k = "dead-miss"
    elif "launched RUN-CORTEX" in line:
        k = "launch"
    elif "HALT-ALL" in line or "architect-STOP" in line:
        k = "halt"
    elif "alive on" in line:
        k = "alive"
        c[k] += 1
        continue
    else:
        continue
    c[k] += 1
    ts = line[:19]
    fl = first_last.setdefault(k, [ts, ts])
    fl[1] = ts
    if ts < fl[0]:
        fl[0] = ts
out["cortex_watchdog"] = {"counts": dict(c), "span": first_last}

# last 24h (from 2026-08-15T11:00 local)
c24 = Counter()
for line in lines(wd):
    if line < "2026-08-15T11:00":
        continue
    if "STOP-CORTEX" in line:
        c24["stop-cortex"] += 1
    elif "REVIVE" in line and "no revive" not in line.lower():
        c24["revive"] += 1
    elif "dead (miss" in line:
        c24["dead-miss"] += 1
out["cortex_last_24h"] = dict(c24)

# --- governor subtypes ---
gov = VAULT / "_ops" / "governor" / "governor-alerts.md"
cur_ts = ""
sub = Counter()
span = {}
buf_alert = False
for line in lines(gov):
    m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", line)
    if m:
        cur_ts = m.group(1)
        continue
    if not cur_ts or cur_ts < CUTOFF:
        continue
    if "circuit OPEN" in line and "orchestr" in line:
        k = "circuit-open-orchestr-429" if "429" in line else "circuit-open-orchestr-other"
    elif "circuit OPEN" in line:
        k = "circuit-open-other"
    elif "circuit RECOVERED" in line:
        k = "circuit-recovered"
    elif "closed با opened_at" in line or "شکلِ ریست" in line:
        k = "circuit-reset-shape"
    elif "price_in/price_out" in line:
        k = "budget-price-unlocked"
    elif "KeyError: 'text'" in line:
        k = "debate-keyerror-text"
    elif "RefuseToSend" in line or "ZAI_API_KEY" in line:
        k = "zai-key-missing"
    elif "neural_stack is None" in line:
        k = "consolidation-wire-off"
    elif "⚠️" in line or "error" in line.lower() or "fail" in line.lower():
        k = "governor-other"
    else:
        continue
    sub[k] += 1
    sp = span.setdefault(k, [cur_ts, cur_ts])
    sp[1] = cur_ts
out["governor_sub"] = {"counts": dict(sub), "span": span}

# --- paid timeout ---
pt = Counter()
pt_span = {}
p = VAULT / "_ops" / "state" / "paid-timeout-alerts.jsonl"
for line in lines(p):
    if not line.strip():
        continue
    o = json.loads(line)
    ts = o.get("ts", "")
    if ts < CUTOFF:
        continue
    role = o.get("role", "?")
    pt[role] += 1
    sp = pt_span.setdefault(role, [ts, ts])
    sp[1] = ts
out["paid_timeout"] = {"by_role": dict(pt), "span": pt_span}

# --- organ denied ---
od = []
p = VAULT / "_ops" / "budget" / "organ-gate-log.jsonl"
for line in lines(p):
    if not line.strip():
        continue
    o = json.loads(line)
    ts = o.get("ts", "")
    if ts < CUTOFF:
        continue
    if o.get("allow") is False or o.get("ok") is False:
        od.append({"ts": ts, "organ": o.get("organ"), "task": o.get("task"),
                   "why": str(o.get("reason") or o.get("why") or o.get("deny") or "")[:80]})
out["organ_denied"] = {"n": len(od), "rows": od[:20],
                       "by_organ": dict(Counter(x["organ"] for x in od)),
                       "by_task": dict(Counter(x["task"] for x in od))}

# --- center hung / miniapp ---
hung = []
for line in lines(VAULT / "_ops" / "state" / "tg-center-watchdog-log.txt"):
    if "HUNG" in line and line[:10] >= CUTOFF:
        hung.append(line)
out["center_hung"] = hung
tun = []
for line in lines(VAULT / "_ops" / "state" / "miniapp-watchdog-log.txt"):
    if "alive=False" in line and "2026-08-0" in line[:10] or (
        "alive=False" in line and line[:10] >= CUTOFF
    ):
        if line[:10] >= CUTOFF:
            tun.append(line)
out["tunnel_restarts"] = {"n": len(tun), "first": tun[0] if tun else "",
                          "last": tun[-1] if tun else ""}

# --- pep ---
pep = []
pp = VAULT / "_ops" / "state" / "telegram-pep-shadow.jsonl"
if pp.exists():
    for line in lines(pp):
        if line.strip():
            pep.append(json.loads(line))
out["pep"] = {"n": len(pep), "verdicts": dict(Counter(
    str(x.get("verdict") or x.get("decision") or x.get("action")) for x in pep))}

print(json.dumps(out, ensure_ascii=False, indent=2))
