---
type: report
status: draft
created_by: agent (Cowork session)
project: "[[03 - Projects/Accounting/PROJECT]]"
tags: [accounting, importer, validation, acc-v9]
created: 2026-07-12
updated: 2026-07-12
---

# راستی‌آزمایی ANZ Importer — تست synthetic + اجرای واقعی (ACC-V9)

> verdict مالک برای تست/راستی‌آزمایی: ثبت‌شده 2026-07-12. اجرای draft-only؛ هیچ DB و هیچ دفتری نوشته نشد.

## ۱) تست‌های synthetic

`[FACT]` `node importer/anz-import.test.js` → **۱۳/۱۳ سبز** (ادعای README تأیید شد). پوشش: CSV با کوتیشن/کاما، GST=total/11، GST-free (خارجی/بهره)، نگاشت فروشنده، Div7A، no-ABN، آستانهٔ AUSTRAC، reconciliation (۱ مغایرت تزریقی، بدون false-positive)، شکل خروجی draft.

نکتهٔ محیط: `better-sqlite3` نصب نیست → لایهٔ dedup-DB به‌صورت طراحی‌شده skip شد و draft کامل تولید شد (رفتار graceful درست). `[FACT]`

## ۲) اجرای واقعی — ۵ فایل PS Export (۱۶۰ تراکنش، AUG–NOV 2024)

فایل‌های xlsx در `data/حساب کتاب/` دقیقاً همان ۱۴ ستونِ مورد انتظار importer را دارند `[FACT]` → به CSV تبدیل و اجرا شد. خروجی‌ها: `drafts/importer-run/*.json`.

| فایل | rows | business | نیاز به review | فلگ انطباق | مغایرت reconcile |
|---|---:|---:|---:|---:|---:|
| Armin | 6 | 0 | 6 | 0 | 2 |
| Rent | 13 | 10 | 3 | 0 | 6 |
| behzad | 20 | 0 | 20 | 0 | 18 |
| maliheh | 72 | 1 | 39 | 0 | 48 |
| sume asadi | 49 | 11 | 35 | 6 | 34 |

رفتارهای درستِ مشاهده‌شده `[FACT]`:
- GST=total/11 روی دادهٔ واقعی (مثال: xero 280 → 25.45 + 254.55)
- شکار cross-scope: خرید Bunnings داخل فایل شخصی maliheh → Materials/business
- ۶ فلگ `no_abn_check` روی هزینه‌های بیزنس >۷۵$ در ANZ Business Essentials (Allianz 312 · Google Ads 186 · Xero 280 · Ezidebit 388 · بنزین 3,300 · برداشت 4,600)
- هیچ تراکنش ≥10k → صفر فلگ AUSTRAC (درست)

## ۳) محدودیت‌ها و gapهای شناسایی‌شده

1. **مغایرت‌های reconcile سیگنال خطا نیستند** — این exportها *فیلترشده* (per-person) هستند؛ Closing Balance بین تراکنش‌های غیرمتوالی می‌پرد. reconciliation فقط روی export کامل حساب معنا دارد `[FACT — طراحی importer هم همین را فرض کرده]`.
2. **GST روی برداشت نقدی/انتقال** — «برداشت مستقیم از کارت بیزنس» (4,600) GST=418.18 گرفت؛ برداشت/drawing مشمول GST نیست. پیشنهاد: تشخیص `TRANSFER/DRAWING/withdrawal/برداشت` → gstFree + فلگ drawing `[پیشنهاد backlog]`.
3. **Div7A فلگ نخورد چون حساب‌ها بیزنس تعریف نشده‌اند** — پرداخت‌های associates از `ANZ Plus`/`COMPLETE FREEDOM`/`Smart Access` رفته که در `BUSINESS_ACCOUNTS` نیستند؛ فقط `ANZ Business Essentials` بیزنس است. اگر مالک هرکدام از این حساب‌ها را تجاری اعلام کند، فلگ‌های Div7A فعال می‌شوند `[OPEN — ACC-V5/config]`.
4. **dedup فقط در لایهٔ DB است** — `buildDraft` در حافظه dedup نمی‌کند؛ اگر CSV ورودی ID تکراری داشته باشد دوبار می‌شمارد (در ۵ فایل فعلی: صفر ID تکراری `[FACT]`). پیشنهاد: dedup در `buildDraft` هم `[پیشنهاد backlog]`.
5. `Merchant Changed From` و `Note` در دسته‌بندی استفاده می‌شوند ولی در خروجی draft حمل نمی‌شوند — برای review انسانی مفیدند `[پیشنهاد جزئی]`.

## ۴) نتیجه

Importer برای نقش طراحی‌شده‌اش (**draft-only، روی export کامل مالک**) آمادهٔ استفاده است؛ وضعیت REGISTRY از `csv_import: not built` باید به `built + validated (synthetic 13/13 + real-data smoke)` ارتقا یابد. برای production هنوز: export کامل ANZ + تأیید لیست حساب‌های بیزنس + تصمیم‌های ACC-V2/V5 لازم است.

---
*Sources: importer/anz-import.js · importer/anz-import.test.js · importer/config.js · drafts/ledger-extract/*.csv · drafts/importer-run/*.json*
