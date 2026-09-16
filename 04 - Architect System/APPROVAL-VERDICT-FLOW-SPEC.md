---
title: Approval / Verdict Flow Spec
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, approval, verdict, state-machine, wave-6, hitl]
backlinks:
  - "[[WAVE-6-WORKING-NOTE]]"
  - "[[OCTOPUS-KNOWN-RISKS]]"
---

# Approval / Verdict Flow Spec

> Explicit state machine for all actions requiring owner approval. No silent jumps. Every transition is logged.

## Action Object Model

```json
{
  "action_id": "uuid",
  "type": "refresh | mining_start | approve_spending | ...",
  "source": "telegram | agent | system",
  "amount_aud": 0.0,
  "proposal_rationale": "Why this action was suggested",
  "requested_at": "2026-07-12T13:00:00Z",
  "status": "suggested | queued | owner_approved | executed | rejected | expired | superseded | dry_run",
  "verdict": "approve | deny | expire | supersede",
  "owner_identity": "owner_42",
  "verdict_timestamp": "2026-07-12T13:05:00Z",
  "verdict_rationale": "Why the owner decided this",
  "execution_result": "success | failure | cancelled | expired",
  "execution_timestamp": "2026-07-12T13:06:00Z",
  "rollback_class": "reversible | irreversible | requires_manual | unknown",
  "execution_mode": "dry_run | shadow | live"
}
```

## State Machine

```
suggested ──► queued ──► owner_approved ──► executed
    │           │              │
    ▼           ▼              ▼
 rejected    expired      superseded
    ▲           ▲              ▲
    └───────────┴──────────────┘
```

### Valid Transitions

| From | To | Requires Verdict |
|---|---|---|
| suggested | queued | No |
| suggested | rejected | Yes |
| suggested | expired | No |
| suggested | dry_run | No |
| queued | owner_approved | Yes |
| queued | rejected | Yes |
| queued | expired | No |
| queued | superseded | Yes |
| queued | dry_run | No |
| owner_approved | executed | No |
| owner_approved | rejected | Yes |
| owner_approved | expired | No |
| dry_run | queued | No |
| dry_run | rejected | Yes |

### Invalid Transitions (raise ValueError)

- executed → queued
- executed → rejected
- rejected → anything
- expired → anything

## Audit Requirements

Every transition appends to `_ops/state/approval-log.jsonl`:

```json
{"ts": "...", "action_id": "...", "from_status": "...", "to_status": "...", "actor": "...", "action_type": "...", "rationale": "..."}
```

## UI Representation

- **Status flow diagram** shown in queue panel: suggested → queued → owner_approved → executed
- **Time-in-queue** computed from `created_at` to now
- **Required owner action** label per status
- **Dry-run badge** on items that ran in dry-run mode
- **Deny reasons** from approval-log shown if item was rejected

## File References

- `nervous-system/approval_state_machine.py` — State machine + validator
- `nervous-system/extract_queue_data.py` — Enriches queue items with canonical status
- `_ops/budget/approval_queue_unified.py` — Unified queue (HITL)
- `_ops/budget/approval_channel.py` — Telegram approval channel
- `_ops/state/approval-log.jsonl` — Transition log
