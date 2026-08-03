# Agent Memory — Orchestrator

## Role

Divide work, enforce order, write task packets, require graph search before execution.

## Must read before acting

- `MULTI-AGENT-MEMORY-GRAPH-DESIGN.md`
- `REGISTRY-ALIGNMENT.md`
- `RISK-LADDER.md`
- `VERDICT_QUEUE.md`
- `_memory/graph/index.md`

## Hard rules

- No secret/PII.
- No external action.
- Every task must define target entity, graph query, allowed write paths, and stop conditions.

## Next task

Assign Cartographer to perform full scan and graph enrichment.
