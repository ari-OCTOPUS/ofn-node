# MEMORY-EVIDENCE-INTEGRITY — 2026-09-03

## لایه‌های حقیقت و وضعیتشان
1. **runtime** — سالم و غنی (پورت‌ها/تایمرها/sqlite/فایل‌های state)؛ رسیدِ missing فقط برای journal 138 (دید کاربر) و مسیر دکتر 138.
2. **repo/evidence ledger** — بورد مالک append-only سالم؛ اما والتنِ گیتِ F:\backup با **dirty=400 روی برنچ rescue** = ریسک لغزندگی رسیدها.
3. **checkpoint/notes** — README دکتر (157/157) کهنه در برابر 168/168 اندازه‌گیری‌شده (09-02، دو بار). سند MISSING-WIRING-50 دو موردش همین امروز کهنه شد (NTP✓، 138-drain✓) — خودِ سند باید History بنویسد نه رونویسی.
4. **agent memory** — ۴۵ مدخل؛ دو مورد امروز توسط parallel session بازنویسی/حذف شده بود (الگوی تکراری) — اسکریپت repair-memory-index.ps1 سپر شد (24/24 سپس 45/45).
5. **git history** — سالم (squash-merge‌ها؛ برچسب PR ملاک نه ancestry).

## mirrorها/دوقلوها/redirectها
- CURRENT-TRUTH: کانونیکال = owner-board؛ خطِ ماشین `OCTOPUS\CURRENT-TRUTH.md` جدا (دست‌نخورده ماند)؛ بقیه mirrorها pointer (سیاست 09-02) — این پاس mirror محتوادار جدید دیده نشد (راند دکتر 13-یافته‌ای 09-02: mirror=0).
- دوقلوهای phase0 (A-halt 1875 / isolated 1879 md) هنوز hash-diff نشده‌اند — تفاوتشان UNKNOWN.
- قراردادهای BB-×9 فقط در دوقلو؛ ریشهٔ زنده بی‌قرارداد.

## لینک‌های شکستهٔ شناخته‌شده (بازتأیید از راند 09-02)
- ۳ مردهٔ واقعی در 01-TRUTH (C-NNN wildcard→امروز بازلنگر شد؛ verify_live_store ×۲→strike شد).
- ۱۱ unanchored (فایل جای دیگر است) — LOW با کاندیدا.
- بازهٔ گم‌شدهٔ ۳۲۸-۴۶۳ در سرشماری ۵۶۵-آیتمی قدیم (MASTER-BACKUP) — حفرهٔ شواهد داخل خودِ سرشماری.

## تناقض‌ها (خلاصه؛ کامل در CONTRADICTIONS.md)
C-١ روایت first-send · C-٢ NTP · C-٣ وضعیت outbox سه‌اسنپ‌شات · C-٤ telegram_bridge ignition · C-٥ fullest-tree vs deployed · C-٦ journal vs timers · C-٧ dirty=400 vs append-only · C-٨ 157-vs-168.
