# Phase 3 — Mandatory Memory Read

MEMORY_GATE_IMPLEMENTATION: PASS
LIVE_DATABASE_MODIFIED: false
LIVE_RUNTIME_MODIFIED: false

## Wiring

- Types: `MemoryQuery`, `MemoryReadReceipt`, `DecisionEvidenceBundle` in `ofn/organism/memory/gate.py`
- Call sites: `life_cycle.tick`, `AskCascade.ask`, school `C-memory`, eval via ask
- Empty successful `SELECT` from `episodes WHERE created_at <= decision_time` counts as a read
- `futures` is never queried as episodic evidence
- Failed receipts are not inserted (`CHECK (future_use_count = 0)`)
- Fail-closed: `MemoryUnavailable` on tick; ask returns `route=memory_gate` / `NEEDS_OWNER`

## Live schema guard

`connect(/opt/octopus/lab/lab-data/organism.db)` raises `live_schema_mutation_blocked` unless `OCTOPUS_ALLOW_LIVE_SCHEMA=1`.

Live DB still has no `memory_read_receipts` / `wan_fetches`.

## HTTP flags (default OFF)

- `OCTOPUS_GET_PURE=1` — GET skips persist/enrich/public-status writes
- `OCTOPUS_REQUIRE_LAN_TOKEN=1` + `OCTOPUS_LAN_TOKEN` — 401 without header `X-Octopus-Token`

Activating these on the running process requires Owner Gate restart.

## Tests

See `ofn/organism/tests/test_memory_gate.py` (tempfile DBs only).
