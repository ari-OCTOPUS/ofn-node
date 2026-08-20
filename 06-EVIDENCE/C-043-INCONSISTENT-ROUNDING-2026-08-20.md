---
type: evidence
status: suspected_void
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, C-043]
---

# C-043 — گردکردن ناسازگار فیلدهای life-currency

contradiction_id: C-043
status: **SUSPECTED_VOID**
owner: CORE
related: C-042 · C-045
created: 2026-08-20T12:12+10:00
updated: 2026-08-20T12:36+10:00
implementation: diagnose only — فیکس حساب‌داری این جلسه اجرا نشد

## حکم مالک #۳

ادعای «گردکردن ناسازگار» با شواهد نمی‌خواند. با `round(x,3)` روی هر چهار فیلد، مقادیر beat 42784 (`hard_cap=0.078`, `beat_pool=0.02`, `reserve=0.004`, `tokens=0.001`) فقط برای

`period ∈ [112.32 s, 113.04 s)`

سازگارند. در `period = 113.65 s` نتیجه `hard_cap = 0.079` است نه 0.078.

مسئله گردکردن نیست؛ **period مصرفی حساب‌داری با period گزارش‌شدهٔ داور یکی نبوده**. نقص provenance → [[T14-PERIOD-PROVENANCE-2026-08-20]] · [[C-045 در CONTRADICTIONS|C-045]].

## ERRATA نسبت به ثبت T8

- باطل نمی‌شود که هر فیلد `round(raw,3)` مستقل است (`life_currency.py` 123–124، 232–233، 246–247).
- باطل می‌شود که اختلاف 0.078 در برابر 0.079 در beat 42784 **شاهد ناسازگاری round/truncate در یک فایل** است.
- 0.078 = `round(2×30×112.76/86400, 3)` یعنی period تیک قبل، نه truncate.

## شاهد قبلی (حفظ شد)

فایل beat 42784 روی دیسک **UNLOCATED**. آفلاین `allocate_beat("AMBER", cap=30, period=113.65)` → `hard_cap=0.079`.
