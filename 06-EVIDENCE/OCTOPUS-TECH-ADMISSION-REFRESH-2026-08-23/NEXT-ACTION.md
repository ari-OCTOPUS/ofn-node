# NEXT-ACTION — runtime truth after L3 merge (2026-08-23)

## Where things stand

| Step | Status |
|---|---|
| Step 1 — read-only audit | **PASS** → `AUDIT.json` |
| Step 2 — four TDRs | **PASS** → `TDR-*.md` (all four now on the live branch) |
| L2 batch — fail_run + leakage | **PASS** → `EXECUTION-RECEIPT-FAILRUN-AND-LEAKAGE.md` |
| L2 batch — `server/discover` | **BLOCKED** (see below) |
| L3 — merge to live tree | **DONE** → `EXECUTION-RECEIPT-L3-MERGE.md` |
| L3 — `run_all.py` registration | **BLOCKED** |
| L3 — service restart | **DEFERRED to owner gate** |

## Runtime truth — read this before assuming the fixes are live

**The fixes are on disk on the live branch. They are NOT yet running.**

No process was restarted. `miniapp_gateway.py` (PID 12220, up since 21/08) and
`center.py` (PID 2296) still execute the pre-merge code. `feedback-committed-code-is-inert-until-reload`.

This is safe and deliberate — both fixed defects are *latent* in current production (the
`run_store` race needs concurrent appends to the same `run_id`, which one-turn-at-a-time
chat never produces). Nothing is degraded by waiting.

Live branch: `rescue/octopus-live-tree-20260821` · HEAD **`1994daa`** (was `ad788b6`)

| Landed | Content |
|---|---|
| `cc0ceee` | run_store cross-process append lock + 4 TDRs |
| `9f5169c` | MCP 2026-07-28 spec verification |
| `1994daa` | fail_run wiring + test-state leakage isolation |

Applied by `git cherry-pick -x`, not `git merge` — the merge timed out at 5 min because the
source branch is 293 commits / 1880 files behind. Verified no damage from the timeout, and
verified every touched file had zero commits on the live branch since merge-base, so each
patch applied to an identical base. Details in `EXECUTION-RECEIPT-L3-MERGE.md` §2.

## What was actually fixed

1. **Event loss (data integrity).** `run_store.append_event` was an unguarded
   read-modify-write. Proven pre-fix: 96 concurrent appends → 67 unique sequences **and 2
   events destroyed** (interleaved writes corrupt lines; `_read_jsonl` swallowed the
   `JSONDecodeError`). Fixed with a cross-process file lock covering the write, not just the
   sequence computation.
2. **Orphaned runs.** `fail_run()` had zero production callers, so any exception escaping
   `handle()` left a run `ACTIVE` forever — a dead conversation shown to the owner as
   in-progress. Now wired at the lifecycle boundary; the exception still re-raises.
3. **False success.** `MODEL_FINISHED` reported `COMPLETED` even when the model call failed.
   Now `FAILED`, while the run itself still completes (a stub reply really was delivered).
4. **Test-state leakage.** Three independent causes; 2 tracked files dirtied → 0.

## Three things needing the owner

1. **Restart gate.** To make the above live:
   restart `miniapp_gateway.py` (PID 12220) and `center.py` (PID 2296). Recommendation: fold
   this into the same restart that deploys `server/discover`, per the owner's own "one
   controlled restart" preference. Note the recorded gap:
   `RESTART-PROCESS.ps1` has no zombie fallback (`feedback-cortex-restart-has-no-zombie-fallback`).
2. **`run_all.py` registration.** `_ops/tests/run_all.py` is 16 commits ahead of the working
   branch and is WORKLOCK-reserved. Until someone registers them, `test_run_store_concurrency.py`
   and `test_run_failure_lifecycle.py` **do not run in the central sweep**.
3. **How to unblock `server/discover`.** The working branch's `server.py` is the 411-line
   pre-HTTP version; live has 635 lines (commits `5899ed5`, `634cd76`). Editing from that
   stale base would conflict and risk dropping the live stateless HTTP transport. Options:
   (a) bring the branch current (merging 293 commits — expensive on this disk, as the timeout
   showed), or (b) do the MCP work in a fresh worktree cut from `rescue/octopus-live-tree-20260821`.
   **(b) is cheaper and cleaner.** Spec research is already complete in
   `TDR-MCP-ADAPTER-HEADERS.md` — only the code is blocked.

## Design note for whoever implements `server/discover`

It must **not** advertise `2026-07-28` in `supportedVersions`. This server implements none of
the modern revision (no `_meta` version handling, no MRTR, no `resultType`, no
`subscriptions/listen`). A truthful `DiscoverResult` listing only the versions actually served
(`2025-06-18`, `2025-03-26`, `2024-11-05`) is what lets a dual-era client fall back correctly;
claiming modern support would break era detection — the probe would report a modern server
that then fails every modern request. Error code for version mismatch is `-32022`.

## Still unanswered (from the TDRs)

- Is crash-mid-turn resume a real requirement, or theoretical? Gates `TDR-DBOS-RUNSTORE` option C.
- Is live token-level streaming wanted in the mini-app? Gates `TDR-SSE-O-E4` option A vs B —
  and note option B would activate the `run_store` race that was just fixed.
