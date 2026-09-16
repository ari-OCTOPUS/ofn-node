# EVELAB ↔ DOCTOR WIRE — PLAN STUB (P1 pointer)
# Evidence folder: 06-EVIDENCE/OCTOPUS-POLLER-TELEGRAM-UNIQUE-2026-08-23/
# Status: NOT DONE — planning pointer only. Do not treat as implemented.

## Intent
Wire EveLab (eval / holdout / lab signals) into OCTOPUS doctor checks so uniqueness and poller health are continuously asserted, not only manually sampled.

## Candidate asserts (doctor)
1. Exactly one live `telegram_center/center.py` PID; refuse / WARN if >1.
2. Exactly one ACTIVE row in `state/telegram/poll-lease.sqlite3`; `owner_pid` matches center PID.
3. Exactly one non-stale `state/locks/tg-poller-*.lock`; `poller_id == center-canonical`.
4. `LIVE-TELEGRAM.flag` enabled ↔ poll-health freshness within SLA.
5. No second getUpdates consumer (organism/miniapp must not hold poll lease).

## EveLab side
- Emit structured eval events / canary outcomes that doctor can read (path TBD under `_ops/eval` or `state/telegram/loop`).
- Keep dry-run / no live TG spam constraints.

## Non-goals (this stub)
- No code landed here.
- No restart of healthy procs.
- No claim of wire completion.

## Next concrete step
Locate doctor check registry + add fail-closed uniqueness probe with unit test against fixture lease DB; then optional EveLab event publisher.

Checked_at: 2026-08-23T02:45+10 (approx)
Related evidence: RESULT.json (PASS single poller uniqueness soak sample)

## P1 wire landed (2026-08-23)
See `06-EVIDENCE/OCTOPUS-EVELAB-DOCTOR-WIRE-2026-08-23/RESULT.json` — reversible experiment-ticket path + fixture tests. Uniqueness doctor asserts remain NEXT.


## P2 uniqueness landed (2026-08-23)
See `06-EVIDENCE/OCTOPUS-DOCTOR-UNIQUENESS-2026-08-23/RESULT.json` — fail-closed probe in `_ops/doctor/poller_uniqueness.py` wired into `lab_call_doctor_check` dry-run fixture + live RO confirm (1 center PID / 1 ACTIVE lease / 1 tg-poller lock). Tests 7/7 + evelab 5/5.
