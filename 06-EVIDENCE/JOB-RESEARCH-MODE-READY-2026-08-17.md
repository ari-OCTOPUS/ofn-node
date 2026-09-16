---
type: evidence
session: claim_hypothesis production wiring — option (ب) از پیشنهادِ CLAIM-HYPOTHESIS-WIRING-PROPOSAL، مصوبِ مالک
agent: Claude Sonnet 5 (Claude Code)
created: 2026-08-17 ~22:2x
mode: propose-only for the two live files — sandboxed apply+test only
---

# `_job_research` — گزینهٔ (ب) از پیشنهادِ قبلی، آماده و تست‌شده

مالک از میانِ چهار گزینهٔ [[../02-DECISIONS/CLAIM-HYPOTHESIS-WIRING-PROPOSAL-2026-08-17|پیشنهادِ قبلی]] **گزینهٔ (ب) — modeِ نوِ `_job_research`** را انتخاب کرد؛ یعنی بزرگ‌ترین/کدی‌ترین گزینه، نه ابزارِ دستی.

## طراحی
- **`_job_research` وارد `_MODE_CYCLE` نشد** — به‌جایش مثلِ `git_watcher`، یک فراخوانِ جداگانه با کیدنسِ خودش (`DAEMON_RESEARCH_EVERY`, پیش‌فرض ۵۰ تیک ≈ ۲۵ دقیقه) از خودِ `daemon.py` صدا زده می‌شود — تا چرخهٔ فعلیِ ۱۴حالته دست‌نخورده بماند.
- الگوریتم: قدیمی‌ترین فرضیهٔ `pending`/`tested=0` را بردار → نسبت به `experiments` بسنج (شباهتِ توکنیِ همانِ `hypothesis_similarity` که خودِ `_job_create` برای dedup استفاده می‌کند، آستانهٔ ۰.۳۰) → `claim_hypothesis(row_id, session_ref=f"auto-research-{trace_id}")`.
- **صادقانه محدود:** فقط claim می‌کند، ادعای «تست کردم» (ستونِ `tested`/`result`) نمی‌کند — چون تابعِ claim خودش هم فقط همین را تضمین می‌کند؛ ساختنِ یک setter نو برایِ `tested` بیرونِ دامنهٔ این پچ ماند.

## چرا هر دو فایل TCB اند
`brain/automation.py` (متدِ نو) و `brain/daemon.py` (فراخوانِ کیدنس‌دار) هر دو در `trust-boundary.json:tcb.files` هستند — هیچ‌کدام مستقیم ویرایش نشدند، فقط پچِ سندباکس‌تست‌شده ساخته شد.

## راستی‌آزماییِ سندباکس [A]
کپیِ کاملِ `4d_system`، DB سندباکسِ مستقل، ۳ فرضیهٔ seed با timestampِ دستکاری‌شده (قدیم/میانه/جدید) + یک تجربهٔ مرتبط:

| بررسی | نتیجه |
|---|---|
| فراخوانِ ۱ | claim #۱ (قدیمی‌ترین)، ۱ تجربهٔ مرتبط یافت شد |
| فراخوانِ ۲ | claim #۲ (بعدی)، ۱ مرتبط |
| فراخوانِ ۳ | claim #۳ (آخرین از سه‌تای seed)، ۱ مرتبط |
| فراخوانِ ۴ | صفِ seedِ من خالی شد، رفت سراغِ صفِ agenda-seed خودِ `AutomationController.__init__` — claim #۴، ۰ مرتبط، **بدونِ کرش** |
| **تستِ یکپارچگیِ کامل** | `brain.daemon.run_forever(max_ticks=4, DAEMON_RESEARCH_EVERY=3)` — ۴ تیک، ۰ خطا، state سالم نوشته شد |

هیچ ردیفی حذف نشد؛ فقط status از `pending` به `claimed` رفت — دقیقاً طبقِ قراردادِ `claim_hypothesis`.

## پچ‌ها
- `00 - Inbox/PATCH-JOB-RESEARCH-automation-2026-08-17.patch` (۸۱ خط — متدِ نو)
- `00 - Inbox/PATCH-JOB-RESEARCH-daemon-2026-08-17.patch` (۲۷ خط — قلابِ کیدنس‌دار)

## مراسمِ لازم از دستِ مالک
هم‌الگویِ EQUIP G2 (`06-EVIDENCE/EQUIP-G2-WIRING-READY-2026-08-17.md`): `git apply` هر دو پچ → بازسازیِ manifest → امضا با کلیدِ owner-signing → ریاستارتِ دیمون. **پیشنهاد: هر دو پچ (EQUIP G2 + این دو‌تا) را در یک مراسمِ TCB بزنید** — یک بازسازی+امضا+ریاستارت به‌جایِ دوتا.

## کارِ باز
- `DAEMON_RESEARCH_EVERY=50` یک حدسِ محافظه‌کارانه است، نه سنجش‌شده — بعد از چند روزِ زنده قابلِ تنظیم.
- اگر بعداً خواستید claim واقعاً به معنایِ «تست‌شده» هم برسد (ستونِ `tested`/`result`)، آن یک قدمِ بعدیِ جداست، نه بخشی از این پچ.
