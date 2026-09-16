---
title: Replay / Audit Model Spec
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, audit, replay, rollback, wave-6, logging]
backlinks:
  - "[[WAVE-6-WORKING-NOTE]]"
  - "[[OCTOPUS-KNOWN-RISKS]]"
---

# Replay / Audit Model Spec

> Every action on the control plane is logged with pre-action snapshot, execution mode, result, and rollback classification.

## Audit Record Schema

```json
{
  "timestamp": "2026-07-12T13:00:00Z",
  "action_id": "uuid",
  "actor": "owner | agent | system",
  "action_type": "refresh | approve_spending | mining_start | ...",
  "pre_action_snapshot": {"queue_hash": "abc123", "relevant_state": "..."},
  "proposal_rationale": "Why this action was proposed",
  "verdict": "approve | deny | expire | supersede",
  "verdict_owner": "owner_42",
  "execution_mode": "dry_run | shadow | live",
  "result": "success | failure | cancelled | expired",
  "rollback_class": "reversible | irreversible | requires_manual | unknown",
  "meta": {}
}
```

## Rollback Classification

| Class | Definition | Examples |
|---|---|---|
| **reversible** | Can be undone automatically or trivially | refresh data, toggle panel, copy text, status, queue, help |
| **irreversible** | Cannot be undone; permanent effect | approve spending, execute command, delete data, stop |
| **requires_manual** | Requires human operator to undo | mining start, wallet transfer, telegram message send |
| **unknown** | New untested action; classification pending | Any action not in the known lists |

## Audit Logger API

```python
from audit_logger import AuditLogger

logger = AuditLogger()

# Log a proposal
logger.log_proposal("a1", "refresh", proposal_rationale="Data stale")

# Log a verdict
logger.log_verdict("a1", "approve", "owner_42")

# Log execution result
logger.log_execution("a1", "success", "dry_run")
```

## UI: Audit Trail Panel

- **Collapsed by default** (read-only panel)
- Shows last 10 actions: timestamp, actor, action type, rollback class, execution mode, result
- **Dry-run vs live ratio** badge
- **Rollback coverage** indicator (% reversible / irreversible / requires_manual)
- **Success rate** badge

## File References

- `nervous-system/audit_logger.py` — Audit logger class
- `nervous-system/extract_audit_trail.py` — Extractor for UI data
- `nervous-system/audit-trail-data.js` — UI payload
- `_ops/state/action-audit.jsonl` — Canonical audit log
- `_ops/heart/replay_s.py` — Replay engine (existing, not modified in Wave 6)
