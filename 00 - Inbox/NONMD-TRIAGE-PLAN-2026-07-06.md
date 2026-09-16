---
type: proposal
status: done
created: 2026-07-06
updated: 2026-07-06
tags: [triage, backlog, non-md, cleanup]
---

# NONMD-TRIAGE-PLAN — پلن انتقال فایل‌های غیر-md (propose-only)

> verdict آری 2026-07-06: «خودت مهندسی کن». این سند طراحی است؛ **هیچ فایلی هنوز جابه‌جا نشده.** اجرا فقط با verdict روی هر batch. حذف مطلقاً ممنوع — همه‌چیز `mv` است.

## یافتهٔ کلیدی اسکن (عدد ۷۶۷۴ گمراه‌کننده بود)

| محل | تعداد غیر-md | وضعیت |
|---|---|---|
| `04 - Architect System/architect/_code` | ~۴۷۶۱ | ✅ از قبل داخل `_code` است — سر جای خودش، read-only، هیچ اقدامی لازم نیست |
| `.claude` | ~۱۳۴۵ (۳۸۸MB) | ⚙️ کش سیستم/پلاگین — جزء vault نیست، دست نزن |
| `08 - Assets` | ~۶۲۵ (تصویر) | ✅ مقصد درست asset هاست |
| `_Duplicates` | ~۱۵۷ (۸۴MB) | ✅ خودش مقصد انتقال است |
| `03 - Projects` | **~۷۰۵** | 🔴 تنها backlog واقعی — پلن پایین |
| بقیه (Inbox/Dashboard/Knowledge/scripts) | ~۶۰ | ✅ عملیاتی (validatorها، HTMLهای داشبورد و…) |

یعنی کل مسئله = **~۷۰۵ فایل داخل ۶ پوشهٔ پروژه**، نه ۷۶۷۴.

## پلن ۳-batch برای 03 - Projects

**قاعدهٔ ثابت:** کد → `_code/<project>/` (پوشهٔ `_code` ریشهٔ vault؛ اگر نیست ساخته می‌شود) · باینری/دیتا/آرشیو → `_Duplicates/nonmd-<project>/` (تا انتقال نهایی به دیسک بیرونی توسط آری) · تصویرِ ارجاع‌شده در نوت‌ها → می‌ماند (یا `08 - Assets` اگر orphan).

| Batch | محتوا | مقصد | ریسک | تست بعد از اجرا |
|---|---|---|---|---|
| **B1 — کد** | ‏`py/sh/bat/js/yml/json/vbs` در Lead (۶۲py) · Mining (۷۷py) · Ziman (۳۰py) · Crypto (۶py) · Accounting (۷js) | `_code/<project>/` با حفظ ساختار زیرپوشه | متوسط — اسکریپتی که با مسیر نسبی به نوت‌ها اشاره کند می‌شکند؛ ⚠️ در Lead یک repo تودرتو (`.git/hooks/*.sample`) هست → کل آن پوشه یکجا منتقل شود، بازش نکن | هر دو validator + `rg` روی PROJECT.mdها برای مسیرهای شکسته به فایل‌های منتقل‌شده |
| **B2 — دیتا/باینری** | ‏`parquet(14)/csv/zip/pdf`های آرشیوی Mining و Crypto | `_Duplicates/nonmd-<project>/` | کم — دیتای مصرف‌شده | لینک‌چک؛ اسپات‌چک ۳ نوت Mining |
| **B3 — تصاویر** | ‏jpgهای پروژه‌ها (Lead ۱۵۹، Mining ۶۳…) | فقط orphanها → `08 - Assets/<project>/`؛ ارجاع‌شده‌ها می‌مانند | کم‌ولی‌پرتعداد — embed ‏`![[...]]` نباید بشکند | `find_broken_links.py` صفر شکسته |

**ترتیب:** B1 → validator سبز → B2 → B3. هر batch یک جلسه، بعدش commit (وقتی git init شد). قبل از B1 اگر git هنوز init نشده، پیشنهاد: اول runbook 04 (rollback داشته باشیم).

## ✅ اجرا شد — 2026-07-06 (verdict آری: «برو کاملش کن»)

- **B1:** ۹ پوشهٔ کد + ۱۲ فایل منفرد → `_code/<project>/` · ۴ نوت md معماری (path-linked) برگردانده شد تا لینک نشکند.
- **B2:** ۱۴ فایل دیتا/آرشیو بدون‌ارجاع → `_Duplicates/nonmd-*`.
- **B3:** ۶۸ تصویر orphan → `08 - Assets/<project>/` · ۱۹۲ فایل ارجاع‌دار عمداً سر جایشان ماند.
- **git init هم انجام شد** (متادیتا روی fs امن ساخته و verify شد؛ ‏`.git` خراب قبلی → `_Duplicates/broken-dot-git-*`).
- تست پذیرش: link-checker = فقط ۱ شکستهٔ از-قبل‌موجود · frontmatter بدون خطای نو · لاگ کامل: `nonmd-move-log-2026-07-06.csv` (همین پوشه).
- **rollback:** همه‌چیز mv بود + snapshot git — هیچ حذفی رخ نداد.
