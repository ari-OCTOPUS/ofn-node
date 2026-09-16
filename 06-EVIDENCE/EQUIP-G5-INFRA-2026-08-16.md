# EQUIP-G5-INFRA Evidence Report

**Date:** 2026-08-16
**Group:** G5 -- Infrastructure (self-healing runtime)
**Wave:** D (Implementer 8, D2)
**Branch:** `equip/g5-infra-20260816`
**Verdict:** PASS

---

## Executive Summary

G5-INFRA delivers a vertical slice for reproducible and self-recovering runtime:
service inventory with dependency graph, MCP HTTP health/readiness/liveness
three-tier validation, constitution invariant checking, and configuration
schema validation. All 38 tests pass (19 new + 13 G5-A HTTP + 6 G5-A search).
Zero new pip dependencies. Zero secrets in output. Zero WORKLOCK violations.

## G5-A Verification (parallel agent commits c374867..cfb4849)

G5-A performed 4 commits on this branch before G5-INFRA started:

| Commit | What | Verdict |
|---|---|---|
| `c374867` | MCPv2 baseline lock (evidence + baseline txt) | PASS -- baseline captured correctly |
| `5899ed5` | Stateless Streamable-HTTP transport on server.py (+209 lines) | PASS -- 13/13 tests, zero new deps |
| `634cd76` | Fix rg engine on spaced/empty queries | PASS -- search 6/6 |
| `cfb4849` | Evidence registry (`_ops/state/registry/evidence_index.jsonl`) | **WORKLOCK VIOLATION** (see below) |

### G5-A Test Verification (own eyes)

```
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_http_stateless.py
=> OK test_octopus_mcp_http_stateless: 13/13

PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_search.py
=> OK test_octopus_mcp_search: 6/6
```

### server.py Constitutional Verification

- Tool count: 5 (list_tree, read_file_slice, hash_file, search_hybrid, propose_action)
- Read-only tools: 4 (no write-mode open, no os.system, no destructive subprocess)
- Write tool: propose_action (writes only to `_octopus/queue/pending/`, never executes)
- HTTP transport: stateless, no Mcp-Session-Id issued or accepted, no sessions
- Health/Readiness split: /healthz (liveness) and /readyz (readiness) separate
- DNS-rebinding guard: foreign Host header returns 403
- New dependencies: zero

### WORKLOCK Violation (OBSERVATION, not actioned)

Commit `cfb4849` committed `_ops/state/registry/evidence_index.jsonl` under
`_ops/state/**` which is explicitly WORKLOCK-protected ("never commit _ops/state/**").
This file should have been placed elsewhere (e.g., `06-EVIDENCE/`). The commit is
already on the branch; per instructions, this is documented as an observation.
G5-INFRA did NOT follow this pattern and did NOT commit any files under `_ops/state/**`.

## What G5-INFRA Implemented

### New Files

| File | Purpose |
|---|---|
| `_ops/infra/__init__.py` | Package marker |
| `_ops/infra/service_inventory.py` | Service discovery + dependency graph (organism, cortex, live, center, gateway, mcp_server) |
| `_ops/infra/mcp_http_health.py` | Three-tier health check harness (liveness/readiness/service/constitution) |
| `_ops/tests/test_g5_infra_selfheal.py` | 19 tests covering all vertical slice capabilities |

### No Files Modified

server.py was NOT modified (constitutionally read-only per megaprompt; G5-A already
made the needed changes). No dependencies added. No WORKLOCK files touched.

## Discovered Architecture

### Service Inventory (6 services)

| Service | Port | Critical | Watchdog | Restart |
|---|---|---|---|---|
| organism | 8771 | Yes | organism-watchdog.ps1 | RESTART-PROCESS.ps1 organism |
| cortex | 8772 | Yes | cortex-watchdog.ps1 | RESTART-PROCESS.ps1 cortex |
| live (cockpit) | 8773 | No | live-watchdog.ps1 | RESTART-PROCESS.ps1 live |
| center (tg poller) | -- | Yes | -- | RESTART-PROCESS.ps1 center |
| gateway (miniapp) | 8774 | No | miniapp-watchdog.ps1 | RESTART-PROCESS.ps1 gateway |
| mcp_server | dynamic | No | -- | client-managed |

### Dependency Graph

organism -> cortex -> live -> center -> gateway -> mcp_server

### Deployment Infrastructure

- `RESTART-PROCESS.ps1`: PID-verified restart (kills old, launches new, confirms new PID)
- `deploy-to-live.ps1`: Staged reversible deploy (dry-run default, STOP-ORGANISM check, snapshot)
- `restore-drill.ps1`: Monthly backup restore test (rclone from offbox)
- `octopus-health-check.ps1`: Read-only diagnostic (disk, processes, ports, scheduled tasks)
- Watchdogs: 5-min scheduled tasks via schtasks, each with STOP marker off-switch
- Activation flags: 15 runtime flags in `_ops/ACTIVATION-*.flag` (untracked, owner-controlled)
- Kill switches: STOP-ORGANISM (not present = organism halted), HALT-ALL, per-limb STOP markers

### Gaps Identified (not in this slice, documented for next)

1. **No Python-based health watchdog for MCP HTTP server** -- server is client-managed,
   not a daemon; no watchdog revives it if used as persistent service.
2. **No Pydantic Settings or schema validation** for runtime config -- config is YAML
   parsed ad-hoc. A typed schema would catch drift.
3. **No graceful shutdown for MCP HTTP on Windows** -- ThreadingHTTPServer.shutdown()
   is unreliable when called mid-test; daemon_threads + server_close() works but is
   not clean. (Already covered by G5-A test which shuts down once at end.)
4. **No Docker/K8s** -- single-node Windows deployment; containerization would be a
   separate owner decision with significant effort.
5. **No resource limits** (CPU/RAM/disk) for services -- relies on OS defaults.

## Test Results

### New G5-INFRA Tests

```
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g5_infra_selfheal.py
=> OK test_g5_infra_selfheal: 19/19
```

19 tests across 7 categories:
- Service inventory (6): catalog completeness, dependency order, typed output,
  JSON roundtrip, summary generation
- Health/Readiness/Liveness (3): healthz liveness, readyz readiness, endpoint separation
- Constitution (3): 5 tools, read-only enforcement, propose_action presence
- Service call (1): RPC over HTTP (tools/call:list_tree)
- DNS-rebinding (1): foreign Host -> 403
- Config schema (3): policy.yaml keys, .mcp.json existence, activation flags
- Integration (2): full health check report, JSON serialization

### G5-A Regression Tests

```
test_octopus_mcp_http_stateless.py: 13/13 (unchanged)
test_octopus_mcp_search.py: 6/6 (unchanged)
```

### Chain Test Summary

| Group | Tests | Status |
|---|---|---|
| G2 (Memory) | 49/49 | PASS |
| G3 (Perception) | 77/77 | PASS |
| G4 (Coding) | 111/111 | PASS |
| G5-A (MCP HTTP+Search) | 19/19 | PASS |
| G5-INFRA (Self-Heal) | 19/19 | PASS |
| G6 (Observability) | 53/53 | PASS |
| G7 (Identity) | 82/82 | PASS |
| G8 (Containment) | 81/81 | PASS |
| G1 (Orchestration) | 50/50 | PASS |

## Security and Quality Scan

| Check | Result |
|---|---|
| Secrets/credentials in code | CLEAN -- zero matches |
| Unsafe deserialization (pickle/yaml.load) | CLEAN -- zero matches |
| Shell injection (os.system/eval/exec) | CLEAN -- only in inspection comments |
| Outbound network calls | CLEAN -- only localhost HTTP |
| Unbounded loops | CLEAN -- no while True or large ranges |
| Environment variable access | CLEAN -- zero matches |
| Path traversal | CLEAN -- _resolve() guards all paths |
| Prompt injection | N/A -- no LLM prompts in infra module |
| Privileged container | N/A -- no containers in this slice |
| Mutable image tag | N/A -- no containers |
| New dependencies | ZERO -- only stdlib |

## WORKLOCK Compliance

| File | Status |
|---|---|
| `_ops/tests/run_all.py` | NOT TOUCHED |
| `_ops/wiring.py` | NOT TOUCHED |
| `_ops/telegram_center/center.py` | NOT TOUCHED |
| `_ops/orphan_scan.py` | NOT TOUCHED |
| `_ops/state/**` | NOT COMMITTED |
| `ledger.jsonl` | NOT TOUCHED |
| `nervous-system/*-data.js` | NOT TOUCHED |
| `_memory/HEARTBEAT.md` | NOT TOUCHED |

## Rollback Plan

All G5-INFRA work is additive (new files only). No existing files were modified.
Rollback: delete the 4 new files and revert the 2 commits on this branch.
No migration needed. No database changes. No state changes.

## Reproduce Commands

```bash
git checkout equip/g5-infra-20260816

# G5-A tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_http_stateless.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_search.py

# G5-INFRA tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g5_infra_selfheal.py

# Service inventory (live discovery)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/infra/service_inventory.py

# Health check (starts ephemeral server)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/infra/mcp_http_health.py
```

## Evidence Paths

- `06-EVIDENCE/EQUIP-G5-INFRA-2026-08-16.md` (this file)
- `06-EVIDENCE/EQUIP-G5A-MCPV2-BASELINE-2026-08-16.md` (G5-A STEP1)
- `06-EVIDENCE/EQUIP-G5A-MCPV2-STATELESS-HTTP-2026-08-16.md` (G5-A STEP2)
- `06-EVIDENCE/EQUIP-G5A-MCP-SEARCH-RG-FIX-2026-08-16.md` (G5-A STEP3)
- `_ops/tests/_baselines/mcpv2-baseline.txt` (G5-A baseline lock)

## Recommended Next Step

Wave D independent scan (MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md)
by a separate agent, as required for second-group-of-wave implementations.
