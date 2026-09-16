---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, p1]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/01-P1-COMMIT-AUDIT]]"
---

# 06 — P1 runtime

```text
observed_at=2026-08-29T05:31:45Z
method=git_show_plus_procfs_plus_grep
scope=this_host_only
RESTART_PERFORMED=NO
```

## Commit

| Field | Value | Truth |
|---|---|---|
| present locally on 138 | YES `/home/ari/ofn` HEAD | `LIVE_VERIFIED` |
| present on vault git | **NO** | `LIVE_VERIFIED` |
| parent | `68813370c726a1a650a7cb2fb99207c300358db9` | `LIVE_VERIFIED` (was HYPOTHESIS) |
| date | 2026-08-29 09:27:18 +1000 | `LIVE_VERIFIED` |
| subject | feat(cockpit-v2): metadata-only owner approval queue projection | `LIVE_VERIFIED` |
| four files | `ofn/node.py`; `ofn/run.py`; `ofn/adapters/cockpit_v2_read_model.py`; `tests/test_cockpit_v2_owner_queue.py` | `LIVE_VERIFIED` |
| fourth-file justification | test-only; not imported by `ofn.run` | `LIVE_VERIFIED` + `DOCUMENTED` |
| `http_api.py` | unchanged in P1 | `LIVE_VERIFIED` show --stat |

## Symbols on disk

`owner_queue_metadata` at `node.py:2222`; wired in `run.py:322-324`; `data.owner_items` at `cockpit_v2_read_model.py:1574`.

source: grep on 138 · truth: `LIVE_VERIFIED`

## Process

| Field | Value | Truth |
|---|---|---|
| live PID | 1351408 still | `LIVE_VERIFIED` |
| started | 2026-08-27 11:33:39 AEST | `LIVE_VERIFIED` |
| loaded commit | **cannot be a27eb05** (start before commit; P1 sources mtime after start) | `LIVE_VERIFIED` inference-from-time = `CONTRADICTED` if someone claims loaded |
| owner_items from live backend | **NOT_RUN** authenticated V2 (401). Unauthenticated proves auth only. | `NOT_RUN` body / `LIVE_VERIFIED` 401 |
| frontend `queue.js` | reads `data.items` / `queue` only; **no `owner_items`** | `LIVE_VERIFIED` |
| items parity | P1 design: mesh items unchanged; **unproven in this PID** | `DOCUMENTED` design / `NOT_RUN` live |
| instrumentation | production patch has no debug regions; tests may log if env set | `DOCUMENTED` |

```text
P1_REPO_IMPLEMENTED=YES
P1_RUNTIME_LOADED=NO
P1_BACKEND_VISIBLE=NO
P1_FRONTEND_VISIBLE=NO
P1_END_TO_END=NO
```

Restart is **not** authorized here. Activation plan remains `P2-DISCOVERY/10-RUNTIME-ACTIVATION-PLAN.md`. Restart alone still does not render `owner_items`.
