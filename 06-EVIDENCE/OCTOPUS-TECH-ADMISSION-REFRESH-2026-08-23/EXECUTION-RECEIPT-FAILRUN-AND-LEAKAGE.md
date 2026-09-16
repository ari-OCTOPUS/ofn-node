# EXECUTION RECEIPT — fail_run wiring + test-state leakage isolation

**Date:** 2026-08-23 · **Authority:** owner verdict "CONTINUE L2, THEN LIMITED L3"
**Worktree:** `great-spence-d84352` · **Branch:** `claude/octopus-chat-connectors-report-8bc6c2`
**Batch items covered:** 4, 5, 6, 7, 9, 10 · **Blocked:** 1, 2, 3 (see §5)

## 1. Pre-flight — per-file drift (this is what split the batch)

The previous batch found every file byte-identical to the live tree. **Not so this time.**
The live tree is on branch `rescue/octopus-live-tree-20260821` @ `ad788b6`, which is
**293 commits ahead** of this branch (1880 files, ~491k insertions since merge-base `8b7e6e8`).

Per-file commit counts on the live branch since merge-base:

| File | Commits ahead | Batch impact |
|---|---|---|
| `_ops/owner_console/collaborator.py` | **0** | safe to edit |
| `_ops/owner_console/chat_log.py` | **0** | safe to edit |
| `_ops/doctor/criticality_v2.py` | **0** | safe to edit |
| `_ops/tests/test_cognitive_unify.py` | **0** | safe to edit |
| `_ops/cognitive/{run_store,event_stream}.py` | **0** | safe |
| `_ops/tests/harness.py`, `live_state_guard.py` | **0** | safe |
| `_ops/octopus_mcp/server.py` | **2** | **BLOCKED** — batch items 1-3 |
| `_ops/tests/run_all.py` | **16** | **BLOCKED** — L3 registration |

Method note: an earlier check using `"F:\backup\\$f"` reported everything as differing.
That was a **path-quoting artifact** (mixed separators), not drift — re-run with
`F:/backup/$f`. Recorded because a false drift signal would have wrongly aborted the batch
(`feedback-resolve-before-you-judge-a-path`).

## 2. Items 4-6 — production failure boundary, `fail_run` wired, verified

### The measured boundary (item 4)

Traced every non-test caller. The chat-run lifecycle is owned entirely by
`collaborator.handle` — it calls `start_run()`, and `complete_run()` at the end. Two real
failure boundaries exist, and **neither was recorded correctly**:

**(a) Exception escapes `handle()` → run orphaned forever.**
Almost every block in `handle` is wrapped in `except Exception: pass`, but
`_model_enhance(base_reply, text)` is **not**. If the model adapter *raises* (as opposed to
returning `ok=False`), the exception leaves `handle`, `complete_run` never runs, and
`_state_from_events` returns `"ACTIVE"` forever. The owner sees a dead conversation as
"still in progress."

**(b) Model call fails without raising → run reports success.**
`_model_enhance` falls back to a stub and sets `model_source="model-fallback-stub"`, but
`MODEL_FINISHED` was emitted with the default `status="COMPLETED"`. The timeline reported a
real failure as complete.

### The fix (item 5)

`_ops/owner_console/collaborator.py`:

- `handle()` is now a thin lifecycle wrapper; logic moved to `_handle_impl()`. Any escaping
  exception calls `fail_run(run_id, f"unhandled:{type(exc).__name__}")` and **re-raises** —
  caller behavior is unchanged. Public API (`collaborator.handle`) is untouched, so the four
  production call sites (`conversation_hub/service.py`, `telegram_adapter.py`,
  `collab_sim.py`, `shadow_rollout.py`) need no change.
- Run context is passed **explicitly** (`_run_ctx` dict), not via thread-local or module
  global — concurrent callers must not share lifecycle state.
- Context is cleared after a successful `complete_run`, so a run can never receive both
  `RUN_COMPLETED` and `RUN_FAILED`.
- `MODEL_FINISHED` now carries `status="FAILED"` when the model call failed, plus a
  `failure_reason`. **The run itself still completes** — a stub reply really was delivered;
  marking the run FAILED would be a lie in the opposite direction.
- New `_sanitize_reason()`: the adapter's reason string can contain exception text, and
  `reason`/`failure_reason` are **not** in `run_store`'s redaction key list. It strips to
  `[alnum-_.:]` and caps at 60 chars, so prose leakage is structurally impossible.
  Only the exception **type name** is recorded — never its message.

### Verification (item 6) — failing-first

`_ops/tests/test_run_failure_lifecycle.py`, 7 checks. Proven against pre-fix code by
reverting `collaborator.py` to HEAD:

```
❌ exception in handle -> run FAILED: run باید FAILED باشد، دیده شد ACTIVE — fail_run سیم نشده
❌ failure reason carries no owner text: نوعِ استثنا ثبت نشد
❌ model failure -> event FAILED, run COMPLETED: ... دیده شد COMPLETED
💥 _sanitize_reason strips prose: AttributeError (helper did not exist)
✅ fail_run marks terminal FAILED        (pre-existing correct behavior)
✅ failed run is not ACTIVE              (pre-existing correct behavior)
✅ successful run still completes        (pre-existing correct behavior)
```

Post-fix: **7/7**. The three that passed pre-fix are regression guards and were expected to.

**Two bugs in the first draft of this suite, caught and fixed before trusting it** — worth
recording because both produce false greens:
1. `harness` deliberately sets `OCTOPUS_WIRE_COLLAB=0` ("suites that need them re-arm
   explicitly"). Without re-arming, `handle()` returns at its first line and no run is ever
   created — the suite was testing nothing.
2. Identifying the run as "newest file by mtime" picked up this file's own `run_*` fixtures.
   Replaced with a before/after snapshot.

## 3. Item 7 — test-state leakage, audited and closed

**Measured before:** running the existing suites dirtied **2 tracked files** and created
untracked run files in the worktree.

Three independent causes, all found by isolating suite-by-suite rather than guessing:

| # | Cause | Fix |
|---|---|---|
| 1 | `chat_log.py:22` built `STATE_DIR` from `__file__`, ignoring `OCTOPUS_STATE_DIR` | honor the env var, same default |
| 2 | `criticality_v2.py:23` built `_TRACE` the same way | same |
| 3 | `test_cognitive_unify.py` used `harness.run()` for reporting but **never called `harness.setup()`** — the only such suite among its peers, so neither `OCTOPUS_STATE_DIR` nor `live_state_guard` was ever active | add `harness.setup("cognitive-unify")` |

Causes 1 and 2 are the exact class `harness.py`'s own `VQ-LIVE-STATE-GUARD-001` comment
warns about. The convention they now follow —
`Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))` — is verbatim what
`run_store.py:34`, `memory_formation.py:25`, `brain_pulse.py:21` and `math_control/spine.py:16`
already do. **Defaults are byte-identical to the previous paths**, so production behavior is
unchanged when the env var is unset.

**Measured after: 0 tracked files dirtied by the full suite run.**

Cause 3 carried real risk of breaking a green 11/11 suite, so it was applied and then
verified empirically rather than assumed: still **11/11**, and the leak closed.

Untracked run-store artifacts still appear under `_ops/state/cognitive/runs/`. They are
untracked, excluded from the commit, and **not deleted** (owner instruction + vault
constitution). Three exist: `run_9523f5b935d2`, `run_8b557e499bf9`, `run_44a9eb93f29f`.

## 4. Item 9 — regression suites

| Suite | Result |
|---|---|
| `test_run_store_concurrency` | **4/4** |
| `test_run_failure_lifecycle` (new) | **7/7** |
| `test_cognitive_events` | **10/10** |
| `test_cognitive_unify` | **11/11** |
| `test_miniapp_gateway` | **49/49** |
| `test_octopus_mcp_search` | **4/4** |

**85 checks, zero failures.** Tracked-state leakage: **zero**.

⚠️ **Honesty note on the MCP suite.** It reports in a different format (`OK … 4/4`), not
harness's ✅ lines — an automated ✅-counter scored it `pass=0 fail=0`, which would have been
a green-by-absence. Its real result is 4/4. But this worktree's copy is the **stale**
4-check version; the live branch's commit `634cd76` says "search test now 6/6". This suite
is **not** authoritative here.

## 5. Items 1-3 (`server/discover`) — BLOCKED, not attempted

`_ops/octopus_mcp/server.py` here is the **411-line** pre-HTTP-transport version. The live
branch's is **635 lines**, carrying two commits this branch lacks:

- `5899ed5` — manual stateless Streamable-HTTP transport (13/13 tests)
- `634cd76` — rg engine fix for spaced/empty queries (6/6)

Implementing `server/discover` in `_handle()` here would edit a stale base. Both branches
would then have modified the same function from a common ancestor, producing a genuine
merge conflict — and resolving it wrongly would silently drop the live tree's HTTP transport.

**Correction to an alarm I raised mid-batch:** I first said a merge would "regress the live
tree." That was wrong for a proper 3-way git merge — git keeps their side for files this
branch never touched, so the `run_store` fix merges cleanly *because* `server.py` was left
alone. The danger is specifically in editing `server.py` from the stale base.

The spec research is done and captured in `TDR-MCP-ADAPTER-HEADERS.md` (schema, error code
`-32022`, dual-era rules). Only the code change is blocked. It needs the branch brought
current first — an owner decision, since it means merging 293 commits / 1880 files into this
branch.

**Design finding worth recording now:** `server/discover` must **not** advertise
`2026-07-28` in `supportedVersions`. This server implements none of the modern revision
(no `_meta` version handling, no MRTR, no `resultType`, no `subscriptions/listen`). Per the
spec's compatibility matrix, a truthful `DiscoverResult` listing only the versions actually
served (`2025-06-18`, `2025-03-26`, `2024-11-05`) is what lets a dual-era client fall back
correctly. Claiming modern support would break era detection — the probe would report a
modern server that then fails every modern request.

## 6. Boundaries respected

- ARMED **OFF**, PWM **OFF** — untouched.
- No PolicyGate, Ledger, owner-verdict or `durable_journal` semantics touched.
- No DBOS/Postgres, no token streaming, no SSE redesign, no O(n) optimization, no
  crash-resume wiring, `initialize` not removed — all per the DO-NOT list.
- No dependency added (`os`, `contextlib` are stdlib).
- No live-tree write. No deletion. No push.
- `git add` with **explicit paths only**.
- `run_all.py` not touched (WORKLOCK-reserved **and** 16 commits stale here).
- Single sequential session, no subagents, no fan-out.

## 7. Rollback

Four modified files, all one-concern edits, no state migration, no schema change:

```bash
git revert <this-commit>     # or, per file:
git checkout HEAD~1 -- _ops/owner_console/collaborator.py
```

- `collaborator.py` — `handle()` reverts to the single function; public signature never
  changed, so callers are unaffected either way.
- `chat_log.py` / `criticality_v2.py` — one-line path resolution each; defaults identical to
  pre-change, so reverting is a no-op in production.
- `test_cognitive_unify.py` — removing `harness.setup()` restores prior (leaky) behavior.
- New test file is additive; deleting it changes nothing else.

Verified rollback pattern in the previous batch (file checkout → old behavior returns →
checkout back → fix returns) applies unchanged here.

## 8. Gate

L3 is **not** started. Two of its steps are blocked or changed by §1:

1. **`run_all.py` registration** — 16 commits stale here; editing it would conflict, and it
   is WORKLOCK-reserved regardless.
2. **"Merge the approved branch into the live tree"** — the live tree is on
   `rescue/octopus-live-tree-20260821`, not `main`, and its working tree is continuously
   dirty from the running organism. This is a materially different merge than the
   authorization assumed.

Per the owner's own contingency — *"if the next batch cannot complete promptly, merge the
already-verified run_store event-loss fix separately"* — the data-integrity fix is ready and
conflict-free (zero commits touch `run_store.py` on the live branch).
