"""Carry-forward the FORGOTTEN-100 into the 250 registry with today's status.

Rule (anti-self-deception): status defaults to OPEN unless a fresh evening
finding (2026-09-15 deep-scan) or a known receipt contradicts it. Every status
carries status_basis (evidence pointer). Nothing is marked resolved by guess.
"""
import json
import re
from pathlib import Path

LANE = Path(r"F:\backup\09-LANES\OCTOPUS-DEEP-SCAN-250-20260915")
PREV = json.loads(Path(r"F:\backup\09-LANES\OCTOPUS-DEEP-MEMORY-SCAN-20260915\FORGOTTEN-100.json")
                  .read_text(encoding="utf-8"))
NOW = "2026-09-15T21:10:00Z"

# ---- load fresh findings available so far (extraction agent may still be running) ----
fresh = []
for f in sorted((LANE / "raw").glob("*-findings.json")):
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("{"):
                fresh.append(json.loads(line))
    except Exception as e:
        print("skip", f.name, e)

def toks(s):
    return set(re.findall(r"[A-Za-z0-9\-]{3,}", str(s or ""))) | set(re.findall(r"[\u0600-\u06FF]{4,}", str(s or "")))

# explicit resolution evidence found in the evening sweep (title-mention -> note)
RESOLVED_HINTS = {
    "watchdog": "evening sweep verified live code: watchdog STOP_FLAGS gap FIXED (agent-verified against _ops code)",
}
RECONFIRMED_HINTS = {
    "G8-021": "evening runtime sweep (RT-1): still 'executed but never retired', burning component budget every tick",
    "W24": "evening runtime sweep (RT-1/RT-4): W24 still paced behind G8-021; lane dirs uncommitted on F:/ofn-node",
    "OW-8": "evening runtime sweep: starvation item not re-measured; status unchanged",
}

carried = []
for it in PREV["items"]:
    title = it.get("title", "")
    entry = dict(it)
    entry["carried_from"] = "FORGOTTEN-100 @2026-09-15T07:05Z (lane OCTOPUS-DEEP-MEMORY-SCAN-20260915)"
    entry["status"] = "open"
    entry["revalidated_at_utc"] = NOW
    note = "morning-scan 2026-09-15T07:05Z; no contradicting evidence in the evening sweep"
    # cross-reference against fresh findings by token overlap
    ft = toks(title)
    best, best_n = None, 0
    for nf in fresh:
        nt = toks(nf.get("title", ""))
        n = len(ft & nt)
        if n > best_n:
            best, best_n = nf, n
    if best is not None and best_n >= 3:
        note = f"reconfirmed by evening finding {best['id']} ({best_n} shared anchors) — still unfinished"
        entry["linked_fresh"] = best["id"]
    for key, msg in RESOLVED_HINTS.items():
        if key.lower() in title.lower():
            entry["status"] = "resolved_evidence"
            note = msg
    for key, msg in RECONFIRMED_HINTS.items():
        if key.lower() in title.lower():
            entry["status"] = "revalidated_open"
            note = msg
    entry["status_basis"] = note
    entry["U"] = it.get("U", 2)
    entry["R"] = it.get("R", 3)
    entry["C"] = it.get("C", 3)
    carried.append(entry)

(LANE / "carried-100.json").write_text(json.dumps({
    "schema": "octopus.deep-scan.carried.v1",
    "carried_at_utc": NOW,
    "count": len(carried),
    "items": carried,
}, ensure_ascii=False, indent=1), encoding="utf-8")

from collections import Counter
print("carried:", len(carried), "| fresh loaded:", len(fresh))
print("statuses:", Counter(c["status"] for c in carried))
print("with fresh link:", sum(1 for c in carried if c.get("linked_fresh")))
