---
type: project
kind: area
project: "[[03 - Projects/Accounting/PROJECT]]"
status: active
owner: آری
risk_level: high
autonomy_level: read-only
tags: [accounting, tax, australia]
created: 2026-07-03
updated: 2026-07-06
---

# پروژه: Accounting

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

دفاتر audit-ready برای شرکت (Pty Ltd — D3) تا آری بتواند قراردادهای بزرگ‌تر بگیرد. **tenant #1** سیستم architect (ترتیب D-26: Accounting → Lead-نقاشی → Mining).

> ⚠️ هیچ ایجنتی مشاوره مالیاتی نمی‌دهد. همه قواعد مالیاتی/انطباقی این نوت `[Unverified — accountant to confirm]` هستند تا حسابدار رسمی تأیید کند.

## Current state (شواهد)

- ساختار: Pty Ltd ثبت‌شده یا در حال ثبت (تصمیم D3) `[Assumption — مالک تأیید کند]`
- محتوای موجود vault: فقط لاگ تلگرام (`03 - Projects/Accounting/Accounting.md`) و `README.md` — هیچ دفتر/فاکتور ساختاریافته‌ای هنوز داخل vault نیست `[Verified: ls همین پوشه]`

## رجیستر انطباق شرکت (Australian company compliance)

| فیلد | مقدار | وضعیت |
|---|---|---|
| ACN | — | `[To measure — مالک]` |
| ABN | — | `[To measure — مالک]` |
| Director ID | — | `[To measure — مالک]` |
| ASIC annual review date | — | `[To measure — مالک]` |
| Registered office | — | `[To measure — مالک]` |
| ثبت GST | وضعیت ما: — `[To measure — مالک]` · آستانه اجباری: گردش سالانه ≥ $75,000 (ثبت تا ۲۱ روز پس از عبور) | `[Verified: ato.gov.au، 2026-07]` |
| چرخه BAS | فصلی — استاندارد برای گردش < $20M؛ سررسید: ۲۸امِ ماه بعد از هر فصل | `[Verified: ato.gov.au]` · تطبیق با وضعیت ما: حسابدار |
| نرخ مالیات شرکت | ۲۵٪ اگر base rate entity (گردش تجمیعی < $50M **و** ≤۸۰٪ درآمد passive)، وگرنه ۳۰٪ — سال مالی 2025-26 | `[Verified: ato.gov.au tax-rates-2025-26]` · تشخیص BRE بودن ما: حسابدار |
| PAYG withholding | — | `[To measure — مالک]` |

**اگر بیزنس نقاشی نیرو بگیرد (هرکدام یک فیلد وضعیت):** STP فعال؟ — `[To measure]` · Superannuation guarantee: **۱۲٪** از 2025-07-01 (آخرین پله افزایش) و **از 2026-07-01 پرداخت super هر payday** به‌جای فصلی — `[Verified: ato.gov.au super-guarantee + payday-super]` · NSW workers comp (icare) — `[To measure]`

## گردش‌کار فاکتور و رسید

1. هر فاکتور/رسید → عکس/PDF به `00 - Inbox` (یا تلگرام) → ایجنت پیشنهاد دسته‌بندی می‌دهد (draft) → تأیید انسان → بایگانی در پوشه Accounting.
2. دسته‌های هزینه: مواد نقاشی، ابزار، سوخت/خودرو، بیمه، اشتراک نرم‌افزار/AI، بازاریابی، تلفن/اینترنت، حق‌الزحمه حرفه‌ای، متفرقه.
3. نگهداری سوابق: ۵ سال (ATO، از تاریخ تهیه/تکمیل تراکنش) و **۷ سال اسناد مالی شرکت** (Corporations Act 2001 s 286 — ASIC) `[Verified: ato.gov.au + asic.gov.au]`.

## Assets & resources

درآمد renovation/painting (منبع اصلی)؛ حسابدار خارجی `[To measure — انتخاب نشده]`؛ هنوز نرم‌افزار حسابداری انتخاب نشده `[To measure]`.

## Active workstreams

1. تکمیل رجیستر بالا توسط مالک. 2. انتخاب حسابدار + نرم‌افزار. 3. راه‌اندازی گردش‌کار رسیدها (پیش‌نیاز tenant شدن).

## KPIs

فاصله ثبت رسید تا دسته‌بندی (هدف <۷ روز) · BAS بدون جریمه · درصد تراکنش‌های دسته‌بندی‌شده `[To measure]`

## Agent interface

- **می‌خواند:** همین PROJECT.md، رسیدها/فاکتورهای Inbox، لاگ تلگرام Accounting.
- **می‌نویسد:** فقط draft دسته‌بندی و گزارش ماهانه — همه با برچسب `[Unverified — accountant to confirm]`.
- **verdict انسانی لازم:** هر ثبت نهایی، هر ارسال به ATO/ASIC (ایجنت هرگز lodge نمی‌کند)، هر پرداخت.
- **Security Gate:** تا باز بودن CRITICALهای [[ROTATION_CHECKLIST]] فقط read-only.

## Open blockers

- ردیف‌های `[To measure]` رجیستر — فقط مالک.
- حسابدار انتخاب نشده → هیچ قاعده مالیاتی تأییدشده نیست.

## Active Context

- تمرکز فعلی: تبدیل به tenant #1 — اول تکمیل رجیستر انطباق و انتخاب حسابدار
- تغییرات اخیر: 2026-07-03 — ارتقا به manifest فاز ۱ (رجیستر انطباق + گردش‌کار + agent interface) · 2026-07-04 — [[03 - Projects/Accounting/Report - Accounting - Tax Map FY2025-26|Report - Tax Map FY2025-26]] از Inbox به این پوشه منتقل شد (نکته کلیدی: سقف instant asset write-off از 1 Jul 2026 → $1,000) · 2026-07-04 — کیت مغز پروژه (INDEX·DecisionLog·OpenQuestions طبق LIVING-BRAIN-BLUEPRINT) ساخته شد
- ۳ قدم بعدی: (۱) مالک: ACN/ABN/تاریخ‌ها را پر کند (۲) انتخاب حسابدار (۳) تست گردش‌کار رسید با ۱۰ رسید واقعی
- تصمیم‌های باز: نرم‌افزار حسابداری؛ چرخه BAS با حسابدار

## Progress

- چه کار می‌کند: manifest کامل؛ گردش‌کار تعریف‌شده (اجرا نشده)
- چه مانده: داده واقعی، حسابدار، نرم‌افزار، اجرای گردش‌کار
- مشکلات شناخته: هیچ سند مالی ساختاریافته‌ای هنوز در vault نیست

## Next actions

- [ ] تکمیل رجیستر انطباق (مالک)
- [ ] انتخاب حسابدار و جلسه اول
- [ ] پایلوت گردش‌کار رسید

## نوت‌های مرتبط

- [[03 - Projects/Accounting/Report - Accounting - Tax Map FY2025-26|Report - Tax Map FY2025-26]]
- [[03 - Projects/Accounting/Accounting|لاگ پیام‌های تلگرام — Accounting]]
- [[03 - Projects/Accounting/app/README|README]]
- [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاش�