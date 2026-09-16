---
type: migration
project: ZIMAN
status: proposal
updated: 2026-07-12
---

# MIGRATION MAP — to OLP-1 (no automatic moves)

## Principle
**Improve, don't rewrite. No file moves without owner batch approval.**

## Proposed target (additive folders already created)
```
Ziman Galerry/
├── 00-Control/          ✅ created (STATUS.md)
├── 01-Identity/         ✅ created
├── 03-Offering/         ✅ created (CATALOG.md)
├── 05-Growth/           ✅ created (Experiments/)
├── 08-Memory/           ✅ created (policy + ledger + candidates)
├── 09-Agents/           ✅ created (CONSTITUTION.md)
├── 10-Interfaces/       ✅ created (OCTOPUS-ADAPTER.md)
├── content/             keep
├── control-brain/       keep (or pointer to _code later)
├── ziman-agent/         keep
├── contracts/           keep
├── docs/                keep until links migrated
└── (legacy root md)     keep until batch move
```

## Suggested future batch moves (NOT executed)
| Current | Future | Risk |
|---|---|---|
| PROJECT.md | 00-Control/PROJECT.md | wikilinks/canvas |
| MANIFEST.yaml | 00-Control/MANIFEST.yaml | agent loaders |
| DecisionLog.md | 00-Control/DECISION-LOG.md | low |
| VERDICT_QUEUE.md | 00-Control/VERDICT-QUEUE.md | low |
| Business-Zeiman.md | 02-Domain/ or 01-Identity | medium |
| content/* | 05-Growth/Content/ | medium |
| control-brain + ziman-agent | stay or `_code/` with pointer | high — code paths |

## Validation before any move
1. Link check (Obsidian + canvas)
2. ziman-agent vault.notes paths
3. control-brain projects.yaml workdir
4. Owner approval in VERDICT_QUEUE
