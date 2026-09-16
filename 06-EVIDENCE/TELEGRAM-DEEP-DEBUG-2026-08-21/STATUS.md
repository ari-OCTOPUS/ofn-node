# TELEGRAM DEEP-DEBUG IMPLEMENTATION — STATUS 2026-08-21

دستور مالک: `OWNER EXECUTION ORDER — WRITE AND REPAIR AUTHORIZED` (2026-08-21).
Plan: `_ops/cortex/plans/TELEGRAM-DEBUG-IMPLEMENTATION-2026-08-21.md` (W0, commit f7dbebc).

## وضعیت نهایی

**`IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING`** — تنها وضعیت مجاز برای Builder.

- سویییتها: **۲۰۲/۲۰۲ سبز** (۱۶۳ ثبتشده + ۳۹ تست موجهای A–F) — `SUITE-MATRIX.json`.
- ۸ commit اتمی (W0–W6 + restore) — `WAVE-COMPLETION-RECEIPTS.json` (SHA کامل، فایلها، rollback، اسکن no-secret).
- ممنوعیتها رعایت شد: **صفر** ارسال زنده، صفر webhook، صفر تماس پولی، صفر تغییر TCB، صفر force-push، صفر دستکاری ledger/evidence.
- Live attachment سوییچها default-off باقی ماندند (sender_bridge توسط مرکز import نمیشود؛ transport subprocess با فلگ owner-gated).

## موجها (خلاصه)

| موج | commit | دستاورد |
|---|---|---|
| W0 | f7dbebc | Plan + baseline |
| W1 | fc3ef66 | health truth: watchdog_truth (poll کامل = سلامت؛ update هرگز تنها معیار نیست) + فیلدهای کامل |
| R | 94fa59f | restore organs package روی خط اصلی (یکپارچگی شواهد ۱۶۳) |
| W2 | b78d1b6 | ConfigManager: boot-once، reload با digest، snapshot غیرقابلتغییر، LKG+stale، حذف read_text مستقیم از حلقههای داغ (mission/rfcs) |
| W3 | 036ef32 | transport_pool: circuit per-bot (threshold/409/cooldown)، سقف همزمانی، deadline سخت، subprocess قابل terminate |
| W4 | 2af9904 | شواهد lease تک-pollery: مصرفکنندهٔ دوم قبل از getUpdates رد میشود |
| W5 | ad42c43 | شواهد C3/C4: retry_after کامل، مرزهای restart، crash→UNCERTAIN بدون auto-resend، کلید تکراری |
| W6 | 6249741 | باتری ۱۶ سناریوی دستور (۱۰۰×DNS، ۱۰۰×read/write stall، crash-before، نشتی worker و…) |

## ۱۶ سناریوی دستور — پوشش

۱–۳. ۱۰۰ DNS / ۱۰۰ config read / ۱۰۰ config write stall → fail-soft بدون قفل
۴. concurrent poller race → مصرفکنندهٔ دوم deny قبل از شبکه
۵. 409 → circuit/lease فوراً OPEN + cooldown
۶. crash قبل از attempt → ماندگار، بعد از restart یک‌بار ارسال
۷. crash بعد از attempt → UNCERTAIN_SEND_OUTCOME در DLQ، هرگز auto-resend
۸–۹. restart در retry_after−۱ (ارسال ممنوع) / retry_after (ارسال مجاز)
۱۰. کلید تکراری → یک تحویل
۱۱–۱۲. malformed config / stale snapshot → LKG سالم، هرگز جایگزین نمیشود
۱۳–۱۴. poll خالی = progress / ۳۰ دقیقه بیپیام = سالم (نه HANG)
۱۵. watchdog false-positive پیشگیری (watchdog_truth)
۱۶. worker/thread leak → صفر پس از ۱۰۰ stall

## مرزهای زنده (لمس نشد)

- restart کنترلشدهٔ مرکز زنده انجام **نشد** — طبق دستور فقط بعد از سبز شدن fixtureها، و اینجا فعلاً شواهد fixture کافی برای restart امن نیست (گیت بعدی مالک).
- میزبان network فقط api.telegram.org؛ token هرگز لاگ/کامیت نشد؛ lease فقط digest یکطرفه.

## گیتهای بعدی (مالک)

1. بازبینی این شواهد + تصمیم restart کنترلشدهٔ مرکز در polling/read-only
2. SIG-IV: verification مستقل (هد اعلامشده cc267048 یا فرزند بعدی)
3. سپس مسیر مگاپرامپت ۲ (canary تکپیامی) با تأیید صریح
