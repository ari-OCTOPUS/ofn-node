# 03-EVENT-SCHEMA — Typed Event Schema v1 (2026-08-12)

## Envelope

```json
{
  "event_id": "evt_<uuid16>",
  "event_type": "INTENT_DETECTED",
  "event_version": 1,
  "run_id": "run_<uuid12>",
  "trace_id": "trace_<uuid12>",
  "sequence": 3,
  "occurred_at": "2026-08-12T16:00:00Z",
  "producer": "conversation",
  "status": "COMPLETED",
  "intent": "intro",
  "payload": {},
  "evidence_refs": [],
  "redaction_applied": true,
  "may_authorize": false,
  "applied": false
}
```

## Event Types v1 (پیاده‌شده)

`RUN_CREATED` · `USER_MESSAGE_ACCEPTED` · `INTENT_DETECTED` · `MODEL_FINISHED` · `RESPONSE_COMPLETED` · `RUN_COMPLETED` · `RUN_FAILED`

## Event Types تعریف‌شده ولی هنوز emit‌نشده

`CONTEXT_RETRIEVAL_STARTED` · `CONTEXT_RETRIEVED` · `MEMORY_FOUND` · `MEMORY_CANDIDATE_CREATED` · `MODEL_STARTED` · `MODEL_TOKEN` · `TOOL_REQUESTED` · `TOOL_STARTED` · `TOOL_RESULT` · `CLAIM_CREATED` · `CLAIM_VERIFIED` · `PROPOSAL_CREATED` · `POLICY_DECISION` · `EXECUTION_RECEIPT` · `RESPONSE_STARTED` · `RUN_PAUSED` · `RUN_RESUMED` · `RUN_CANCELLED`

## قواعد اعمال‌شده

- event_id یکتا (uuid4 hex) ✅
- run_id ثابت بعد از creation ✅
- sequence صعودی و بدون gap ✅
- redaction: text/prompt/content/dm فیلتر ✅
- may_authorize همیشه false ✅
- applied همیشه false (بدون EXECUTION_RECEIPT) ✅
- append-only JSONL ✅
