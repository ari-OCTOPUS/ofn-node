# NEXT-ACTION — status APPLIED (2026-08-23)

## Status

| Step | Status |
|---|---|
| Step 1 — read-only audit | **PASS** → `AUDIT.json` |
| Step 2 — four TDRs | **PASS** → `TDR-*.md` |
| L2 — fail_run + leakage isolation | **PASS** → `EXECUTION-RECEIPT-FAILRUN-AND-LEAKAGE.md` |
| L2 — `server/discover` | **PASS** → commit `d883867` |
| L3 — central test registration | **DONE** → commit `e808c3f` |
| L3 — merge to live tree | **DONE** — fast-forward `bf46ffe` → `e808c3f` |
| L3 — restart consumer services | **DONE** — gateway + center |
| L3 — post-restart smoke / health / concurrency | **PASS** — 94 checks |
| **Overall** | **APPLIED** (one caveat, below) |

Live branch: `rescue/octopus-live-tree-20260821` @ **`e808c3f`** · nothing pushed to any remote.

## Runtime truth

**The fixes are running.** Not merely committed.

| Service | Before | After | Started |
|---|---|---|---|
| `miniapp_gateway.py` | 12220 | **14924** | 19:22:11 |
| `center.py` | 2296 | **32604** | 19:22:41 |

`cortex` / `organism` / `live` deliberately untouched — they never import
`event_stream`/`run_store`, and the only changed files they could load have byte-identical
production defaults. Restarting them would have violated "restart *only* services that load
the changed modules."

Smoke on the restarted gateway: `/api/runs/*` → 403 `owner_auth_required` (handler alive,
gate closed), `/` → 200. Post-restart suites on live code: **94 checks, zero failures**.

### The one caveat

`server/discover` is proven working on live code (fresh stdio probe returns v1.2.0 with the
correct version list). But the long-running MCP server **pid 1376** predates the change and
still runs the old dispatcher. It was not killed on purpose — an MCP stdio server is a child
of its client, so its restart is that client reconnecting.

- New MCP client connections → **APPLIED**
- The existing pid-1376 session → **MERGED_NOT_ACTIVE** until it reconnects

## What is now live

1. **Event loss stopped.** `run_store.append_event` was an unguarded read-modify-write.
   Proven pre-fix: 96 concurrent appends → 67 unique sequences **and 2 events destroyed**
   (interleaved writes corrupt lines; `_read_jsonl` silently swallowed the
   `JSONDecodeError`). Cross-process file lock now covers the whole critical section
   including the write.
2. **Orphaned runs fixed.** `fail_run()` had zero production callers, so any exception
   escaping `handle()` left a run `ACTIVE` forever — a dead conversation shown as
   in-progress. Wired at the lifecycle boundary; the exception still re-raises.
3. **False success fixed.** `MODEL_FINISHED` reported `COMPLETED` even when the model call
   had failed. Now `FAILED`, while the run still completes (a stub reply was delivered).
4. **`server/discover`** implemented additively; `initialize` untouched and pinned by four
   regression checks.
5. **Test-state leakage** closed — three independent causes; 2 tracked files dirtied → 0.
6. **Three suites registered** in `run_all.py`; previously green but never executed centrally.

## Open items for the next agent

1. ~~**`initialize` malformed-params DoS**~~ — **FIXED** 2026-08-23, commit `f9f294b`
   (ff-merged). Auditing it found **three** sites of the same class, not one: `_handle`
   (non-dict message), `initialize`, and `tools/call`. `main()`'s stdio loop now also wraps
   `_handle` in `try/except`. `initialize` is hardened, **not** weakened — byte-identical for
   every valid input, pinned by a regression test. Failing-first proof reproduced actual
   process death. Details: `EXECUTION-RECEIPT-MALFORMED-DOS-2026-08-23.md`.
   Residual: MCP server **pid 1376** predates the fix and is unhardened until its client
   reconnects — low exposure, since the DoS is reachable only by the connected client over
   its own stdio pipe, never over the network.
2. **Two TDR questions still unanswered by the owner:**
   - Is crash-mid-turn resume a real requirement, or theoretical? Gates
     `TDR-DBOS-RUNSTORE.md` option C (wiring `durable_journal` into chat runs).
   - Is live token-level streaming wanted in the mini-app? Gates `TDR-SSE-O-E4.md` option A
     (rename to poll — recommended) vs option B (build real streaming). Note option B would
     activate the `run_store` race that was just fixed, and the MCP spec itself has since
     **removed** `Last-Event-ID` resumability — a directional signal favouring option A.
3. **`TDR-SSE-O-E4.md` open defect stands:** `/api/runs/{id}/events` is a poll wearing a
   `text/event-stream` Content-Type. Harmless today because `app.js` uses XHR, but a
   spec-compliant `EventSource` would get infinite duplicate redelivery. Option A is ~10 lines.
4. **`TDR-OTEL-MAPPING.md` counter-proposal not acted on:** 19 of 25 declared event types
   have zero production emitters, and `MODEL_STARTED` is test-only, so model latency is
   unmeasurable. Wiring it is ~15 lines and needs no dependency.

## Rollback

```bash
git revert --no-edit e808c3f d883867 1994daa 9f5169c cc0ceee
powershell -File F:\backup\_ops\RESTART-PROCESS.ps1 gateway
powershell -File F:\backup\_ops\RESTART-PROCESS.ps1 center
```

Pure code, no state migration, no schema change, no dependency. Pre-restart PIDs: gateway
12220, center 2296. Full detail in `EXECUTION-RECEIPT-APPLIED-2026-08-23.md`.
