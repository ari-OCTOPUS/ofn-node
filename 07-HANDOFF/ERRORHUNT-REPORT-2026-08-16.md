---
type: handoff
session: ERRORHUNT-2026-08-16
audience: next-agent
---

# HANDOFF — شکار خطا / گیرکردن (2026-08-16)

شواهد: [[../06-EVIDENCE/ERRORHUNT-2026-08-16|ERRORHUNT]] · خام: [[../06-EVIDENCE/ERRORHUNT-RAW-2026-08-16|RAW]] · کارت‌ها: [[../02-DECISIONS/ERRORHUNT-CARDS-2026-08-16|کارت‌ها]]

## یک‌خطی
زیرِ beat سالم، سه چیز واقعی بود: اسنپ‌شات circuit دروغ می‌گفت closed (C-022، persist شد) · `mark_nudged()` تولیدی TypeError می‌داد (فیکس شد) · خودِ Poisoning Watch در 10:08 با FILE_NOT_FOUND مرد. readback پس از 05:00 صفر خطا است. cortex در ۲۴ساعت اخیر wedge نشده.

## برای ایجنت بعد
1. `run_all.py` را خودت ثبت نکن (WORKLOCK). دو فایل تست نام‌یکتا: `test_circuit_demote_persist_errorhunt.py` · `test_discovery_nudge_high_water_errorhunt.py`.
2. `wiring.py` هانکِ recall-loop هم در درخت کاری است — mark_nudged را جدا نگه دار.
3. فایل زنده `circuit-state.json` هنوز ممکن است `closed+opened_at` نشان بدهد تا اولین `check()`/`status()` پس از این کد.
4. آزاد بعدی تناقض: **C-023**. C-022 = همین نشست. مگاپرامپت «C-019 آزاد» کهنه بود.

## نکن
خاموش‌کردن آلارم/واچداگ برای ساکت‌کردن · لمس TCB · ری‌استارت غیررسمی · حذف لاگ.
