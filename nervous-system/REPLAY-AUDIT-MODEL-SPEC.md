---
type: spec
project: OCTOPUS
wave: 6
status: implemented
created: 2026-07-13
updated: 2026-07-13
tags: [octopus, wave-6, replay, audit, rollback, logging]
---

# Replay / Audit Model Spec

## Audit Logger

**Module:** `nervous-system/audit_logger.py`
**Sink:** `_ops/state/action-audit.jsonl`
**Pattern:** Append-only, immutable, structured JSON lines.

### Record Schema

```json
{
  "timestamp": "2026-07-13T12:00:00Z",
  "action_id": "uuid",
  "actor": "owner|agent|system",
  "action_type": "approve|reject|refresh|toggle|...",
  "pre_action_snapshot": {
    "hash": "sha256:16chars",
    "keys": ["budget.remaining", "queue.counts.pending"]
  },
  "proposal_rationale": "...",
  "verdict": "approve|deny|...",
  "verdict_owner": "owner_chat_id",
  "execution_mode": "dry_run|shadow|live",
  "result": "success|failure|cancelled|expired",
  "rollback_class": "reversible|irreversible|requires_manual|unknown"
}
```

## Rollback Classification

| Class | Description | Examples |
|---|---|---|
| **reversible** | Can undo without side effects | refresh data, toggle panel, copy text |
| **irreversible** | Cannot undo; permanent change | approve spending, execute command, delete data |
| **requires_manual** | Needs human intervention to revert | mining start, wallet transfer, telegram message send |
| **unknown** | New/untested action | default until classified |

## Extractor

**Module:** `nervous-system/extract_audit_trail.py`
**Output:** `audit-trail-data.js` → `window.AUDIT_TRAIL_DATA`

### Emitted Fields

- `stats.total_actions`
- `stats.success_rate`
- `stats.dry_run_ratio`
- `stats.live_ratio`
- `stats.by_rollback` (counts per class)
- `recent_actions[]` (last 10)
- `rollback_classification` (descriptions)

## UI Panel

- Collapsed by default
- Shows:
  - Last 10 actions with timestamp, actor, type, result
  - Dry-run vs live ratio badge
  - Rollback coverage indicator (reversible / irreversible / manual)
