#!/usr/bin/env python3
"""S1-PARALLEL-ATTACK-V1 / L-C step 2 — OCT-SENSE-099 divergence timeline.

Read-only. Scans the journal for 099 health events, inspects every retained
snapshot's stored 099 status vs journal-derived status at that snapshot's seq,
and reports the first snapshot where live-lineage and journal replay disagree.
"""
import json
from pathlib import Path

J = Path("/var/lib/octopus/state/events.jsonl")
SNAPDIR = Path("/var/lib/octopus/state/snapshots")

ev = []
with J.open(encoding="utf-8") as fh:
    for line in fh:
        if "OCT-SENSE-099" not in line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("kind") == "health" and r.get("sensor_id") == "OCT-SENSE-099":
            ev.append(r)

print("health_events_099:", len(ev))
if ev:
    print("first:", json.dumps(ev[0])[:220])
    print("last3:", json.dumps(ev[-3:])[:600])

# journal-derived status lookup: last health event with seq <= S
def journal_status_at(seq_limit):
    st = None
    for r in ev:
        if int(r.get("seq", 0)) <= seq_limit:
            st = r.get("status")
        else:
            break
    return st

latest = json.loads((SNAPDIR / "latest.json").read_text(encoding="utf-8"))
print("latest.json: journal_seq=%s  099=%s  mtime=%s" % (
    latest.get("journal_seq"), (latest.get("health") or {}).get("OCT-SENSE-099"),
    (SNAPDIR / "latest.json").stat().st_mtime))

snaps = sorted(SNAPDIR.glob("snapshot-*.json"))
first_div = None
mismatch_count = 0
statuses = {}
for s in snaps:
    try:
        d = json.loads(s.read_text(encoding="utf-8"))
    except Exception:
        continue
    jsq = int(d.get("journal_seq") or 0)
    live = (d.get("health") or {}).get("OCT-SENSE-099")
    jour = journal_status_at(jsq)
    statuses.setdefault(live, 0)
    statuses[live] += 1
    if live is not None and jour is not None and live != jour:
        mismatch_count += 1
        if first_div is None:
            first_div = (s.name, jsq, live, jour)
print("snapshots_scanned:", len(snaps))
print("live_099_status_distribution:", statuses)
print("snapshot_vs_journal_mismatches:", mismatch_count)
if first_div:
    print("FIRST_MISMATCH_SNAPSHOT:", first_div)
    print("=> divergence onset is at or BEFORE this snapshot's journal_seq:", first_div[1])
else:
    print("no mismatch inside the retained 24h window => onset older than snapshots")
# boundary detail around 'after'
after = int(latest.get("journal_seq") or 0)
before = [r for r in ev if int(r.get("seq", 0)) <= after]
afterev = [r for r in ev if int(r.get("seq", 0)) > after]
print("last_099_journal_event_before_latest_snapshot_seq:",
      json.dumps(before[-1])[:220] if before else None)
print("099_events_after_latest_snapshot_seq:", len(afterev))
