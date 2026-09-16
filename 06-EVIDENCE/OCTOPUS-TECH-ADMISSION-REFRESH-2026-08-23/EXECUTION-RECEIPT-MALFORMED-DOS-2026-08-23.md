# EXECUTION RECEIPT — malformed-input DoS hardening

**Date:** 2026-08-23 · **Authority:** owner — *«همون DoS مربوط به initialize رو هم فیکس کن»*
**Commit:** `f9f294b` · **Merge:** fast-forward `9acc502` → `f9f294b` on
`rescue/octopus-live-tree-20260821`

## 1. Scope — one instance asked for, one class found

The owner named `initialize`. Auditing it showed **three** unfixed sites of the same class.
Fixing only the named one would have left the server killable by an identical message and
would have read as done, so the class was fixed.

| Site | Before |
|---|---|
| `_handle` | `msg.get("id")` — `msg` itself could be non-dict |
| `initialize` | `(msg.get("params") or {}).get("protocolVersion")` — the named one |
| `tools/call` | `params = msg.get("params") or {}` — same shape |
| `server/discover` | already fixed in `d883867` |

### Why `or {}` was security theatre

`or` only catches **falsy** values. `""`, `[]`, `0` fall through to `{}` — but `"abc"`,
`[1]`, `42` **pass through unchanged**, and `.get()` on them raises `AttributeError`.
The idiom looked defensive and was not.

### Root asymmetry

The **HTTP** transport already validated `isinstance(msg, dict)` → `400`. The **stdio**
transport — which is what `.mcp.json` actually runs — did not. The guard now lives in
`_handle`, so both transports are covered by one check.

Severity differed by transport: on stdio an exception **killed the process**; on HTTP
`BaseHTTPRequestHandler` absorbed it into a 500 and the server survived. The fatal one was
the transport actually in use.

## 2. Fix

- New `_params_of(msg)` — the only sanctioned way to read `params`; returns `{}` unless it
  is genuinely a dict.
- `_handle` rejects non-dict messages and non-string methods with `-32600 Invalid Request`
  (`id: null`, per JSON-RPC).
- `main()`'s stdio loop wraps `_handle` in `try/except` → `-32603` instead of dying. That
  loop **is** the server's lifetime; no single message may end it. Only the exception
  **type** is returned, never its message (which can carry paths or data).
- `tools/call` with non-dict `arguments` returns an honest `isError` rather than silently
  executing with `{}`.

## 3. `initialize` is hardened, not weakened

The earlier verdict forbade removing or weakening the `initialize` compatibility path.
This change only rejects input that previously **crashed the process**. For every valid
input the behaviour is byte-identical, pinned by
`t_initialize_behaviour_unchanged_for_valid_input`:

- explicit supported version → echoed back unchanged
- unknown version → falls back to the server's own version (prior negotiation behaviour)
- no `params` at all → same fallback

## 4. Failing-first proof

Against the pre-hardening file, the server **crashed**:

```
Traceback (most recent call last):
  File "..._ops\octopus_mcp\server.py", line 709, in <module>  main()
  File "..._ops\octopus_mcp\server.py", line 702, in main      resp = _handle(msg)
❌ malformed->discover->tools (stdio): پاسخ‌ها ناقص‌اند: []  ← zero responses
```

Process death reproduced, not argued.

The decisive test drives a **real subprocess**. An in-process call to `_handle` can never
prove "the server survived", because what died was the process
(`feedback-test-the-pipeline-not-the-unit`).

## 5. Verification

`test_mcp_malformed_hardening.py` — **11/11**, covering 14 malformed shapes that are all
*valid JSON* (so they pass `json.loads` and reach the dispatcher).

Regressions: `mcp_server_discover` 18/18 · `run_store_concurrency` 4/4 ·
`run_failure_lifecycle` 7/7 · `cognitive_events` 10/10 · `cognitive_unify` 11/11 ·
`miniapp_gateway` 49/49 · `octopus_mcp_search` 6/6 — **116 checks, zero failures, zero
tracked-state leakage.**

**Live-code smoke** (post-merge, one process, malformed flood then a real request):

```
responses: 6 | ids: [None, None, None, 1, 2, 'final']
survived flood + served final request: True
final protocolVersion: 2025-06-18
```

Registered in `run_all.py` (parses; CRLF intact, 1644/0).

## 6. Services restarted: none needed

`_ops/octopus_mcp/server.py` is not loaded by `miniapp_gateway` or `center`, so neither was
restarted (`gateway` 14924 and `center` 32604 from the previous batch remain current).

MCP server **pid 1376** predates the change and still runs the unhardened dispatcher. Not
killed on purpose: an MCP stdio server is a child of its client, so its restart is that
client reconnecting.

**Honest severity scoping:** this DoS is reachable only by whoever already speaks to the
server over its stdio pipe — i.e. the connected client itself. It is not network-reachable
and not remotely exploitable, and a well-behaved client never sends `42`. So pid 1376 being
unhardened until respawn is a low-exposure gap, not an emergency. Stated plainly rather than
inflated.

## 7. Rollback

```bash
git revert --no-edit f9f294b
```

Pure code, additive guards only, no state migration, no schema change, no dependency.
Reverting restores the prior crash-on-malformed behaviour. No restart required in either
direction, since no long-lived service loads this module.

## 8. Boundaries

ARMED **OFF**, PWM **OFF**. `initialize` **not** removed. No PolicyGate / Ledger /
owner-verdict / `durable_journal` change. No DBOS, Postgres, token streaming, SSE redesign,
O(n) work, or crash-resume. No dependency. **No deletion.** **No push to any external
remote.** Explicit `git add` paths only. Single sequential session, no subagents.
