---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave1, shadow]
---

# WAVE1-SHADOW-PLAN

Mode: TEST_ONLY fixture. No production mutation. `paid_calls=0`.

## Identities (fixed)

| | id |
|---|---|
| task A | `tsk_wave1_a` |
| run A | `run_wave1_a` |
| task B | `tsk_wave1_b` |
| run B | `run_wave1_b` |
| shared | `mem_shared_01` with `shared=true` |

## Fixture

`wave1_readonly.default_fixture()`: 8 private A records, 2 private B, 1 shared, 1 future (must not leak).

## Expected

- ≥10 retrieve calls
- A never sees `mem_b_01` / `mem_b_02`
- B never sees `mem_a_*`
- both may see `mem_shared_01` when queried
- future id absent
- unresolved caller → `task_id` empty, not inferred
- v2 receipts with `capability_id=memory.read`
- store fingerprint unchanged
- `STOP-WAVE1-READ` in overlay → status `killed`, zero hits

## Rollback of the shadow itself

Delete overlay STOP file (done by the runner). Fixture lives only in process memory. No production files to restore.

## Production rollback (if lock was opened)

See [[WAVE1-ROLLBACK]].
