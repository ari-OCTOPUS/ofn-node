---
type: proposal
kind: b1-change
decision_id: PROPOSAL-B1-CARDIAC-DAILYCAP-WIRING
status: PROPOSED_NOT_APPLIED
owner_vote: SIGNED_ED25519 (B1-SIGNING-CARD-2026-08-20 · T34 CONFIRMED_SAME — ERRATA بر APPROVED_VIA_CHAT قبلی)
scope: B1 (governed genome — _ops/cardiac.py, life_currency data source)
observed: 2026-08-19
---

# B1 Proposal — cardiac-budget.json باید `daily_cap` بنویسد

## شاهد (path + method + timestamp + grade)

- `_ops/state/cardiac-budget.json` — فقط `date/spent/resting` دارد؛ فیلد `daily_cap` غایب (OBSERVED, 2026-08-19T22:54).
- `_ops/heart/life_currency.py::daily_pool()` — `cb.get("daily_cap")` → `None` → `0.0` (OBSERVED_CODE).
- `_ops/state/pulse/life-currency-latest.json` — beat 42075: همهٔ اعضا صفر (OBSERVED_ZERO_ALLOCATION).
- علت ریشهای: `cardiac.py::BeatBudget` سقف روزانه را نمینویسد؛ مصرفکننده هیچ سقفی نمیخواند.

## تغییر پیشنهادی (اعمال نمیشود تا رأی مالک)

در `_ops/cardiac.py::BeatBudget`، فیلد `daily_cap` (مشتق از `budgets.yaml`/BIOS) به خروجی `cardiac-budget.json` اضافه شود — یا `daily_pool()` بهعنوان fallback از `budgets.yaml` بخواند.

## چرا B1

سقف متابولیسم/روز، سیاست ژنوم حاکم است (CONSTITUTIONAL-ZONES.yaml: `_ops/cardiac.py` = B1) و هر دو مسیر روی code خودِ B1 دست میزنند → نیازمند proposal → simulation → falsifier → shadow → رأی مالک → امضا.

## فالسایفر

اگر پس از اعمال، ۱۰ ضربان متوالی همچنان تخصیص صفر باشد (با daily_cap>0)، ادعای «سیمکشی درست» ابطال شده است.

## اثر در صورت رد

تخصیص همچنان صفر میماند؛ اقتصاد داروینی (فاز ۶) مستقل از این سیمکشی با شبیهسازی قطعی کار میکند و در docstring/LIFE-CURRENCY-SPEC صراحتاً «صفر تخصیص زنده» ثبت شده است.

## رأی مالک — تأیید پسینی (2026-08-20)

رأی چت مالک در جلسهٔ ZCode (چیپ پنج‌گزینه‌ای 2026-08-20 ~13:50 +10:00):
گزینهٔ **«تأیید پسینی با ثبت چت»**. یعنی: اعمالِ B1 ([[B1-APPLIED-UNSIGNED-2026-08-20]])
و rollback ایمنی به ۳۰ هر دو به‌عنوان تصمیم مالک **تأیید می‌شوند**؛ مراسم امضا
کامل نشده حساب می‌شود و Ed25519 به‌محض حل owner-key روی
[[B1-SIGNING-CARD-2026-08-20]] می‌نشیند و هر دو رویداد لجر را پوشش می‌دهد.
ثبت‌کننده: ایجنت ZCode (این خط). جعل امضا نیست — حکم کارت:
`B1_CHAT_APPROVED_ED25519_PENDING`.
