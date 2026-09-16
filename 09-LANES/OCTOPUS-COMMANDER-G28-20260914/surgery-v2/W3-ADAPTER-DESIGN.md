# W3 Adapter — تصمیم → worker ادامه (طراحی + پیاده‌سازی staged)

## اتصال به مکانیزم موجود

Worker موجود `park/unpark` دارد: تسک‌هایی که dependency شان برقرار نشده در
`blocked/` پارک می‌شوند و هر tick دوباره ارزیابی می‌شوند (`coding_worker.py:676-683`).
یک park reason از نوع `awaiting_owner_ack` اضافه می‌شود که فقط با ACK_SEEN برطرف می‌شود.

## Enum بستهٔ resume_action

```python
RESUME_ACTIONS = frozenset({
    "unpark_existing_internal_task",  # گیت: task در blocked/ با park_reason=awaiting_owner_ack
    # future: "mark_seen_in_report",
    # future: "enable_internal_step",
})
```

## جریان کامل (W3 end-to-end)

```
1. Task producer → decision_tasks.json ثبت می‌کند (durable, BEFORE card display)
   task: {task_id, payload_sha256, state: "awaiting_ack",
          created_at, scope: "internal-inert",
          resume_action: "unpark_existing_internal_task",
          worker_task_id: <real task in blocked/>}

2. Owner → پیام → glass → go_b3_inbox → binder → owner_decision.v1.jsonl
   decision: {verdict: "ACK_SEEN", bound_request_payload_sha256: <hash>}

3. consume_decisions (in tick):
   - matches task by exact hash
   - state → "resume_eligible" (ACK_RECORDED)
   - reads resume_action → dispatches to adapter

4. Adapter (in tick, after consume_decisions):
   - finds worker task in blocked/ by worker_task_id
   - verifies park_reason == "awaiting_owner_ack"
   - unparks it (moves to tasks/)
   - state → "resume_delivered" (RESUME_DELIVERED)

5. Worker (next tick):
   - picks up unblocked task
   - executes internal step
   - state → "work_completed" (WORK_COMPLETED) — only after real effect + read-back
```

## Statuses (معنادار، not just state-flip)

| Status | معنا | چه چیزی اثبات می‌شود |
|---|---|---|
| `awaiting_ack` | task ثبت شده، منتظر دیدن مالک | رجیستری durable |
| `resume_eligible` | ACK_SEEN ثبت شد؛ گیت ACK برطرف شد | آگاهی مالک |
| `resume_delivered` | worker درخواست ادامه را گرفت | unpark واقعی |
| `work_completed` | کار نتیجه داد + read-back شد | اثر داخلی |

## Durability (سه فاصلهٔ crash)

1. **پس از state change، پیش از receipt**: state در file است، receipt نیست → replay → TASK_NOT_WAITING → receipt تکمیل می‌شود (idempotent)
2. **پس از dispatch، پیش از delivery ثبت**: worker task در tasks/ است (unparked) → replay → adapter sees worker task active → RESUME_DELIVERED
3. **پس از اثر، پیش از completion**: worker انجام داده ولی decision_tasks هنوز resume_delivered → next tick: adapter checks worker task completed → WORK_COMPLETED

هر فاصله با idempotency key پایدار (task_id + decision_key) و state-based recovery حل می‌شود؛ نیاز به WAL جدا نیست.

## Negative controls (موردنیاز برای پذیرش)

- ACK-only on task needing approval → zero dispatch (resume_action not in enum)
- replay → zero additional effect
- registry absent/corrupt → NO_TASK_RETRYABLE (not permanently lost)
- delayed registration → recovered on next tick (proven by counterexample test)
- identity mismatch → NO_TASK_RETRYABLE
- dependency/quota unmet → task stays blocked; ACK only clears the ACK gate

## Implementation location

داخل ops_agent.py (TRIO)، درست بعد از `consume_decisions()`:
```python
def _dispatch_resumes(od: Path, tasks: dict) -> str:
    """Adapter: read resume_eligible tasks, execute their resume_action
    via the EXISTING worker park/unpark mechanism. No new orchestrator."""
```

Wired in tick(): `results["resume_dispatch"] = _dispatch_resumes(od, tasks)`

## آنچه هنوز OPEN است

1. **Producer واقعی رجیستری**: به‌صورت fixture-proven در battery؛ برای production، producer باید در مسیر owner_ask/decision_request کارت اضافه شود
2. **Deploy**: TRIO باید مستقر شود (quota-bound)
3. **Cognition broker 180**: هنوز نسخه‌دار نشده
