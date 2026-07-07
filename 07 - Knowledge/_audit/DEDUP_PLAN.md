---
title: DEDUP_PLAN — فاز A (dry-run)
created: 2026-07-05
scope: فقط 07 - Knowledge
status: منتظر تأیید — هیچ فایلی تغییر نکرده
method: نرمال‌سازی NFC + case-insensitive + SHA-256 کامل
---

# 🧹 DEDUP_PLAN — نقشه‌ی اقدام (dry-run)

## خلاصه‌ی آماری

| متریک | مقدار |
|---|---|
| گروه‌های هم‌اسم (>۱ عضو) | ۲ (`readme.md` ×۲۲، `roadmap.md` ×۲) |
| زیرگروه identical (hash یکسان) | **۰** |
| اقدام TRASH | **۰** |
| اقدام RENAME خودکار | **۰** |
| فضای آزادشونده | ۰ MB |
| لینک نیازمند به‌روزرسانی | ۰ |

**نتیجه‌ی خالص: در این scope هیچ تکراریِ byte-for-byte وجود ندارد و هیچ اقدام خودکاری لازم نیست.** دلیل: dedup بزرگ قبلاً انجام شده (نسخه‌ی ۶۴MB تکراری این پوشه در `03 - Projects` → `_Duplicates`، طبق یادداشت `_Index - Knowledge.md`).

## بخش ۱ — حذف تکراری دقیق
خالی. هر ۱۱۰ فایل hash یکتا دارند (حتی `16_Future/README.md` و `17_Archive/README.md` که هم‌حجم‌اند، محتوای متفاوت دارند — چک شد).

## بخش ۲ — تغییرنام هم‌اسم‌های متفاوت
طبق SOP، هم‌اسم‌های غیر-identical باید RENAME شوند. اما هر دو گروهِ یافت‌شده **هم‌اسمیِ قراردادی** هستند، نه تصادفی — RENAME به آن‌ها آسیب می‌زند:

| گروه | اعضا | چرا RENAME نه |
|---|---|---|
| `readme.md` ×۲۲ | READMEهای پوشه‌ای (۱۷ دسته‌ی KB + ۴ placeholder + ریشه‌ی KB) | قرارداد استاندارد «شرح پوشه»؛ ابزارها (Obsidian، Git، هر LLM) دقیقاً همین نام را انتظار دارند. مسیر والد disambiguator طبیعی است. |
| `roadmap.md` ×۲ | `00_Knowledge_Base/Roadmap.md` و `Silabi-Bot/roadmap.md` | دو سند واقعاً متفاوت در دو پروژه‌ی متفاوت؛ هیچ wikilink مبهمی به «roadmap» وجود ندارد (چک شد). فقط اگر روزی فایل‌ها هم‌پوشه شوند مشکل می‌شود. |

پیشنهاد: **SOP را با یک استثنا اصلاح کن:** «نام‌های قراردادیِ scoped-به-پوشه (README.md، index.md و مشابه) از قاعده‌ی rename معاف‌اند.»

## بخش ۳ — برای تصمیم انسانی

| مورد | فایل‌ها | ماهیت | پیشنهاد |
|---|---|---|---|
| نقشه‌ی قلب | `heart-awareness-map.pdf` / `-v2.html` / `-v3.html` (ریشه) / `.html` (Neuro-HRV-Nof1) | version + format siblings (هم‌اسم دقیق نیستند) | canonical = نسخه‌ی Neuro-HRV (مرجع E1–E5)؛ سه‌تای دیگر آرشیو. → HYGIENE §۱ |
| jahan-e-fusion | `.pdf` + `_CORRECTED.md` | format siblings | MD canonical (تصمیم ۸ خودت)؛ PDF آرشیو/برچسب |
| فایل‌های ژنتیکی | `امواج مغزی/*`، `GenomeInsight….pdf` | تکراری نیستند؛ طبق قانون ۴ فقط گزارش | خروج از vault (تصمیم/اجرای owner) |
| `Roadmap/roadmap` | دو فایل بالا | تصادم فقط case-insensitive | بدون اقدام، یا rename اختیاری `Silabi-Bot/roadmap.md` → `silabi-roadmap.md` (لینک ورودی ندارد؛ امن) |

## فاز B
اجرایی وجود ندارد که منتظر تأیید باشد — **هیچ TRASH/RENAME خودکاری پیشنهاد نشده.** اگر با پیشنهادهای بخش ۳ (آرشیو نسخه‌های heart-map و jahan PDF) موافقی، پیام بده: `APPROVED: اجرا کن` تا فقط همان انتقال‌های آرشیوی را با rollback map در `DEDUP_LOG.md` انجام دهم (انتقال به `_trash_2026-07-05/` داخل همین پوشه، برگشت‌پذیر).

> ⚠️ محدوده: `_Duplicates/` ریشه و بقیه‌ی vault خارج از دسترس این جلسه بود؛ dedup سراسری نیازمند دسترسی به کل `backup` است.
