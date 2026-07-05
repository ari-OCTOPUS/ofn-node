---
type: log
status: active
tags: [review, routine]
created: 2026-07-03
updated: 2026-07-03
---

# مرور هفتگی — چک‌لیست اجراپذیر ایجنت

> نسخه ایجنت‌محورِ مرور هفتگی (۱۵–۳۰ دقیقه معادل انسانی). ربات architect اجرایش می‌کند و یک پیام خلاصه فارسی می‌فرستد؛ تا آن روز، Claude Code دستی اجرایش می‌کند.

## هفتگی

- [ ] جاروی `00 - Inbox` و `10 - Telegram processing` تا صفر — طبق [[10 - Telegram processing/SOP|SOP]] و درخت تصمیم قانون اساسی.
- [ ] ورودی‌های `pending` تلگرام با مالک حل شود.
- [ ] هر نوت `status: active` با `updated:` قدیمی‌تر از ۱۴ روز → از مالک بپرس (تلگرام): هنوز active است، paused یا done؟
- [ ] اعتبارسنج‌ها: `validate_frontmatter.py` + `find_broken_links.py` (پوشه `04 - Architect System/scripts`) — هر دو پاس.
- [ ] هرچه `status: done` شده → چک‌لیست تکمیل (بخش ۳ قانون اساسی).
- [ ] سوالات بی‌جواب [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] به مالک.
- [ ] یک پیام خلاصه فارسی به مالک.

## ماهانه (اضافه بر هفتگی)

- [ ] مرور نوت‌های `kind: area` (بیزنس‌های جاری): Active Context هنوز درست است؟
- [ ] نگاهی به `_Archive`/`_Duplicates` با مالک: چیزی برای حذف نهایی؟ (تصمیم فقط با مالک.)

## لاگ اجراها

<!-- هر اجرا یک خط: تاریخ — یافته‌های مهم — لینک گزارش. -->
