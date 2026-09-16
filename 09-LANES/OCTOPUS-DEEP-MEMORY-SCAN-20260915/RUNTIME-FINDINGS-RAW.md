# RUNTIME-FINDINGS-RAW — my own probes (not agent output)

All observed 2026-09-15T07:07–07:12Z via ssh board138, read-only.

1. G8-021 executed (06:54:16Z verified=True) but request file NEVER retired from
   canary-requests/ → executor now re-evaluates it each tick, base 02fb704d vs live
   fc993720 → OPS_B_STALE_BASE self-loop (receipt 07:05:00Z) + consumes component
   pacing. Retire-miss class (same family as the 04:56Z requed_receipt incident).
2. Fleet-jobs bus histogram (91 rows): QUEUED 17, LEASED 16, RUNNING 15, ACK_RESULT 13,
   PERSISTED 13, CLOSED 13, UNKNOWN 2, REJECTED 2 → 61 rows non-terminal. Consumers
   drain only a minority; QUEUED backlog with a 30-min scheduler = most job types
   have no consumer.
3. B5 breaker OPEN (budget_allows('B5','storage-cache') = False, CIRCUIT_BREAKER_OPEN)
   since 06:38:12Z; feeding failures not yet root-caused (failed/op-ae56d3d1,
   op-f4f0c543 + at least one newer).
4. G22 behavioral probe (queued 06:36Z): ZERO receipts after 34 min — starvation
   defect live-proven (blocked G8-021/W24 pacing aborts the whole B8 category loop).
5. smartmontools.service FAILED on 138 (disk monitoring down on the node that
   survived a disk crisis).
6. tg-inbox spool: 0 rows — no owner→organism binds since STRATA-CHOICE (09-14);
   inbound chain built but carries no traffic.
7. revenue-state.json 06:01:30Z: SENT=3, CHANNEL_AUTHORIZED=17, verified_cash
   implied 0; owner-review.json has open TRAFFIC-DECISION card (ad budget = RED).
8. Restore drill: no restore/drill artifacts found under /home/ari/ofn/state
   (matches GOV-V8 risk register "restore_drill=NOT_RUN").
9. Learning-loop timers all fired recently (feedback-loop 07:0x, experience-ingest
   07:0x, learningfeeder 06:2x, fleet-scheduler 07:0x) — claim holds.
10. mesh leftovers: inbox 0, inbox-expired-20260903 5 files, dead 1, quarantine 2.
11. self-model/OCTOPUS-SELF-DRIVE-20260913/PLAN.json exists in runtime; pins
    INCOMPLETE-WIRINGS-20260913.{md,json} in 00-SEASON as SoT (scan C covers).
12. W24-BINDER-006: base still matches live binder (00dd4ef3); paced behind B8
    component window (opens 07:24:16Z) — NOT a defect unless it fails after that.

DISCREPANCY SEEDS:
- D1: CURRENT-TRUTH says G22 enforcement "LOADED"; runtime: code present, behavior
  unproven (probe starved). Claim stronger than evidence.
- D2: vault "closed learning loop live" vs fleet-jobs bus 61 rows non-terminal:
  timers live, bus backed up — "loop" is partially true.
- D3: older claims "B5 real cycle running" vs B5 breaker open since 06:38Z.
- D4: ENGINEERING-ENTRYPOINT chain: 4 dated versions (09-04 canonical per AGENTS.md,
  but 0906/0907 exist) + none reference the forensic-reorientation lane — navigation
  staleness (the exact conflict the forensic megaprompt was written to end).
