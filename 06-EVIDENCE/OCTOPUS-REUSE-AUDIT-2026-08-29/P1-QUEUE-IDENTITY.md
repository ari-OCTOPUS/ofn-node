---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, reuse, queue, p1]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/REUSE-MAP]]"
---

# P1 — هویت صف: CONFIRMED mismatch

مشاهده: 2026-08-29. `runId=p1-queue-identity`. اثر خارجی ۰. پچ کد ۰.

## فرضیه‌ها

| ID | فرض | حکم | شاهد |
|---|---|---|---|
| A | صف V2 از دایرکتوری‌های mesh می‌آید، نه از `Outbox` کسب‌وکار | **CONFIRMED** | `_collect_queue` روی `_QUEUE_DIRECTORIES` اسکن می‌کند؛ `source_id = mesh_queue_{name}`؛ `idem`/`owner_queue` در فایل = ۰ |
| B | صف V2 همان `owner_queue()` را wrap می‌کند و IDها یکی‌اند | **REJECTED** | صفر ارجاع به `owner_queue` / `idem_key` در `cockpit_v2_read_model.py` @ `6881337` |
| C | نبود V2 روی vault `c803dee` یعنی قابلیت وجود ندارد | **REJECTED as absence** | فایل ۲۹۶۶ خطی روی شاخهٔ ofn-node هست؛ vault درخت دیگری است |
| D | `OwnerDecision` عمداً تا M2 بی‌سیم مانده | **INCONCLUSIVE** برای نیت؛ **CONFIRMED** برای واقعیت کد: `run.py` فقط ReadModel را load می‌کند |

## دو فضای شناسه

**فرمان زنده (vault `c803dee` + همان الگوی ofn):**

- insert: `scoped = f"{tenant}:{idem_key}"` در `outbox.py:144`
- صف مالک: `"id": item.idem_key` در `node.py:2201`
- decide: `item_id.partition(":")` در `node.py:3094`

**نمای V2 (`6881337`):**

- id = `message_id` از JSON mesh، وگرنه از نام فایل (`_project_queue_row` خطوط ۱۲۸۶–۱۲۸۸، خروجی `"id": message_id` خط ۱۳۳۳)
- منبع = پوشه‌های `inbox|outbox|processing|processed|rejected` + `mesh_queue_leases`

این دو ID به‌صورت ساختاری یکی نیستند. parity صفر با «همان projection» امروز **غیرممکن** است مگر join اضافه شود.

## لاگ

`debug-bbea48.log` · `hypothesisId=A` · `data.lines=2966` (ادعای ۲۹۶۶ **تأیید** شد؛ ۲۷۷۵ خط محتوا اشتباه اندازه‌گیری قبلی بود).

## پچ مجاز بعدی (اعمال‌نشده)

یک منبع دوم **داخل همان** `_collect_queue` یا resource جدا با نام صریح `business_outbox` که `id = tenant:idem_key` را از SQLite outbox موجود بخواند.  
نه API جدید، نه queue سوم، نه Command Bus. نیاز به GO + فاز ۰ هویت درخت ۱۳۸.
