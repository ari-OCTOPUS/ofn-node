---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave1, rollback]
---

# WAVE1-ROLLBACK

Wave 1 canary does **not** require process restart. Rollback is flipping the lock file.

## Disable (≤ 5 seconds)

1. Write `_ops/state/wave1/lock.json` with `"wave1_unlocked": false`.
2. Optionally create `_ops/STOP-WAVE1-READ` (contents: `owner-rollback`).
3. Do **not** restart cortex/daemon/live/organism for this rollback.
4. Do **not** touch `memory.db` or `cost-receipts.jsonl`.

Exact lock closed body:

```json
{
  "schema": "wave1-lock/1",
  "wave1_unlocked": false,
  "verifier_pass": false,
  "note": "rolled back"
}
```

## Affected files

- `_ops/state/wave1/lock.json` (the unlock)
- evidence pack under `06-EVIDENCE/WAVE1-ENTRY-PREFLIGHT-2026-08-20/` (leave as history)
- Wave 0 pack: **must remain unchanged**

## State restoration

No memory rows are written by this canary, so there is no memory restore step. Prove with sha256 of `memory.db` (if present) and `cost-receipts.jsonl` matching `WAVE0-FREEZE.json`.

## Post-rollback checks

- `wave1_readonly.read_lock()["wave1_unlocked"] is False`
- `wave0_governor.audit_wave0()["wave1_unlocked"] is False`
- retrieve with `shadow=False` returns `locked`
- T49 pulse still healthy (existing organism path)

## Maximum rollback time

5 seconds (file write). No reboot.
