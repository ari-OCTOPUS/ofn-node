# T68 — knowledge afferent

Read-only scanner. Notes were not edited. No paid calls. No fact promotion.

## Pipeline

```text
vault notes (07-Knowledge + dashboard + architecture maps + PROJECT.md)
→ scanner (mtime, prefix-hash, type/tags)
→ document events (bitemporal: occurred_at = source mtime)
→ cognition_inbox burst
→ memory candidates: not auto-upgraded to facts
```

## Metrics (this scan)

| metric | value |
|---|---|
| notes_total | 655 |
| notes_changed_last_hour | 7 |
| frontmatter_valid_ratio | 0.4397 |
| untagged_ratio | 0.4931 |
| stale_notes_ratio (>30d) | 0.6107 |
| knowledge_afferent_events | 655 |
| future_use | 0 |
| fabricated_occurred_at | 0 |
| ineligible_temporal | 0 |

Frontmatter debt is **reported, not bulk-cleaned**.

## Flags / rollback

`_ops/organs/WIRING.json` → `knowledge_afferent: true`. Set false to stop sidecar. `live_organism_hook: false` — organism tick unchanged (no restart).

Ledger: `_ops/state/organs/knowledge-afferent.jsonl`
