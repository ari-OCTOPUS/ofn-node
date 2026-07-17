---
type: report
status: draft
created_by: agent (Cowork session)
project: "[[03 - Projects/Accounting/PROJECT]]"
tags: [accounting, compliance, flags, draft]
created: 2026-07-12
updated: 2026-07-12
---

# پرچم‌های انطباق — snapshot AUG–NOV 2024

> ⚠️ **[Unverified — accountant to confirm]** — هیچ‌کدام «تشخیص تخلف» نیست؛ فقط مواردی که باید انسان/حسابدار ببیند. دادهٔ مبنا تاریخی است (FY2024-25).

## A) فلگ‌های خودکار importer (۶ مورد — همه در ANZ Business Essentials، 2024-11-26)

| تاریخ | شرح | مبلغ | فلگ | اقدام لازم |
|---|---|---:|---|---|
| 2024-11-26 | Allianz Insurance | 312.00 | no_abn_check | فاکتور/ABN فروشنده را ضمیمه کن |
| 2024-11-26 | Google Ads (~۱.۵ ماه) | 186.00 | no_abn_check | invoice با ABN گوگل موجود است؟ |
| 2024-11-26 | Xero (8×35) | 280.00 | no_abn_check | invoice + توافق تقسیم ۵۰٪ («باید نصف برمی‌داشتن») |
| 2024-11-26 | Ezidebit | 388.00 | no_abn_check | فاکتور خدمات |
| 2024-11-26 | بنزین | 3,300.00 | no_abn_check | 🔴 مبلغ بزرگ تجمیعی — رسیدهای سوخت جداگانه لازم (logbook?) |
| 2024-11-26 | برداشت مستقیم از کارت بیزنس | 4,600.00 | no_abn_check | 🔴 ماهیت برداشت: حقوق؟ قرض؟ drawing? → Div 7A اگر شرکت |

`[FACT]` صفر تراکنش ≥ $10,000 (AUSTRAC) در این ۱۶۰ ردیف.

## B) فلگ‌های الگویی (تحلیل agent — نیازمند توضیح مالک)

1. 🔴 **حقوق Behzad از مسیر حساب Armin** — ۱۹×`Payment to Armin Mohebiafzal` با برچسب «behzad cashout» (جمع 9,250 از ANZ Plus + 1,000 مستقیم). ردّ پرداخت به شخص ثالث ≠ گیرندهٔ واقعی → مستندسازی فوری لازم؛ به سؤال employee/contractor (PAYG/Super) گره خورده.
2. 🔴 **پرداخت حقوق از حساب‌های شخصی** — حقوق ماهانهٔ Armin (AUG 2,700 · SEP 2,220 · OCT 2,800 · NOV 2,600 + اضافه‌کاری 300 + «کار کامل رضا» 400) همه از ANZ Plus / COMPLETE FREEDOM؛ نه از حساب بیزنس. مخلوط‌شدگی شخصی/تجاری = بزرگ‌ترین red flag حسابرسی (p0 در MANIFEST).
3. 🟡 **«رضا»** در شرح `کار کامل رضا` (400) — رضا در ASSOCIATES config نیست؛ worker چهارم؟ `[OPEN]`
4. 🟡 **حواله‌های ایران** زیر برچسب sume asadi — Sydney Tehran Group (1,661.60) · Kourosh Mahmoodi (1,676) · Pb Holidays (1,280 + 1,000) · Ehsan Davari (3,885) · Ehsan Zamani (1,430) · S Niazmand (910): ماهیت (شخصی/تجاری/تسویهٔ شریک) و مستندات AML مشخص شود.
5. 🟡 **Rent تجاری یا مسکونی؟** — 1,488 دوهفتگی + ردیف‌های «recovered» (بازپس‌گیری؟). GST-claimable بودن ~1,352 در گرو همین پاسخ.
6. 🟡 **اشتراک هم‌زمان MYOB + Xero** — MYOB (31.00، 2024-08-11) و Xero (280 برای ۸ ماه×۳۵) هر دو دیده شد → همان ACC-V7 (قطع یکی).
7. ⚪ **Netflix سه‌بار زیر sume asadi + یک‌بار جدا** — دسته‌بندی شخصی/مشترک شفاف شود (جزئی).

## C) خلاصه برای حسابدار (وقتی انتخاب شد)

سه پروندهٔ اول جلسهٔ اول: (۱) ساختار قانونی دورهٔ AUG–NOV 2024 — sole trader یا Pty Ltd؟ چون Div 7A فقط در حالت شرکت موضوعیت دارد؛ (۲) وضعیت Behzad/Reza/Armin (employee vs contractor + پرداخت از مسیر ثالث)؛ (۳) تفکیک حساب‌ها + اصلاح جریان حقوق.

---
*Sources: drafts/importer-run/*.json · drafts/associates-subledger-DRAFT-2026-07-12.md · importer/config.js*
