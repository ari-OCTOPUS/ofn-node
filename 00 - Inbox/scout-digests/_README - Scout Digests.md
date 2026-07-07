---
type: reference
status: active
tags: [agents, research, inbox]
created: 2026-07-04
updated: 2026-07-04
---

# scout-digests — استیجینگ خروجی fleet تحقیق

> این پوشه «محل فرود اسپور» است: هر اسکات زمان‌بندی‌شده دیجست روزانه‌اش را اینجا می‌گذارد (`YYYY-MM-DD <slug>.md`). طبق درخت تصمیم §۴ قانون اساسی، مالک این‌ها را تریاژ می‌کند: ارزشمند → پوشه پروژه یا `07 - Knowledge`؛ بی‌سیگنال → هرس.

- مثل `10 - Telegram processing/Raw/` یک استیجینگ پایپ‌لاینی است، نه Inbox اصلی — تا Inbox اصلی تمیز بماند.
- همه فایل‌ها: `type: research` · `status: inbox` · `created_by: agent` · `sources` (≥۲).
- پروتکل و فهرست اسکات‌ها: [[05 - Agents/Research Scout Fleet|Research Scout Fleet]].
- **اول این‌ها را بخوان:** `* synthesis.md` (سنتز شبانهٔ روز، خواندنی‌ترین) و یکشنبه‌ها `* fleet-eval.md` (ارزیابی و تنظیم ناوگان). بقیهٔ فایل‌ها دیجست خام هر اسکات‌اند.
- **نمای دیتابیسِ ابسیدین (Bases):** برای مرورِ فیلترشده/گروه‌بندی‌شدهٔ همهٔ دیجست‌ها:

![[Scout Digests.base]]
- **Evaporation (2026-07-04):** consolidator هر شب `status` دیجست‌های >۱۴ روز را به `archived` می‌برد (in-place، برگشت‌پذیر، فقط همین پوشه) تا نقشه خوانا بماند. **حذف** هرگز خودکار نیست (§۰ قاعده ۱) — پاکسازی نهایی فقط دستی مالک.
