---
type: owner-decision-record
decision_id: CORE-LIVE-LEARNING-01
status: RECORDED — اجرا آغاز شده (patch sequence شروع شد)
created: 2026-08-18 ~22:4x +10:00
recorded_by: agent (ZCode GLM-5.3, .191) — متن verdict عیناً از پیام مالک
supersedes: "توالی صرفاً ترتیبی F2–F5 در محور حافظه/یادگیری (F1-ACCEPTANCE قلمرو R01 را محدود کرد؛ این حکم دامنه را برای محور memory/learning باز می‌کند). F2-minimal (تعیین store کانونی) داخل patch-1 انجام می‌شود."
conflicting_advisory: "LAB-BURST-01 (پیشنهاد مشاور: worktree ایزوله + دادهٔ آزمایشی + ممنوعیت canonical) — ثبت شد؛ سنخ آشتی پایین"
tags: [octopus, core-live, memory, learning, budget]
---

# CORE-LIVE-LEARNING-01 — فعال‌سازی یادگیری زنده روی هستهٔ اصلی

## Verdict مالک (عیناً)

```text
OWNER DECISION: CORE-LIVE-LEARNING-01
OWNER AUTHORITY: confirmed
GOAL: فعال‌سازی هستهٔ اصلی برای API واقعی، حافظهٔ canonical و یادگیری رفتاری واقعی.
MODE:
  CORE = LIVE · MEMORY_WRITE = CANONICAL_GATED · MEMORY_READ = LIVE
  LEARNING = LIVE_MEASURED · EXTERNAL_ACTION = PROPOSE_ONLY · MONEY = LOCKED
  BOARDS = NO_CONTACT · NETWORK_DISCOVERY = FORBIDDEN · SHELL_EXECUTION = FORBIDDEN
  SCHEDULER = UNCHANGED
```

ALLOW (خلاصهٔ کامل در پیام مالک): API فقط از gateway اصلی با receipt اجباری · خواندن/نوشتن canonical فقط از Memory Admission Gate · ثبت raw/episode/prediction/negative · retrieval زنده · proposalها executable=false · holdout/calibration روی هسته · پچ کوچک فقط با bug report قابل‌بازتولید + rollback.

DENY (عیناً): دورزدن gate توسط LLM · /sh و subprocess و self-modification آزاد · پول/پیام بیرونی/credential/ACL/tunnel · SSH و تماس بردها · scheduler/daemon/timer جدید · حذف داده و rewrite history.

REQUIRED GATES: trace_id, parent_id, timestamp, actor, source, schema_version · idempotency_key · provenance/confidence/expiry در retrieval · contradiction-search پیش از admission · quarantine · receipt کامل هر API call · owner approval برای promotion · executable=false برای policy/hypothesis.

## BUDGET (پاسخ مالک، 2026-08-18 ~22:3x)

```yaml
daily_cap:        15 AUD          # مالک — provider: DeepSeek
per_call_cap:     0.50 AUD        # پیشنهاد ایجنت (مالک تعیین نکرد؛ قابل بازنویسی)
concurrency:      1               # ارتقا به 2 فقط با ۳۰ receipt کامل + error_rate < 5%
hard_stop:        12 AUD (80%)    # از existing budget gate (_ops/budget/) — نه سیستم موازی
model_spec:       "DeepSeek — «F4 flash» مبهم ثبت شد؛ مدل دقیق هنگام اولین receipt ثبت می‌شود"
local_compute:    "لوکال: حداقلی — لپ‌تاپ نباید هنگ کند (پروسه‌های organism/cortex/live/tg زنده‌اند)"
test_timebox:     "کل پاس تست ≤ 30 دقیقه با timeout سخت"
```

## SUCCESS CRITERIA (عیناً از verdict)

صفر write خارج از Admission Gate · ۱۰۰% receipt · ۱۰۰% prediction قبل از outcome · retrieval با provenance/timestamp/confidence/expiry · حداقل یک بهبود قابل‌اندازه‌گیری روی holdout زمان‌دار؛ وگرنه برچسب رسمی: `MEMORY_LIVE / LEARNING_UNVERIFIED`.

## آشتی با مشاورهٔ مخالف (LAB-BURST-01)

اختلاف فقط «محل ریسک در حین توسعه» بود، نه هدف. سنخِ اجرا (که هر دو قید مالک را حفظ می‌کند):

```text
توسعهٔ پچ‌ها در worktree قرنطینه (بدون write زنده)  →  مراسم owner-approval
→  فعال‌سازی روی هستهٔ اصلی (MODE بالا)  →  اندازه‌گیری زنده با receipt/holdout
دادهٔ تست در فاز ۳۰-دقیقه‌ای اول: test-only؛ پس از آن جریان واقعی هسته از همان مسیر گیت‌دار
```

یعنی: **آزمایشگاه برای ساخت، هسته برای حقیقت.** هیچ‌چیز از DENY-list در هیچ فازی باز نمی‌شود.

## ترتیب پنج patch (عیناً از verdict مالک — نقشهٔ اجرا)

| # | patch | لمس TCB؟ | خروجی |
|---|---|---|---|
| P1 | بستن bypass: سرشماری کامل writerها/readerها + تک‌مسیر کردن نوشتن | خیر (_ops/memory) | writer-census + پچ قرنطینه |
| P2 | Memory Admission Gate (evidence/timestamp/source/confidence/contradiction-check/quarantine) | خیر | ماژول + تست |
| P3 | Memory Read Patch در introspect/create/conclude | **بله — automation.py** | مراسم مالک اجباری |
| P4 | Prediction Ledger (immutable + تست ضد-backdating) | خیر | chrono/store + تست |
| P5 | Learning Evaluator (baseline vs holdout) | خیر | ارزیاب + گزارش صادقانه |

سطح‌های زمانی مالک (Live-1: ۳۰دقیقه / Live-2: ۲ساعت / Live-3: ۲۴ساعت) روی همین ترتیب سوار می‌شود؛ هر سطح فقط پس از گیت قبلی.

## وضعیت قفل‌های قبلی — بدون تغییر

D2 (/sh مسلح — CARD-A همچنان معلق نزد مالک) · D3 (mail_credentials فاز انسانی) · D5 (sprint فریز) · D6 (بردها بدون تماس) · GITWRITE-FAILED و FREEZE دست‌نخورده.
