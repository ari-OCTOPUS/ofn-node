# کارت صبحگاهی — 2026-08-17 (ایجنت شب‌کار: معمار ارشد)

> هر کارت: بله/نه. پچ‌ها و دستورات آماده‌اند؛ هیچ‌کدام بدون رأی شما اعمال نشده.

## کارت ۱ — گیت enabled() در approve/reject (C-026، مصوب، ولی فایل TCB است)

**چرا:** پیشنهادِ ساخته‌شده حین ON، بعد از OFF هم قابل تصمیم است؛ گیت دو خط آن را می‌بندد.
**چرا کارت ماند:** `brain/self_code.py` جزو ۱۴ فایل مرز اعتماد است — ویرایش بدون امضای مجدد = halt.
**سه قدم صبح (۲ دقیقه):**
```powershell
cd F:\backup
# ۱) اعمال پچ (daemon شاید موقتاً halt کند — عادی است)
git apply "00 - Inbox/PATCH-C026-self_code-enabled-gate.patch"
# ۲) بازتولید manifest
cd 4d_system; py scripts/generate_trust_boundary.py; cd ..
# ۳) امضا + وریفای
openssl pkeyutl -sign -inkey "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem" -rawin -in "4d_system\config\trust-boundary.json" -out "4d_system\config\trust-boundary.json.sig"
openssl pkeyutl -verify -pubin -inkey "_ops\owner-signing\octopus-owner-ed25519-public.pem" -rawin -in "4d_system\config\trust-boundary.json" -sigfile "4d_system\config\trust-boundary.json.sig"
```
**بعد:** دو تست xfail سخت‌گیر `test_seam_selfcode_gate_20260816.py` را به positive ارتقا ده (حذف نشانگر). rollback: `git checkout -- 4d_system/brain/self_code.py` + regen + sign.

## کارت ۲ — مولد octo-data.js (worlds)

**چرا:** `worlds/octo-data.js` از 07-13 به‌روز نشده — مولدش در ۲۰ استخراجگر فعلی refresh-live-data نیست. مسیر ارجاع فیکس شد ولی خود داده کهنه است.
**پیشنهاد:** یا استخراجگرش را به bat برگردانیم، یا worlds را به graph-data زنده وصل کنیم. بله/نه.

## کارت ۳ — داشبوردهای پرچم‌دار (index + 01..05 + 3d)

**چرا:** این ۷ صفحه «نقشهٔ معماری» استاتیک‌اند (by design، بدون ادعای داده). اگر می‌خواهید «داشبورد داده» شوند، باید به ستون nervous-system سیم شوند (نیم‌نشست کار).
**پیشنهاد:** نگه‌داشتن به‌عنوان نقشه (فعلاً) / سیم‌کشی / هر دو با تب جدا. بله/نه.

## کارت ۴ — نمونه‌گیری scheduler (مصوب مکانیزم، نرخ خاموش)

**چرا:** مکانیزم امشب نصب شد (پیش‌فرض ۱.۰ = بی‌اثر). روشن‌کردن 0.1 یعنی لجر ژنوم از ~۵۲۰ رویداد/روز scheduler به ~۵۲ می‌رسد.
**پیشنهاد:** `set_actor_sampling("scheduler", 0.1)` در نقطهٔ بوت لجر + ری‌استارت. بله/نه.
