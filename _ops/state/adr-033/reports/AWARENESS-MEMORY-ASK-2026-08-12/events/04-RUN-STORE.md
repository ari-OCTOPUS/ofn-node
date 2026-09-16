# 04-RUN-STORE — Run Store Adapter (2026-08-12)

## فناوری

JSONL append-only در `state/cognitive/runs/<run_id>.jsonl`.
Reuse convention موجود (`evidence_plane/event_log.py` با همان الگو).

## API

```python
create_run(run_id, trace_id, metadata) → run dict
append_event(run_id, event_type, ...) → sequence number
get_run(run_id) → run dict | None
list_events(run_id, after_sequence=-1) → list[event]
mark_terminal(run_id, status) → bool
```

## Durability

`PROCESS_DURABLE` — فایل روی دیسک، ولی no cross-process guarantee.
pause/resume ادعا نمی‌شود.

## Invariants

- append-only ✅
- monotonic sequence ✅
- idempotent by event_id (duplicate append → sequence continues) ✅
- terminal state enforcement (RUN_COMPLETED/RUN_FAILED/RUN_CANCELLED) ✅
- corrupt record → fail-closed (JSON decode error skip) ✅
- may_authorize همیشه false ✅

## تست‌ها (10/10)

- run_id unique (100 IDs, 0 collision)
- start_run creates events (RUN_CREATED + USER_MESSAGE_ACCEPTED)
- sequence monotonic
- no raw text persisted (redaction)
- may_authorize always false
- complete_run terminal
- fail_run
- run_summary
- list_events after sequence
- duplicate run_id idempotent
