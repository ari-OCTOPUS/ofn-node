# Graph Memory Index

> Seed graph for multi-agent memory/search.

Files:

- `nodes.jsonl` — graph nodes.
- `edges.jsonl` — graph edges.
- `graph-report.md` — human-readable report.

## Search protocol

Before any agent acts:

1. Load target node.
2. Load local docs from node path.
3. Load outgoing/incoming edges depth 2.
4. Load gates/verdict requirements.
5. Execute only if not hard-gated.
6. Append memory event.

## Seeded entities

- ArchitectOps
- Accounting
- LeadPainting
- Ziman
- ProjectF
- Mining
- CryptoEtoro
- NBB_CP
- FourD
- VaultScanner

