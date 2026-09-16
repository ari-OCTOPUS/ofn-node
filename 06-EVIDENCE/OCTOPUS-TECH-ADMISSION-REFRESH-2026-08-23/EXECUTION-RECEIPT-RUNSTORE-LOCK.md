# EXECUTION RECEIPT — run_store concurrent-append fix

**Date:** 2026-08-23 · **Authority:** owner verdict "BOUNDED AUTONOMY", L0–L2
(code changes inside assigned worktree; tests; reversible refactoring; commits to
assigned branch) · **Worktree:** `great-spence-d84352` ·
**Branch:** `claude/octopus-chat-connectors-report-8bc6c2`

Selected autonomously from `TDR-DBOS-RUNSTORE.md` option B — the only **measured**
defect found anywhere in the tech-admission audit. Ranked first on impact ×
evidence-confidence × unlock-value ÷ (cost × risk), and fully reversible.

## 1. Pre-flight — staleness check

The audit read every source file from the **live tree** (`F:\backup`), but this worktree
sits at commit `8b7e6e8` (2026-08-16). Fixing a stale copy would strand the work
(recorded lesson: `feedback-workflow-worktree-isolation-strands-fixes`).

`diff -q` live-tree vs worktree, all five files in scope:

| File | Result |
|---|---|
| `_ops/cognitive/run_store.py` | IDENTICAL |
| `_ops/cognitive/event_stream.py` | IDENTICAL |
| `_ops/owner_console/collaborator.py` | IDENTICAL |
| `_ops/tests/test_cognitive_events.py` | IDENTICAL |
| `_ops/tests/harness.py` | IDENTICAL |

The fix therefore applies cleanly to the code actually running.

## 2. Defect — reproduced, not asserted

Test written **before** the fix and required to fail first, per the threshold set in
`TDR-DBOS-RUNSTORE.md` §6 (a test that passes pre-fix pins the bug rather than catching it —
`feedback-green-mutation-means-unwatched`).

`_ops/tests/test_run_store_concurrency.py` · 8 threads × 12 appends on one `run_id`,
`threading.Barrier` to open the race window.

**Pre-fix output (verbatim):**

```
❌ concurrent appends -> no duplicate sequence: sequence تکراری: [1, 8, 14, 15, 25, 27, 34, 39, 40, 46]
   — 96 رویداد ولی فقط 67 شمارهٔ یکتا (race در append_event)
❌ concurrent appends -> no event lost: انتظار 97 رویداد، 95 یافت شد — رویداد گم شده است
❌ returned sequences unique: append_event دو بار همان sequence را برگرداند: [1, 6, 10, 11, 19, 20, 21, 25, 26, 27]
✅ single-thread monotonic (regression guard)
```

**The defect is worse than the TDR stated.** The TDR predicted duplicate sequence numbers.
Reality also **destroys events**: 96 appends produced 95 records. Mechanism —
concurrent writes interleave mid-line, producing malformed JSON, which
`_read_jsonl` discards via `except json.JSONDecodeError: continue`. The event vanishes
with no error anywhere. `TDR-DBOS-RUNSTORE.md` §3 is superseded on this point by this receipt.

## 3. Fix

`_ops/cognitive/run_store.py` — cross-process exclusive file lock around the whole
critical section.

- `_exclusive(run_id)` contextmanager; lock files in `RUNS_DIR/.locks/` so `RUNS_DIR`
  keeps only data files.
- `fcntl.flock` on POSIX, `msvcrt.locking` + bounded retry on Windows
  (`LOCK_TIMEOUT_S = 30.0`). Neither available → degrades to prior behavior, never crashes.
- **Cross-process, not in-process.** A `threading.Lock` would have passed this suite and
  still lost events across processes — `feedback-inprocess-lock-doesnt-stop-a-second-process`.
  Locks bind to the open-file-description, so the same primitive covers threads too.
- The **write** is inside the lock, not just the sequence computation — that is what
  fixes event loss (§2), which a compute-only lock would not have.
- `_mark_terminal` left deliberately lock-free (caller holds it; the lock is not
  reentrant); public `mark_terminal()` acquires it. Deadlock avoided by construction.
- `create_run` also wrapped.
- `DURABILITY` constant `PROCESS_DURABLE` → `SERIALIZED_APPEND`. Still no fsync guarantee;
  the string was already load-bearing documentation and would now be a lie.

**Not fixed, deliberately:** the O(n) full-file re-parse per append. It is a performance
issue with no current trigger (~6 events/run), and a sidecar counter would add a new file
format plus crash-consistency semantics. Fixing a non-existent problem is the same error
this audit criticized elsewhere. Documented, not built.

## 4. Verification

| Suite | Pre-fix | Post-fix |
|---|---|---|
| `test_run_store_concurrency.py` (new) | **3 of 4 FAIL** | **4/4 PASS** |
| `test_cognitive_events.py` | 10/10 | **10/10** |
| `test_cognitive_unify.py` | 11/11 | **11/11** |
| `test_miniapp_gateway.py` | 49/49 | **49/49** |

Zero regression. `ast.parse` clean.

## 5. Incidental finding — test-isolation leak (NOT caused by this change)

Running the pre-existing suites dirtied **tracked** state files in the worktree:

```
_ops/state/chat/chat-log.jsonl              | 2 ++
_ops/state/criticality/criticality-v2.jsonl | 1 +
```

plus an untracked `_ops/state/cognitive/runs/run_9523f5b935d2.jsonl` (a minted
`run_<hex12>` id — from `collaborator` via `test_cognitive_unify`, not from this suite,
which only uses fixed `run_conc_*` ids and a temp `RUNS_DIR`).

`git status` was clean before this session apart from the TDR folder, so the suites caused
it. `harness.live_state_guard` did not catch these paths. Both tracked files were restored
with `git checkout --` (revert to HEAD, not deletion) and are **excluded from the commit**.

The untracked run file was **left in place** — the vault constitution forbids deletion
(*"هرگز حذف نکن؛ فقط منتقل کن"*). Owner may remove it.

This is a real pre-existing gap in suite isolation and is logged for separate triage. It is
out of scope here and no attempt was made to fix it.

## 6. Rollback

Single tracked file changed. Verified live, not asserted:

```bash
git checkout HEAD~1 -- _ops/cognitive/run_store.py   # → concurrency suite FAILS 3/4 (old behavior)
git checkout HEAD   -- _ops/cognitive/run_store.py   # → concurrency suite PASSES 4/4
```

- **No state migration.** Storage stays append-only JSONL; existing run files remain
  readable by both old and new code — the record schema is untouched.
- **Forward-compatible:** old code reads new files fine. New code reads old files fine.
- Lock files in `RUNS_DIR/.locks/` are pure runtime artifacts; deleting them is safe and
  they are recreated on demand.
- Only behavioral difference on rollback is the return of the race.

## 7. Boundaries respected

- ARMED **OFF**, PWM **OFF** — untouched.
- No PolicyGate, Ledger, or owner-authored decision modified.
- No secrets, permissions, external messages, financial actions, or installs.
- No dependency added — `fcntl`/`msvcrt`/`contextlib` are stdlib. Admission Gate not triggered.
- No write to the live tree. All code changes confined to the worktree.
- No deletion.
- `git add` used with **explicit paths only** — never `git add -A` (WORKLOCK).
- `_ops/tests/run_all.py` **not** touched — central registration is WORKLOCK-reserved.
  **Owner/ari action:** register `test_run_store_concurrency.py` there.
- Single sequential session. No fan-out.

## 8. Gate reached

Merging this branch to the live tree is **owner-gated** (WORKLOCK). Not attempted.
The running processes still execute the unfixed code until that merge happens —
`feedback-committed-code-is-inert-until-reload` applies: a merge alone is not enough,
the gateway/cortex processes must be restarted for the fix to take effect in production.
