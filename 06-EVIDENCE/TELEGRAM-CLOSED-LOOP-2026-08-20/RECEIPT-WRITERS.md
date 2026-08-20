---
type: evidence
status: active
tags: [telegram, a3, quota, receipts, 2026-08-20]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# A3 — writerهای رسید + forensic

## Writerهای `cost-receipts.jsonl` (شناختی)

| محل | نقش |
|---|---|
| `_ops/cortex/cost_receipt.py` `CostReceiptAdapter.build` | schema |
| `_ops/cortex/model_router.py` (~352 و ~786) | append زنده |
| `_ops/cognition_quota.py` | فقط classify/gate — بازنویسی صفر |

Writerهای «receipt» دیگر (`state_guard`, `action_bridge`, `full_loop_flash/gateway`, `integration_receipt`) فایل جدا دارند؛ ۹۶۲ ردیف تاریخی **بازنویسی نشد**.

## Forensic (limit 5000، کل فایل)

```text
n=962
attributed(task_id AND run_id)=6
unattributed=956
ratio=0.62%
rewritten=0
```

۱۴A «۱۹.۷٪ task_id امروز» را با معیار ضعیف‌تر (فقط task_id) گفته بود. سهمیهٔ شناختی حالا **هر دو** `task_id`+`run_id` می‌خواهد. بدون `run_id` → `UNATTRIBUTED` → در cap قابل مصرف نیست.

Bucketها: `K9` · `event_probe` · `full_loop` · `telegram_normal` · `judge_phase2`.

گیت قبل از reserve/شبکه: `PAID_COGNITION_PAUSED` | `UNATTRIBUTED_INTENT_BLOCKED` | `QUOTA_EXHAUSTED` → `LOCAL_DEGRADED_MODE`.

پس از reload مرکز، `_ask_paid` داخل همان پروسه تا `OCTOPUS_PAID_COGNITION=1` شبکه نمی‌زند. organism (PID 9904) تا ریاستارت جدا کد قدیم را دارد.
