---
type: owner-decision-inbox
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
---

# Owner Decision Inbox — 2026-08-21

اقلامی که واقعاً بدون مالک پیش نمی‌روند. هر مورد از NEEDS-LEDGER آمده و به decision record متصل است.

## DEC-20260821-001 — OFN-Board LANE K (SQL/security debt)

- **منشأ**: NEED-20260821-011 (safety)
- **سؤال**: بدهی pre-existing در `03 - Projects/OFN-Board` (sqlite_base.py SQL پویا، test_sysmetrics path traversal) که Mimosa را در هر commit کل-ریپو مسدود می‌کند.
- **گزینه‌ها**:
  - A) مالک تعمیر OFN-Board را در lane جدا مجاز کند (Agent با allowlist دقیق).
  - B) مالک استثنای commit-scope برای این فایل‌ها بدهد (مثل پنجرهٔ commit امروز).
  - C) وضعیت فعلی حفظ شود: lane جدا، patch bundle، بدون bypass.
- **پیشنهاد Agent**: C فعلاً؛ A بعد از تصمیم مالک.
- **evidence**: LOOP-REGISTRY (LOOP-OFN-BOARD-SQL-SAFETY)، 02-DECISIONS/ACTIVATION-REPORT-2026-08-20.md

## DEC-20260821-002 — S-T02 closure معیار

- **منشأ**: NEED-20260821-003/012 (telegram)
- **سؤال**: آیا termination در notif-inbox برای شاخهٔ low-urgency event_bridge، closure محسوب می‌شود؟ یا S-T02 فقط با alert واقعی از شاخهٔ critical (incident.opened/contained → تلگرام) بسته می‌شود؟
- **گزینه‌ها**:
  - A) شاخهٔ critical: منتظر یک alert واقعی بمانیم (توصیهٔ فعلی).
  - B) مالک inbox-termination را به‌عنوان terminal مقبول اعلام کند → S-T02 با شواهد فعلی بسته شود.
  - C) retirement: اگر مسیر منسوخ است، مالک اعلام کند.
- **پیشنهاد Agent**: A.
- **evidence**: EVENT-BRIDGE-CANARY-2026-08-21.json

## DEC-20260821-003 — Wave 1 gate معیار

- **منشأ**: NEED-20260821-001/002 (memory/tests)
- **سؤال**: آیا تعمیر memory gate suite (F3/t_h/timeout) پیش‌شرط activation موج ۱ است؟
- **پیشنهاد Agent**: بله — preflight امروز NOT_ALL_GATES_PASS داد؛ wave1_unlocked=false می‌ماند تا suite سبز شود.
- **evidence**: WAVE1-PREFLIGHT-2026-08-21.json

## تصمیم‌های ثبت‌شدهٔ امروز (لینک)

- `_ops/state/decisions/decision-record.jsonl` (OWNER_ACCEPTANCE 0ad6f53 + continue order)
- `_ops/state/loops/TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json` (scopeها)
