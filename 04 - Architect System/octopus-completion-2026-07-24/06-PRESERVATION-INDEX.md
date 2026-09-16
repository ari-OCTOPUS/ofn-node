---
type: preservation-index
title: OCTOPUS Preservation & Recovery
date: 2026-07-24
status: reference
---

# 🛟 OCTOPUS — فهرستِ حفاظت و بازیابی (2026-07-24)

> **اصل:** در کلِّ پاک‌سازی، هیچ‌چیزِ منحصربه‌فرد پاک نشد. هر کارِ کامیت‌نشده و هر برنچِ حذف‌شده در git محفوظ است. این سند = نقشهٔ بازیابی.

## ۱) دلتاهای worktree — `refs/rescue/*` (۲۰ عدد)
وقتی ۳۷ worktree حذف شد، **کارِ کامیت‌نشدهٔ هرکدام** (tracked + untracked) در یک commit ذخیره و به `refs/rescue/<name>` اشاره داده شد.
- **دیدن:** `git for-each-ref refs/rescue/ --format='%(refname:short) %(objectname:short)'`
- **بازیابیِ محتوا:** `git checkout refs/rescue/<name>` یا `git show refs/rescue/<name>`
- **مثال‌های ارزشمند:** `rescue/charming-keller-b87cd0` (آزمایشِ C3 self-improvement)، `rescue/coin-hunter-bot-arch-d49739` (اسنادِ Mining)، `rescue/youthful-saha-5ee551` (اسنادِ Ziman).

## ۲) پایهٔ worktreeهای detached — `rescue-base/*` (۲ عدد)
`rescue-base/c3fix-verify` (`67f1a71`) و `rescue-base/c7-wt` (`e2a317c`) — کپیِ کاملِ vault بودند (تأییدشده ۱۴۹/۱۴۹ = master؛ فقط برای اطمینان نگه داشته شد). `c7-wt`‌ی `ins.py` هم در `_worktree-rescue-2026-07-24/c7-wt/`.

## ۳) برنچ‌های حذف‌شده — `archive/*` tags
- **`archive/pc-2026-07-24/*` (۱۱):** برنچ‌های «۰-unique» که محتواشان از قبل در master بود.
- **`archive/superseded-2026-07-24/*` (۱۱):** برنچ‌های منسوخ (کارشان در برنچِ کانونیِ نگه‌داشته‌شده جمع شده).
- **دیدن:** `git tag -l 'archive/*'` · **بازگردانِ برنچ:** `git branch <name> archive/superseded-2026-07-24/<name>`

## ۴) نیت‌های حفظ‌شده (از `session-f92f3d` قبل از حذف)
دو نیتِ مالک که فقط داک بودند (صفر کد)، اینجا ثبت شد تا گم نشود (کاملش در `archive/superseded-2026-07-24/session-f92f3d`):
- **fusion-lab:** stagingِ پای پژوهشیِ `SHADOW_ONLY` + پرامپتِ canonical v1.0.0 (صفر کد/فلگ تا رأیِ مالک).
- **WLOS:** مربیِ تعاملیِ تلگرام + مسیرِ امنِ الحاقِ داده (صفر دادهٔ سلامت، صفر کد/فلگ).

## ۵) پوشهٔ rescueِ فایلی
`F:\backup\_worktree-rescue-2026-07-24\` — پچِ `admiring-galileo` (۶ ویرایشِ `_ops`: accountant/approval_channel/تست‌ها) + `c7-wt/ins.py`. **قابلِ حذف** پس از اطمینان (این‌ها در `refs/rescue`/tagها هم هستند).

## ۶) پاک‌سازیِ نهاییِ refهای حفاظتی (اختیاری، خیلی بعد)
وقتی مطمئن شدی هیچ‌کدام لازم نیست:
```powershell
git for-each-ref refs/rescue/ --format='%(refname)' | % { git update-ref -d $_ }
git tag -l 'archive/*' | % { git tag -d $_ }
git tag -l 'rescue-base/*' | % { git tag -d $_ }
git gc --prune=now
```
> تا آن‌موقع نگه‌دار — بی‌وزن‌اند و تنها تورِ ایمنیِ برگشت‌اند.
