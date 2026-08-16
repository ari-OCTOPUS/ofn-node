---
type: handoff
session: RECALL-LOOP-2026-08-16
audience: next-agent
---

# HANDOFF — حلقهٔ recall (2026-08-16)

نقطهٔ شروع: [[../06-EVIDENCE/RECALL-LOOP-2026-08-16|شواهد کامل]] · کارت‌ها: [[../02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/RECALL-LOOP-CARDS-2026-08-16|کارت‌ها]]

## یک‌خطی
ریشه = NaN از hash-as-float32 در doctor encode + انتخاب nearest؛ فیکس شد و گرم شد. M3: **58/2.0/9.28٪ → 90/21.0/14.4٪**. 4d: **0 → 1** با تسک ۶ساعته.

## برای ایجنت بعد
1. اگر مالک کارت ۱ را داد: `RESTART-ALL.ps1` سپس یک سیکل صبر کن و `recall_reach` را دوباره بگیر — ردیف ۶۲۵ نباید `sk=[]` شود.
2. تست ثبت‌نشده (WORKLOCK): `_ops/tests/test_recall_loop_distant.py` — در `run_all.py` ثبت نکن مگر lane آزاد.
3. تسک ویندوزی: `OCTOPUS 4d Consolidation Tick` — لاگ در `06-EVIDENCE/POISONING-WATCH-4d.md`.
4. C-022 آزاد است. C-021 = NaN-hash recall (این نشست). C-019 = 4d بی‌قلاب daemon (contained با تسک).

## نکن
حذف کلید برای «بهبود» آمار · لمس TCB · فلگ تازه · فعال‌سازی یادگیری/NO-GO.
