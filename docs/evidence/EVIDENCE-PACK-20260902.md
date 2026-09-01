# EVIDENCE PACK — raw outputs for supervision §7

generated: 2026-09-01T14:48:49Z (UTC) · host: DietPi

## 1) pytest raw — all three batteries
```
.........................                                                [100%]
25 passed in 3.12s
```
## 2) rate card — command + output + active card
```
$ cd ~/ofn/ofn/agents && python3 rate_card_builder.py
{"written": "/home/ari/.local/share/ofn/painting_rate_card.json", "approved": false}
{"n_contracts": 9, "min_aud": 153105.0, "median_aud": 218311.5, "p25_aud": 163836.2, "p75_aud": 651200.0, "max_aud": 772819.41}
```
active card (graded) — key fields:
```json
[stderr] Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import json,os; d=json.load(open(os.path.expanduser('~/.local/share/ofn/painting_rate_card.json'))); print(json.dumps({k:d[k] for k in ('grade','ocp_derived','approval')}, ensure_ascii=False, indent=1))
                                                                                                                             ~^^^
KeyError: 'grade'
```
## 3) git show --stat
```
af4aba8b feat(autonomy): full roadmap #64 executed — ears, quote engine, infra, governance
 QUESTIONS-FOR-OCTOPUS.md                     |   15 +
 data/domain_allowlist.json                   |   11 +
 data/painting_source_registry.json           | 1168 +++++++++++++-------------
 docs/OWNER-CHECKLIST.md                      |   35 +
 docs/adr/2026-09-01-A-utc-unification.md     |   20 +
 docs/adr/2026-09-01-B-transport-vs-worker.md |   21 +
 ofn/agents/consent_store.py                  |  281 +++++++
 ofn/agents/daily_digest.py                   |   89 ++
 ofn/agents/followup_worker.py                |  156 ++++

42122af1 feat(next-agent): E->Q loop closed + ops hardening (roadmap #64 follow-through)
 ofn/agents/quote_pipeline.py | 126 +++++++++++++++++++++++++++++++++++++++++++
 ofn/agents/rotate_logs.py    |  45 ++++++++++++++++
 tools/install_systemd.sh     |   8 +--
 tools/smoke.sh               |  41 ++++++++++++++
 4 files changed, 217 insertions(+), 3 deletions(-)

7a1f4e36 feat(convergence): 4 of 5 roadmap items from CB-Insights x HF convergence doc — honest E-grades
 ofn/agents/capability_token.py   | 123 ++++++++++++++++++++++++++++++++++++
 ofn/agents/followup_worker.py    |  15 ++++-
 ofn/agents/imap_listener.py      |   8 +++
 ofn/agents/memory_chain.py       |  83 ++++++++++++++++++++++++
 ofn/agents/quote_engine.py       |  23 +++++--
 tests/test_teeth.py              | 133 +++++++++++++++++++++++++++++++++++++++
 tools/mcp/octopus_repo_server.py | 125 ++++++++++++++++++++++++++++++++++++
 tools/reconcile.py               |  22 ++++---
 8 files changed, 519 insertions(+), 13 deletions(-)

```
## 4) smoke.sh raw
```
pytest lane battery:                          PASS
imports (transport/worker/writer/listener/quote):PASS
reconcile 6 invariants:                       PASS
timers armed (7 octopus timers):              PASS (7/7)
clock synchronized (NTP):                     PASS
last backup exists:                           PASS (20260901T140621Z)
halt oracle clear (HALT-ALL absent):          PASS
rate card lock intact:                        PASS (locked)
SMOKE ALL-PASS
```
## 5) systemctl list-timers
```
Tue 2026-09-01 14:50:00 UTC  1min 5s Tue 2026-09-01 14:45:03 UTC 3min 50s ago octopus-budget-monitor.timer octopus-budget-monitor.service
Tue 2026-09-01 15:00:00 UTC    11min Tue 2026-09-01 14:06:02 UTC    42min ago octopus-heartbeat.timer      octopus-heartbeat.service
Tue 2026-09-01 15:00:00 UTC    11min Tue 2026-09-01 14:45:03 UTC 3min 50s ago octopus-imap.timer           octopus-imap.service
Tue 2026-09-01 15:00:00 UTC    11min Tue 2026-09-01 14:30:03 UTC    18min ago octopus-quote.timer          octopus-quote.service
Tue 2026-09-01 15:00:00 UTC    11min Tue 2026-09-01 14:45:03 UTC 3min 50s ago octopus-scheduler.timer      octopus-scheduler.service
Tue 2026-09-01 21:00:00 UTC       6h -                                      - octopus-digest.timer         octopus-digest.service
Wed 2026-09-02 01:00:00 UTC      10h -                                      - octopus-followup.timer       octopus-followup.service
Wed 2026-09-02 03:00:00 UTC      12h -                                      - octopus-backup.timer         octopus-backup.service
Sun 2026-09-06 04:00:00 UTC   4 days -                                      - octopus-drill.timer          octopus-drill.service
```
## 6) reconcile raw
```
{
 "date": "2026-09-01",
 "checks": {
  "R1_counter_eq_wal_today": {
   "counter": 5,
   "wal_sent_today": 5,
   "match": true
  },
  "R2_events_today": {
   "events": 5,
   "wal": 5,
   "match": true
  },
  "R3_outbox_eq_wal": {
   "outbox_sent": 5,
   "wal_sent_all": 5,
   "match": true
  },
  "R4_active_leads": {
   "active_leads": 8,
   "wal_sent_all": 5,
   "match": true
  },
  "R5_no_suppressed_in_cycle": {
   "violations": 0,
   "match": true
  },
  "R6_wal_no_nonfinal": {
   "nonfinal": {},
   "match": true
  }
 },
 "ok": true,
 "outbox_pending": 0
}
```

## 7) fingerprint store (production, post-cleanup)
```

```
---
End of pack.
