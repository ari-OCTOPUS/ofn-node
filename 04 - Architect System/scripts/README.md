---
type: reference
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [scripts, validation]
created: 2026-07-03
updated: 2026-07-03
---

# اسکریپت‌های اعتبارسنجی vault

> «ایجنت تصمیم می‌گیرد، اسکریپت verify می‌کند.» هر دو dry-run هستند — فقط گزارش، بدون تغییر. این پوشه کنار `_code` است، نه داخلش؛ ویرایشش مجاز است.

| اسکریپت | چه می‌کند | خروج غیرصفر یعنی |
|---|---|---|
| `validate_frontmatter.py` | نوت‌های «لایه دست‌چین» (پوشه‌های سیستمی + همه PROJECT.mdها + نوت‌های سطح‌بالای 03/07 — نه بسته‌های سند داخلی مثل brushline): کلیدهای هسته، status/type در مجموعه بسته، تاریخ ISO، tags لیست، کلید خارج از schema | حداقل یک نوت نامعتبر |
| `find_broken_links.py` | همه `[[wikilink]]`ها را با فایل‌های موجود مطابقت می‌دهد (به سبک resolution ابسیدین: basename یا مسیر) | حداقل یک لینک شکسته |

اجرا (از ریشه vault):

```
python "04 - Architect System/scripts/validate_frontmatter.py"
python "04 - Architect System/scripts/find_broken_links.py"
```

قاعده (بخش ۱۱ قانون اساسی): بعد از هر ویرایش دسته‌ای و در شروع مرور هفتگی، هر دو اجرا شوند؛ جلسه وقتی «تمام» است که هر دو پاس شوند.

مرجع schema: [[06 - Architecture Maps/Property Schema|Property Schema]] — کلید جدید اول آنجا تعریف می‌شود، بعد به `KNOWN_KEYS` اسکریپت اضافه می‌شود.
