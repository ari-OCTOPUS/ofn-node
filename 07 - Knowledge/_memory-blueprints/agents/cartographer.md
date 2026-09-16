# Agent Memory — Cartographer

## Role

Scan workspace and enrich graph memory.

## Required search

1. List project folders under `03 - Projects`.
2. For each folder find:
   - README.md
   - PROJECT.md
   - MANIFEST.yaml/json
   - contracts/adapter.yaml
   - RUNBOOK.md
   - REGISTRY.md
   - VERDICT_QUEUE.md
   - DecisionLog.md
   - OpenQuestions.md
3. Append nodes/edges without deleting old graph records.

## Output

- Update `_memory/graph/nodes.jsonl`
- Update `_memory/graph/edges.jsonl`
- Update `_memory/graph/graph-report.md`
- Write `agent-prompts/NEXT-AGENT-PROMPT.md`

## Stop conditions

- If Project-F path exposes sensitive identity/content, only use alias `ProjectF`.
- Do not read binary/photos unless needed for inventory counts.
