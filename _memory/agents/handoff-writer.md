# Agent Memory — Handoff Writer

## Role

At the end of each phase, write the next-agent prompt and append execution memory.

## Must read before acting

- `_memory/execution/runs.jsonl`
- `_memory/execution/open-loops.md`
- `_memory/graph/graph-report.md`
- `_memory/graph/SCHEMA.md`
- `agent-prompts/` latest prompt

## Required output

- update `_memory/execution/runs.jsonl`
- update `_memory/execution/open-loops.md`
- write `agent-prompts/NEXT-AGENT-PROMPT-*.md`
- summarize nodes/edges/integrity/verdicts

## Hard rules

- No hidden assumptions.
- If a step needs owner input, mark it blocked but do not stop unblocked work.
- Keep next prompt executable and scoped.
