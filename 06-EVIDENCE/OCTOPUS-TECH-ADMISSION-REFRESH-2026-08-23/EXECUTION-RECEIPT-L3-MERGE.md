# EXECUTION RECEIPT — L3 merge to live tree

**Date:** 2026-08-23 (local, Sydney) · **Authority:** owner verdict "LIMITED L3 AUTHORIZATION"
**Target branch:** `rescue/octopus-live-tree-20260821` (the branch the live tree runs from —
**not** `main`) · **Source:** `claude/octopus-chat-connectors-report-8bc6c2`

## 1. Commit IDs

| Source commit (worktree) | Landed on live branch as | Content |
|---|---|---|
| `6f5e548` | **`cc0ceee`** | run_store cross-process append lock + 4 TDRs |
| `48b05d2` | **`9f5169c`** | MCP 2026-07-28 spec verification |
| `af4b36a` | **`1994daa`** | fail_run wiring + test-state leakage isolation |

Pre-merge live HEAD: **`ad788b6`** · Post-merge live HEAD: **`1994daa`**

## 2. Merge ID — and why there isn't one

**`git merge` was attempted first and timed out after 5 minutes.** The source branch is
293 commits / 1880 files / ~491k insertions behind the live branch, so a 3-way merge has to
reconcile the entire divergence — on this machine's mechanical disk (the recorded
`feedback-recursive-scan-hangs-this-laptop` bottleneck) that exceeded the budget.

**Verified the timeout left no damage:** live HEAD still `ad788b6`, and no `.git/MERGE_HEAD`,
no `.git/MERGE_MSG`, no `.git/index.lock`. The merge never progressed far enough to modify
the working tree.

**Mechanism substituted: `git cherry-pick -x` of the three commits.** This is sound here
specifically because every file the commits touch has **zero commits on the live branch since
merge-base** — verified per-file before starting — so each patch applies to an identical
base. It achieves the authorized outcome (the verified changes are on the live branch) without
computing an 1880-file 3-way. `-x` records the originating SHA in each message for provenance.

There is therefore **no merge commit**; the three cherry-picks above are the merge record.
This is a deliberate mechanism substitution, flagged rather than silently done.

Post-cherry-pick state clean: no `CHERRY_PICK_HEAD`, no `MERGE_HEAD`, no `index.lock`.

## 3. Services restarted: **NONE** — deferred to an owner gate

No process was restarted. The changed modules are inert in the running processes until
reload (`feedback-committed-code-is-inert-until-reload`), so **the fixes are on disk but not
yet in effect in production.**

Running processes that load the changed modules:

| PID | Process | Started | Loads |
|---|---|---|---|
| 12220 | `_ops/telegram_center/miniapp_gateway.py` | 21/08 16:18 | `event_stream` → `run_store` (direct import in the `/api/runs` handler) |
| 2296 | `_ops/telegram_center/center.py` | 23/08 08:38 | `collaborator` via `telegram_adapter` |
| 24760 | `cortex/cortex.py` | 21/08 16:19 | possibly — not confirmed |
| 29020 | `organism.py` | 23/08 08:02 | possibly — not confirmed |

Not restarted, for four reasons:

1. **No urgency.** Both fixed defects are *latent* in current production. The `run_store`
   race requires concurrent appends to the **same** `run_id`; production mints a fresh
   `run_id` per turn and appends sequentially, so it cannot currently fire. `fail_run` only
   matters when an exception escapes `handle()`.
2. **Restarting bounces the owner's live Telegram bot and mini-app** — outward-facing and
   disruptive, on a Sunday evening with the system in active use.
3. **The service set is not fully confirmed.** Items 3-4 above are unverified, and the owner's
   instruction was "restart *only* services that load the changed modules." Restarting on a
   guess violates that instruction rather than following it.
4. **The owner's own stated preference: "one consolidated merge and one controlled restart."**
   `server/discover` is still pending (blocked), so a second deployment is coming regardless.
   Deferring this restart to combine with that one *is* the consolidated restart the
   authorization asks for.

Because every changed API signature is unchanged, a mixed old/new module state across
processes is benign — no restart is required for correctness of what is already running.

## 4. Tests

Run **from the live tree** after the cherry-picks, against the merged code:

| Suite | Result |
|---|---|
| `test_run_store_concurrency` | **4/4** |
| `test_run_failure_lifecycle` | **7/7** |

Plus, before merge, in the worktree: `test_cognitive_events` 10/10 · `test_cognitive_unify`
11/11 · `test_miniapp_gateway` 49/49 · `test_octopus_mcp_search` 4/4 — **85 checks, zero
failures.**

Byte-identity check: all 7 merged files (`run_store.py`, `collaborator.py`, `chat_log.py`,
`criticality_v2.py`, `test_cognitive_unify.py`, and the two new suites) are identical to the
verified worktree versions.

### Honest limit on the leakage measurement

The worktree measurement — **2 tracked files dirtied → 0** — is the clean evidence, because
nothing else writes there.

On the live tree the same measurement is **not attributable**: 5 processes write state
continuously, and the tree already showed 279 tracked-modified files *before* any of this
work began. `_ops/state/chat/chat-log.jsonl` appears modified there, but the organism writes
real owner chat to that file as its actual production purpose. No claim is made that live-tree
state churn was caused, or not caused, by the test run — the measurement cannot separate them.

## 5. Not done from the L3 list

- **`run_all.py` registration of `test_run_store_concurrency.py`** — `_ops/tests/run_all.py`
  is **16 commits ahead** on the live branch; the worktree copy is stale, and the file is
  WORKLOCK-reserved for central registration regardless. **Owner/ari action.** Until it is
  registered, the two new suites do not run in the central sweep.
- **Post-restart smoke/health verification** — not applicable, nothing was restarted.

## 6. Rollback

Three cherry-picks, revertible newest-first, no state migration and no schema change:

```bash
git revert --no-edit 1994daa 9f5169c cc0ceee
```

Per-file rollback also works, since all changes are one-concern edits:

```bash
git checkout ad788b6 -- _ops/cognitive/run_store.py
```

- No process was restarted, so **rollback requires no restart either** — the running
  processes are still executing the pre-merge code.
- Defaults for `chat_log.py` / `criticality_v2.py` are byte-identical to their previous
  paths, so reverting them is a no-op in production.
- `collaborator.handle`'s public signature never changed, so callers are unaffected in
  either direction.
- Rollback pattern verified experimentally in the previous batch (checkout old → defect
  returns → checkout new → fix returns).

Pre-merge SHA recorded: **`ad788b6a165736a2761e4214982784a018ed7134`**

## 7. Boundaries

ARMED **OFF**, PWM **OFF**, untouched. No PolicyGate / Ledger / owner-verdict /
`durable_journal` semantics changed. No dependency. No deletion. **No push to any external
remote.** No ARM/PWM/actuator effect. `git add` with explicit paths only.
