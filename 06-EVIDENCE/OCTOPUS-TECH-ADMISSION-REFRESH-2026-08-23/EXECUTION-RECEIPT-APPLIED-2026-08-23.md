# EXECUTION RECEIPT — status: **APPLIED**

**Date:** 2026-08-23, Sydney local · **Authority:** owner verdict "CONTINUE L2, THEN LIMITED L3"
**Branch:** `rescue/octopus-live-tree-20260821` (the branch the live tree runs from)

This receipt exists because *"nothing counts as applied without a receipt"*. The previous
receipt (`EXECUTION-RECEIPT-L3-MERGE.md`) recorded status **`MERGED_NOT_ACTIVE`**: code on
disk, nothing restarted. **This one records `APPLIED`** — consumer services restarted, and
smoke run against the code those services actually loaded.

## 1. Commit IDs

| Commit | Content | How it landed |
|---|---|---|
| `cc0ceee` | run_store cross-process append lock + 4 TDRs | cherry-pick (earlier batch) |
| `9f5169c` | MCP 2026-07-28 spec verification | cherry-pick |
| `1994daa` | fail_run wiring + test-state leakage isolation | cherry-pick |
| `bf46ffe` | L3 merge receipt + runtime truth | direct commit |
| **`d883867`** | **`server/discover` additive for stdio** | fast-forward |
| **`e808c3f`** | **central `run_all.py` registration of 3 suites** | fast-forward |

**Merge ID:** none needed this round — **fast-forward** from `bf46ffe` → `e808c3f`.
The working branch `claude/mcp-server-discover` was cut *from* live HEAD, so the
293-commit divergence that forced cherry-picking last time did not exist. `--ff-only`
succeeded with zero conflicts.

How the stale-base blocker was cleared: the earlier branch's commits were already
replicated on the live branch, so it held nothing unique (verified by content diff — only
the three evidence files differed). The worktree was therefore moved to a fresh branch at
live HEAD, giving current code (`server.py` 635 lines, not the stale 411) at zero merge cost
— in the same worktree, no fan-out.

## 2. Services restarted

Restarted with `_ops/RESTART-PROCESS.ps1` (owner-authored; compares PIDs, so "restarted" is
a fact, not a claim), **not** raw kills:

| Service | Before | After | Started |
|---|---|---|---|
| `miniapp_gateway.py` | pid **12220** (16:18:04) | pid **14924** | 19:22:11 |
| `telegram_center/center.py` | pid **2296** (08:38:27) | pid **32604** | 19:22:41 |

`center` reported **1 supervisor loop** — the check that prevents two pollers on one bot
token (a 409 incident class this repo has hit before). No stray `STOP-*` markers remain
(`STOP-TG-CENTER`, `STOP-CORTEX`, `STOP-ORGANISM`, `RESTART-REQUESTED` all clear) — a stray
marker once kept the system down for 30 minutes.

### Deliberately NOT restarted

- `cortex.py` (24760), `organism.py` (29020), `live/server.py` (6024) — the instruction was
  "restart **only** services that load the changed modules." These never import
  `event_stream`/`run_store` (verified: only three files in the tree do). The only changed
  files they could touch are `chat_log.py` / `criticality_v2.py`, whose production defaults
  are **byte-identical** to before, so a restart would buy nothing and would violate "only".
- `octopus_mcp/server.py` (pid 1376, started 15:38) — see §4.

## 3. Tests

**Post-restart, from the live tree, against live code:**

| Suite | Result |
|---|---|
| `test_run_store_concurrency` | **4/4** |
| `test_run_failure_lifecycle` | **7/7** |
| `test_mcp_server_discover` | **18/18** |
| `test_cognitive_events` | **10/10** |
| `test_miniapp_gateway` | **49/49** |
| `test_octopus_mcp_search` | **6/6** |

**94 checks, zero failures.** (Pre-merge in the worktree: 105 checks including
`test_cognitive_unify` 11/11.)

**Gateway smoke on the restarted process:**

```
GET /api/runs/run_smoketest         -> HTTP 403 owner_auth_required
GET /api/runs/run_smoketest/events  -> HTTP 403 owner_auth_required
GET /                               -> HTTP 200, 4131 bytes
TCP 8774 listening                  -> True
```

The 403s are the meaningful signal: the endpoint `run_store` feeds is alive **and** its
owner-auth gate is closed. Only the reject direction was exercised — the accept direction
needs real owner `initData`, which was not fabricated.

**`server/discover` on live code**, fresh stdio process against `F:\backup\_ops\octopus_mcp\server.py`:

```
resultType   : complete
supported    : ['2025-06-18', '2025-03-26', '2024-11-05']
serverInfo   : {'name': 'octopus-vault', 'version': '1.2.0'}
2026-07-28 advertised? False
```

## 4. Honest limit — one item is still `MERGED_NOT_ACTIVE`

`server/discover` is **proven working on live code** (probe above, spawned from the live
path). But the long-running MCP server **pid 1376, started 15:38**, predates the change and
still executes the old dispatcher.

That process was not killed on purpose: an MCP stdio server is a child of its client, and
terminating it would disrupt that client's session. Its "restart" is the client reconnecting.
So:

- **New MCP client connections → `APPLIED`** (proven).
- **The existing pid-1376 session → `MERGED_NOT_ACTIVE`** until that client reconnects.

Stated rather than glossed, since the whole point of this receipt is that a commit is not an
application.

## 5. Bug found during this batch — by the test, not by review

`server/discover` with a non-dict `params`/`_meta` (e.g. a JSON string) raised
`AttributeError` from `(... or {}).get(...)`. `main()`'s stdio loop calls `_handle` with no
`try/except`, so **one malformed probe would have killed the entire server process** — a
trivial DoS on the exact method every new client calls first. Fixed with explicit
`isinstance` checks before merge.

Recorded, deliberately **not** fixed: `initialize` has the same fragility
(`(msg.get("params") or {}).get("protocolVersion")`). Same DoS shape, pre-existing. Untouched
because the verdict said not to modify the `initialize` path. It should be fixed in a batch
that is allowed to touch it.

## 6. Central test registration

`_ops/tests/run_all.py` — all three new suites registered (`e808c3f`). Until this, they were
green but **never executed by the central sweep**, so a regression in any of them would have
woken nobody. Verified after edit that the file parses and line endings survived
(1643 CRLF, 0 bare LF) — the Edit tool has broken CRLF in this repo before.

## 7. Rollback

```bash
# code only, keeping evidence:
git revert --no-edit e808c3f d883867 1994daa 9f5169c cc0ceee
# then re-run the two restarts to load the reverted code:
powershell -File F:\backup\_ops\RESTART-PROCESS.ps1 gateway
powershell -File F:\backup\_ops\RESTART-PROCESS.ps1 center
```

- No state migration, no schema change, no dependency: every revert is pure code.
- `run_store` storage stays append-only JSONL, readable by old and new code alike.
- `chat_log` / `criticality_v2` defaults are byte-identical to pre-change, so reverting them
  is a no-op in production.
- `collaborator.handle`'s public signature never changed in either direction.
- `server/discover` is additive; reverting restores the prior `-32601` for that method,
  which is still valid legacy behaviour.
- Rollback was verified experimentally in an earlier batch (checkout old → defect returns →
  checkout new → fix returns), not merely documented.

Pre-restart PIDs for reference: gateway **12220**, center **2296**.

## 8. Boundaries

ARMED **OFF**, PWM **OFF** — untouched. No PolicyGate / Ledger / owner-verdict /
`durable_journal` semantics changed. No DBOS, no Postgres, no token streaming, no SSE
redesign, no O(n) optimisation, no crash-resume, `initialize` not removed. No dependency
added. **No deletion** — pre-existing untracked run artifacts left in place. **No push to any
external remote.** `git add` with explicit paths only. Single sequential session, no
subagents, no fan-out.
