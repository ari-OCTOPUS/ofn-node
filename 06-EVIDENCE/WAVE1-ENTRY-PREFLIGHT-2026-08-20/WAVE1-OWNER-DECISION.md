---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave1, decision]
---

# WAVE1-OWNER-DECISION

**Verdict: GO** for a **bounded canary-sidecar** (read-only API + receipts + kill switch + write guard).

**Not authorized by this GO:** cortex prompt injection, organism tick hook, daemon/live/cortex restart, memory.db writes, paid calls, Wave 0 artifact edits, 98-row receipt migration.

## Remaining blockers (out of this canary)

- `_recall_for_goal` still searches MemoryStore without Wave 1 isolation (pre-existing; not patched).
- Full 786-suite execution was not completed; registry completeness ≠ execution coverage.
- `wave0_governor.wave1_unlocked` remains **false** (Wave 0 freeze). Wave 1 uses `_ops/state/wave1/lock.json` instead.

## Activation that already happened

- Independent verifier `WAVE1-VERIFIER.json` confirmed=true (pre-unlock snapshot).
- Canary sidecar `WAVE1-CANARY.json` ok=true, production hashes unchanged, restarts=0.
- Lock opened: `wave1_unlocked=true`, `prompt_injection=false`, `memory_writes=false`, `organism_hook=false`.

## Exact scope

Module `_ops/nervous_recovery/wave1_readonly.py` may retrieve TEST_ONLY / caller-scoped rows when lock is open. Production MemoryStore is not opened by this module.

## Files / processes

- Touched: nervous_recovery wave1_* , `test_wave1_preflight.py`, `run_all.py` register, evidence pack, `lock.json`
- Not restarted: organism, cortex, daemon, live

## Canary duration

One sidecar pass (~seconds), n=12 attributed reads. Not a multi-hour soak.

## Stop conditions

Create `_ops/STOP-WAVE1-READ` or set `lock.json` `wave1_unlocked=false`. See [[WAVE1-ROLLBACK]].

## Owner command for the next expansion (prompt injection / organism hook)

Not required by master auth if gates still hold, but the next expansion is a **new canary** and must not skip a verifier. Proposed:

```text
WAVE1_ROLLOUT_ORGANISM_HOOK=GRANTED
prompt_injection=NOT_GRANTED
memory_writes=FORBIDDEN
restart=organism_only
```
