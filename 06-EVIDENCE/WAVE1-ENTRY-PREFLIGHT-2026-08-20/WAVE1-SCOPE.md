---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave1, preflight]
---

# WAVE1-SCOPE — read-only memory (bounded)

Wave 0 baseline `9bc506f` is frozen. This Wave 1 scope is **read-only retrieval with task isolation**. It is not prompt injection into cortex and not memory.db mutation.

## What “read-only memory” means

A caller that already possesses a real `task_id` may retrieve records **visible to that task** (same `task_id`, or `shared=true` under an explicit shared-memory contract). Retrieval emits a v2 read receipt. The store fingerprint must not change.

## Allowed

- `query_experiments`, `get_pending_hypotheses`, `search_vault`, `by_id`
- Temporal filter: `occurred_at` and `recorded_at` ≤ decision_time (future rows never leak)
- TEST_ONLY fixture / snapshot copies
- Read receipts to `06-EVIDENCE/WAVE1-ENTRY-PREFLIGHT-2026-08-20/wave1-shadow-receipts.jsonl`
- Kill via `STOP-WAVE1-READ` (overlay or `_ops/STOP-WAVE1-READ`) or `STOP-ORGANISM`

## Forbidden

- insert / update / delete / compact / vacuum of MemoryStore / `memory.db`
- rewrite of `cost-receipts.jsonl` or Wave 0 artifacts
- fabricating `task_id` from PID, timestamp, capability, or model name
- returning task B private rows to task A without `shared=true`
- injecting retrieved text into cortex prompts (out of this Wave 1 canary)
- paid calls

## Processes / modules

| role | path | this canary |
|---|---|---|
| API | `_ops/nervous_recovery/wave1_readonly.py` | used |
| lock | `_ops/state/wave1/lock.json` | file flag; organism hook **off** |
| T49 telemetry | `_ops/memory_read_loop.py` (already live) | unchanged |
| decision recall | `_ops/goal_action_bridge.py` `_recall_for_goal` | **not patched** |
| writers | `memory/gate.py`, `write_gate_enforcer.py` | not invoked |

## Data sources

- Canary/preflight: deterministic fixture in `default_fixture()` (12 rows)
- Production memory.db: **not opened** by this path
- Spine live DB: **not opened** by this path

## Limits

- `MAX_READS_PER_CYCLE = 3` (T49 already uses 3; Wave 1 sample may issue more in TEST_ONLY)
- `MAX_HITS = 8` per retrieve
- `TIMEOUT_MS = 250` (contract; fixture retrieve is in-process)
- Canary duration: one sidecar pass (seconds), not a live soak of organism
