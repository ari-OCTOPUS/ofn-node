---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave1, threat]
---

# WAVE1-THREAT-MODEL

| threat | control | residual |
|---|---|---|
| Prompt / task cross-contamination | Visibility filter: private row requires matching `task_id`; `shared=true` is the only cross-task contract. Cortex prompt injection is **out of canary scope**. | Existing `_recall_for_goal` still searches MemoryStore without this filter until a later rollout patch. |
| Stale-memory influence | `occurred_at`/`recorded_at` must be ≤ decision_time; missing timestamps ineligible. | Stale-but-past records still eligible; TTL is MemoryGate’s job, not this reader. |
| Task/run identity confusion | `task_context.resolve` only: caller, explicit map, or matching `OCTOPUS_TASK_ID`+`OCTOPUS_RUN_ID`. Unresolved → `task_id=""` / unattributed. | Callers that lie about task_id are not cryptographic; this is a process contract. |
| Secret leakage | Fixture has no live secrets. WriteGuard rejects store writes. Search returns whole `text` of visible rows — do not log raw production content. | If production rows contain secrets, retrieval would surface them to the owning task. |
| Recursive self-conditioning | No write-back of retrieved text into memory. `executable=false` on T49. Prompt injection off. | T49 already runs in organism; this canary does not add a learning loop. |
| Unbounded retrieval | `MAX_HITS=8`, kind filters, no recursive search. | A caller looping retrieve is not rate-limited beyond process norms. |
| Corrupted records | Bad timestamps skipped. JSON fixture is well-formed. | Corrupt production sqlite is not parsed by this path (db not opened). |
| Read path triggering writes | `FixtureStore.write/delete/compact` raise; fingerprint compared before/after. Closeout hashes `memory.db` and `cost-receipts.jsonl`. | T49 still writes pulse JSON (`memory-read-latest.json`) as before Wave 1 — telemetry, not MemoryStore. This canary does not call `tick_from_spine`. |
| Memory unavailable | `locked` / `killed` / empty hits → skipped/unattributed receipt, no crash, no fallback guess. | Callers must treat empty as empty. |

Kill switch: overlay or `_ops/STOP-WAVE1-READ` stops Wave 1 retrieve. `STOP-ORGANISM` stops the organism loop (existing). Shadow tests do not honor production STOP files (TEST_ONLY isolation).
