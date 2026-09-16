---
type: spec
project: OCTOPUS
wave: 6
status: implemented
created: 2026-07-13
updated: 2026-07-13
tags: [octopus, wave-6, approval, verdict, state-machine, hitl]
---

# Approval / Verdict Flow Spec

## State Machine

```
suggested → queued → owner_approved → executed
   ↓           ↓            ↓
rejected   expired     superseded
   ↑
dry_run (records intent, no execution)
```

## Valid Transitions

| From | To | Allowed? |
|---|---|---|
| suggested | queued | ✅ |
| suggested | rejected | ✅ |
| suggested | expired | ✅ |
| queued | owner_approved | ✅ |
| queued | rejected | ✅ |
| queued | expired | ✅ |
| queued | superseded | ✅ |
| owner_approved | executed | ✅ |
| owner_approved | dry_run | ✅ |
| owner_approved | rejected | ✅ |
| owner_approved | expired | ✅ |
| executed | superseded | ✅ |
| dry_run | queued | ✅ |
| dry_run | owner_approved | ✅ |
| rejected | * | ❌ Terminal |
| expired | * | ❌ Terminal |
| superseded | * | ❌ Terminal |

## Action Object Model (JSON)

```json
{
  "action_id": "uuid",
  "type": "spend|refresh|mining|telegram",
  "source": "system|agent|owner",
  "amount_aud": 0.0,
  "proposal_rationale": "...",
  "requested_at": "2026-07-13T...",
  "status": "suggested|queued|owner_approved|executed|rejected|expired|superseded|dry_run",
  "verdict": "approve|deny|expire|supersede",
  "owner_identity": "owner_chat_id",
  "verdict_timestamp": "2026-07-13T...",
  "verdict_rationale": "...",
  "execution_result": "success|failure|cancelled|expired",
  "execution_timestamp": "2026-07-13T...",
  "rollback_class": "reversible|irreversible|requires_manual|unknown"
}
```

## Logging

Every transition is appended to `_ops/state/approval-log.jsonl` as an atomic record.

## UI Contract

- Queue panel shows status flow diagram
- Each item displays:
  - Canonical status label
  - Time-in-queue (human readable)
  - Required owner action
  - Dry-run vs live flag
  - Deny reason (if rejected)
- `actOne()` and `actAll()` are **propose-only**; they log intent but do NOT execute
