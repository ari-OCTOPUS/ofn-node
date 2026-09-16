---
type: decision
status: active
tags: [owner-grant, wave1, telegram, 2026-08-21]
created: 2026-08-21
updated: 2026-08-21
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# OWNER-GRANT — بازکردن قفل‌ها 2026-08-21

مالک در فرم قفل‌ها صریحاً حکم داد. منبع: پاسخ AskQuestion همین جلسه (نه سایدکار، نه ایجنت).

| قفل | حکم |
|---|---|
| Wave 1 | **full** — حافظه + organism hook |
| تلگرام زنده | **full_live** — digest + سطح‌ها |
| نوشتن حافظه | **prod_write** |
| تماس پولی | **budgeted** — داخل daily_cap؛ این جلسه prefer صفر |
| doctor-pulse | **merge_pulse** (نه فقط قرنطینه) |
| STOP-TG-HEARTBEAT | **remove_now** (انتقال، نه حذف) |
| WORKLOCK چهار فایل | **all_four** این جلسه |
| بقیه | code_autonomy · git_commit · pass3_tests · lab_merge · approval_digest · botfather |

داده نشد: مسیردهی مینی‌اپ برای ۱۰ خانوادهٔ UNROUTED.

سکوت ≠ approval. این کارت خودِ حکم است.
