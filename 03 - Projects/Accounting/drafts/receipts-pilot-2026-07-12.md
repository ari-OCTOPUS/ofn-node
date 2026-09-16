---
type: report
status: draft
created_by: agent (Cowork session)
project: "[[03 - Projects/Accounting/PROJECT]]"
tags: [accounting, receipts, ocr, pilot, acc-v8]
created: 2026-07-12
updated: 2026-07-12
---

# پایلوت رسیدها (ACC-V8) — نتیجه: هیچ رسیدی موجود نبود

> verdict مالک برای اجرای پایلوت: ثبت‌شده 2026-07-12 (انتخاب صریح در جلسهٔ Cowork). فرمت خروجی طبق RUNBOOK §4.

## خلاصه

`[FACT]` هر ۴ فایل `data/receipts/` باز و بررسی شد — **هیچ‌کدام رسید نیستند**. هر چهار عکس اسکرین‌شات موبایل از یک گفتگوی DeepSeek (فارسی، عنوان «شبیه‌سازی جهان و استراتژی‌ها…»، ساعت 21:49) هستند و هیچ دادهٔ مالی (تاریخ خرید، فروشنده، مبلغ، GST، ABN) در آن‌ها وجود ندارد.

نتیجهٔ عملی: فرض «۴ رسید خام untapped» در MANIFEST/README/RUNBOOK نادرست بود؛ خط لولهٔ receipt-OCR هنوز **هیچ ورودی واقعی** ندارد.

## خروجی استاندارد §4 برای هر فایل

```yaml
# photo_543@21-07-2025_21-50-11.jpg
date: n/a
vendor: n/a
amount_total: n/a
gst_component: n/a
abn_present: unknown
category_draft: NOT_A_RECEIPT (chat screenshot — DeepSeek)
confidence: 0.98
needs_human_review: true
```

```yaml
# photo_544@21-07-2025_21-50-11.jpg
date: n/a
vendor: n/a
amount_total: n/a
gst_component: n/a
abn_present: unknown
category_draft: NOT_A_RECEIPT (chat screenshot — DeepSeek)
confidence: 0.98
needs_human_review: true
```

```yaml
# photo_545@21-07-2025_21-50-11.jpg
date: n/a
vendor: n/a
amount_total: n/a
gst_component: n/a
abn_present: unknown
category_draft: NOT_A_RECEIPT (chat screenshot — DeepSeek)
confidence: 0.98
needs_human_review: true
```

```yaml
# photo_546@21-07-2025_21-50-11.jpg
date: n/a
vendor: n/a
amount_total: n/a
gst_component: n/a
abn_present: unknown
category_draft: NOT_A_RECEIPT (chat screenshot — DeepSeek)
confidence: 0.98
needs_human_review: true
```

## اقدام انجام‌شده (برگشت‌پذیر)

- ۴ فایل به `data/receipts/_not-receipts-quarantine-2026-07-12/` منتقل شد (فقط move؛ هیچ حذفی نشد).
- کپی یکسانِ دوم در `photos/` دست‌نخورده ماند (md5 هر ۴ جفت یکسان `[FACT]`).
- پیشنهاد (نیازمند verdict): محتوای این اسکرین‌شات‌ها به Accounting ربطی ندارد → انتقال به `_inbox-other-projects/` در vault، و حذف یکی از دو کپی تکراری.

## قدم بعدیِ پایلوت واقعی

طبق RUNBOOK §4: مالک ۱۰ رسید واقعی (کاغذی/PDF — ترجیحاً Bunnings/سوخت/بیمه) عکس بگیرد و در `data/receipts/` بگذارد؛ سپس همین چرخهٔ استخراج→draft→verdict اجرا و نرخ خطا ثبت می‌شود. تا آن زمان ACC-V8 = **approved-but-blocked-on-data**.

---
*Sources: data/receipts/*.jpg (۴ فایل، بررسی بصری) · photos/*.jpg (md5 compare) · RUNBOOK.md §4*
