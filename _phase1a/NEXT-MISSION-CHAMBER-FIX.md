# NEXT MISSION — CHAMBER FIX (surgical, independent)

> Queued 2026-07-24, immediately after the C6 first-ignition merge (`d56597c`).
> Scope: **only** the two pre-existing failures in `_ops/tests/test_chamber_temperature.py`.
> These are unrelated to the C6 memory-recall optimization — that is proven below.

## The defect

Full suite (`python _ops/tests/run_all.py`) is **2232 pass / 3 fail**. All three come from a
single file, `_ops/tests/test_chamber_temperature.py`:

| # | failing assertion |
|---|---|
| 1 | `❌ [V] مصرفِ verdict از کانال` — verdict consumption from the channel |
| 2 | `❌ [V] نگاشت و به‌روزرسانیِ registry` — registry mapping + update |
| 3 | `❌ شکست: test_chamber_temperature.py (capability revoked)` — the runner's file-level roll-up of #1–#2 (`run_all.py:405`), not a separate defect |

Everything else in that file is green — the `[R]` rounds_for, `[C]` temperature behaviour,
and `[S]` zero-auto-merge / flag-gating sections all pass. The failure is isolated to the
`[V]` (verdict) section.

## Proof it is PRE-EXISTING (not caused by C6)

Measured both ways on the same machine, same run command:

| tree state | pass | fail | failing set |
|---|---|---|---|
| clean baseline (patch reverted via `git checkout -- _ops/memory/memory_store.py`) | 2232 | 3 | the same 3 |
| C6 batched-hydration applied | 2232 | 3 | **identical** |

Identical fail set ⇒ the C6 change introduced **zero regressions**, and these two assertions
were already red before it. They are therefore a genuine, separate defect on trunk.

## Where to look

- Test: `_ops/tests/test_chamber_temperature.py` — the `[V]` section.
- Likely subjects: `_ops/outcomes/verdict_recorder.py`, `_ops/outcomes/proposal_registry.py`,
  and whatever channel object the chamber consumes verdicts from.
- Note the adjacent green assertions `[V] fail-soft: کانالِ خراب` and
  `[V] hasattr-guard: کانالِ بدونِ متد` — the fail-soft/guard paths work, so the defect is
  most likely in the **happy path** contract (shape of the consumed verdict, or the
  registry update call) rather than in error handling.

## Acceptance criteria

1. `python _ops/tests/test_chamber_temperature.py` → all green.
2. `python _ops/tests/run_all.py` → **2235 pass / 0 fail** (2232 + the 2 repaired assertions,
   and the file-level roll-up clears).
3. No change to propose-only / owner-gated invariants: `merge_or_deploy` stays constitutionally
   forbidden, the chamber stays behind `OCTOPUS_WIRE_CHAMBER_T`, zero auto-merge strings absent.
4. No live-tree writes; fix on a branch, owner votes the merge.

## Guardrails

- Diagnose before editing — confirm whether the defect is in the test's expectation or in the
  production contract. Do not "fix" by loosening the assertion.
- The Mutation Chamber is an owner-gated capability; do not widen its permissions to make a
  test pass.
