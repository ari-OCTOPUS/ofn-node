---
type: report
status: draft
created_by: agent (Cowork session)
project: "[[03 - Projects/Accounting/PROJECT]]"
tags: [accounting, status, gap-analysis]
created: 2026-07-12
updated: 2026-07-12
---

# گزارش وضعیت + Gap-Analysis — جلسهٔ Cowork 2026-07-12

> دستور کار مصوب مالک در همین جلسه: (۱) گزارش وضعیت (۲) راستی‌آزمایی importer (۳) پایلوت رسیدها (۴) استخراج دفاتر xlsx — با مجوز کامل PII داخل جلسه و خروجی به‌صورت zip کامل. همهٔ برداشت‌های مالیاتی `[Unverified — accountant to confirm]`.

## ۱) دلتای واقعیت نسبت به مستندات (مهم‌ترین یافته‌ها)

| ادعای مستندات | واقعیتِ بررسی‌شده | وضعیت |
|---|---|---|
| MANIFEST/REGISTRY: importer «DESIGNED — not built» | کد کامل + تست موجود بود؛ ۱۳/۱۳ تست سبز + اجرای موفق روی ۱۶۰ تراکنش واقعی | ✅ **جلوتر از مستندات** — REGISTRY به‌روز شد |
| MANIFEST/README/RUNBOOK: «۴ رسید خام untapped در data/receipts» | هر ۴ عکس اسکرین‌شات چت DeepSeek است؛ **صفر رسید** | ❌ **فرض نادرست** — قرنطینه شد؛ پایلوت واقعی محتاج ۱۰ رسید واقعی |
| ساختار xlsx «فقط-ساختار، استخراج deferred (openpyxl نبود)» | استخراج کامل ۱۶۰ تراکنش انجام شد + تطبیق با شیت خلاصهٔ دستی | ✅ بلاکر برداشته شد |
| MANIFEST: `pending_human_verdicts: 0` | VERDICT_QUEUE ده verdict باز دارد (ACC-V1..V10) | ⚠️ تناقض داخلی — اصلاح شد |
| MANIFEST: `security_gate: closed (4 CRITICAL)` | RUNBOOK/REGISTRY: «LIFTED 2026-07-06 ولی کف مالی read-only/draft-only باقی» | ⚠️ تناقض بین اسناد — MANIFEST قدیمی‌تر است؛ flag برای verdict |
| PROJECT.md: «کد به `_code/` منتقل شد (B1)» | `app/` و `importer/` داخل همین پوشه حاضرند | ⚠️ snapshot با آن تصمیم ناسازگار است — مالک روشن کند کدام مرجع است |

## ۲) نتیجهٔ استخراج دفاتر (خلاصه — جزئیات در sub-ledger)

`[FACT]` شیت دستی `حساب و کتاب.xlsx` (پنجرهٔ AUG→NOV 2024) با تراکنش‌های PS Export **با دقت ~۸ دلار سازگار است**: Armin ‏11,020 و Behzad ‏10,250 دقیق؛ Rent ‏14,940 پس از حذف دو ردیف جولای دقیق؛ Maliheh ‏+6.94 و Sume ‏+0.99 (رُندکردن). ادعای ورودی 86,075 از این فایل‌ها قابل راستی‌آزمایی نیست (فقط سمت هزینه موجود است) و ماندهٔ 12,938 حساب داخلی‌اش درست است.

نکتهٔ زمانی: این دیتا **FY2024-25** است؛ دفاتر FY2025-26 هنوز صفر رکورد دارد.

پرچم‌های اصلی (جزئیات: `flags/compliance-flags-2026-07-12.md`): حقوق Behzad از مسیر حساب Armin (۱۹ تراکنش)؛ حقوق‌ها از حساب‌های شخصی؛ ماهیت Rent نامشخص؛ برچسب sume asadi مخلوطِ بیزنس/شخصی/حوالهٔ ایران؛ «رضا» خارج از رجیستر associates؛ MYOB+Xero هم‌زمان.

## ۳) وضعیت verdictها بعد از این جلسه

| ID | تغییر امروز |
|---|---|
| ACC-V8 (پایلوت رسید) | ✅ approved by owner 2026-07-12 → اجرا شد → **blocked-on-data** (رسید واقعی صفر بود) |
| ACC-V9 (importer) | ✅ approved (تست/راستی‌آزمایی) → انجام شد؛ ساخت از قبل موجود بود |
| ACC-V6/V7 (نرم‌افزار) | شواهد جدید: پرداخت هم‌زمان MYOB و Xero در دیتای واقعی دیده شد → تصمیم فوری‌تر شد |
| ACC-V1..V5, V10 | بدون تغییر — همچنان open و فقط مالک/حسابدار |
| جدید — **ACC-V11 پیشنهادی** | تکلیف اسکرین‌شات‌های غیررسید (انتقال به `_inbox-other-projects/`؟) + حذف یکی از دو کپی (photos/ ≡ data/receipts) |
| جدید — **ACC-V12 پیشنهادی** | کدام حساب‌ها «بیزنس»‌اند؟ (فعلاً فقط ANZ Business Essentials در config) — پیش‌نیاز فلگ‌گیری Div7A |

## ۴) ناهنجاری‌های ساختاری پوشه (housekeeping — propose-only)

- دو پوشهٔ خالی `1/` و `2/` در ریشه `[FACT]` → پیشنهاد حذف (بی‌محتوا).
- `Report - Tax Map FY2025-26.md` دو نسخه دارد (ریشه + docs/) با تفاوت فقط یک wikilink `[FACT — diff ۴ خطی]`؛ نسخهٔ ریشه canonical است (طبق Active Context) → پیشنهاد حذف نسخهٔ docs/.
- `photos/` کپی بایت‌به‌بایت `data/receipts/` بود (md5 یکسان) → یکی کافی است.
- `app/gitignore` بدون نقطه است (باید `.gitignore` باشد تا عمل کند) `[FACT]`.
- امنیت: هیچ `.env`، توکن واقعی یا فایل DB داخل پوشه نیست `[FACT — اسکن شد]`.
- هیچ‌کدام از حذف‌ها اجرا نشد — فقط قرنطینهٔ برگشت‌پذیر رسیدهای غیرواقعی.

## ۵) سه قدم بعدی پیشنهادی (به ترتیب ارزش/تلاش)

1. **export کامل ANZ (همهٔ حساب‌ها، FY2024-25 + FY2025-26)** → importer آماده است؛ با یک اجرا دفتر draft کامل + فلگ‌های واقعی Div7A تولید می‌شود. (نیم‌ساعت کار مالک)
2. **۱۰ رسید واقعی** در `data/receipts/` → اجرای واقعی پایلوت ACC-V8 و ساخت golden-set برای OCR.
3. **انتخاب حسابدار (ACC-V1)** — با بستهٔ آمادهٔ این جلسه (sub-ledger + flags + سؤالات §C فایل فلگ‌ها) جلسهٔ اول حسابدار بسیار پربارتر می‌شود؛ بدون او همهٔ قواعد `[Unverified]` می‌مانند.

## ۶) کارهای انجام‌شدهٔ این جلسه (فایل‌های جدید)

`drafts/associates-subledger-DRAFT-2026-07-12.md` · `drafts/ledger-extract/*.csv` (۵ فایل) · `drafts/importer-run/*.json` (۵ خروجی) · `drafts/receipts-pilot-2026-07-12.md` · `reports/importer-validation-2026-07-12.md` · `flags/compliance-flags-2026-07-12.md` · `data/receipts/_not-receipts-quarantine-2026-07-12/` · به‌روزرسانی VERDICT_QUEUE / DecisionLog / PROJECT (Active Context) / OpenQuestions / REGISTRY / INDEX · اصلاح نام‌فایل‌های فارسی (`#Uxxxx` → یونیکد).

---
*Sources: MANIFEST.yaml · REGISTRY.md · RUNBOOK.md · VERDICT_QUEUE.md · PROJECT.md · data/حساب کتاب/*.xlsx · data/receipts/*.jpg · importer/* · drafts/* · flags/**
