---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: archived
tags: [octopus, migration]
created: 2026-07-18
updated: 2026-08-08
---

> **⚠️ سندِ تاریخی (۲۰۲۶-۰۷-۱۷/۱۸).** این گزارشِ پروبِ آن تاریخ است و
> بازتابِ وضعیتِ **پیش از** برش‌های ۰-۳ ِ طرحِ هیدرید کنترل‌پلین. سؤالاتِ بازِ این
> سند (مثل «Source of Truth کدام است؟») در `02-OCTOPUS-KNOWLEDGE-SNAPSHOT.md` پاسخ
> داده شده‌اند. برایِ شناختِ به‌روز `00-README-START-HERE.md` و `04-NEXT-AGENT-MEGAPROMPT.md`
> را بخوان. این دادهٔ پروب برایِ پشت‌زمینه نگه داشته شده، نه برایِ عمل.

# 🖥️ یادداشت انتقال به Desktop — شناخت اختاپوس

درخواست مالک این بود که همهٔ اطلاعات در Desktop با نام «شناخت اختاپوس» ذخیره شود.

## وضعیت فعلی

در این اجرای فعلی، allowed directory فقط این بود:

```text
F:\backup
```

بنابراین پوشه اینجا ساخته شد:

```text
F:\backup\شناخت اختاپوس
```

## کار ایجنت بعدی اگر Desktop در دسترس بود

اگر در اجرای بعدی allowed directories شامل Desktop بود، این پوشه را به Desktop کپی یا mirror کن:

```text
From:
F:\backup\شناخت اختاپوس

To:
C:\Users\Armin\Desktop\شناخت اختاپوس
```

## قاعدهٔ انتقال

- قبل از overwrite، مقصد را list کن.
- اگر پوشهٔ Desktop وجود داشت، فایل‌های جدید را merge کن نه overwrite کور.
- اگر تضاد نسخه بود، نسخهٔ F را با timestamp نگه دار.
- هیچ secret یا `.env` را منتقل/باز نکن.
- بعد از انتقال، یک فایل `MIGRATION-DONE.md` در مقصد بساز که زمان و منبع انتقال را بنویسد.

## دستور کوتاه برای انسان/ایجنت

```text
اگر Desktop قابل دسترس شد، F:\backup\شناخت اختاپوس را به Desktop\شناخت اختاپوس mirror کن و فایل‌های README را اول نگه دار.
```
