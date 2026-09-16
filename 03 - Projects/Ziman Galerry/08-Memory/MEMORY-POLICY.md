---
type: policy
project: ZIMAN
status: active
updated: 2026-07-12
---

# MEMORY-POLICY

## Source of truth
- **Event Ledger** (append-only) under `08-Memory/Event-Ledger/`
- Graph / vector = derived indexes only
- Markdown = human-readable view

## Write path
1. Agent creates **candidate** (`08-Memory/Candidates/`)
2. Schema + evidence + duplicate + privacy checks
3. Memory Curator gate
4. Human review when material
5. Activate or reject
6. Rebuild indexes

## Prohibited in memory
- secrets, API tokens
- PayID / payment identifiers
- customer addresses / raw private chats
- registration identifiers
- unsupported model conclusions as fact

## Classes
| Type | Purpose |
|---|---|
| episodic | experiments & operations |
| semantic | evidence-backed product/market facts |
| procedural | verified playbooks only |
| governance | decisions, approvals, policies |

## ZimanLeg
`memory_candidate()` emits provisional proposals only — never canonical write.
