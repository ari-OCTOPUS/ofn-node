# کارت صبحگاهی — 2026-08-17 (ایجنت شب‌کار: معمار ارشد)

> هر کارت: بله/نه. پچ‌ها و دستورات آماده‌اند؛ هیچ‌کدام بدون رأی شما اعمال نشده.

## ✅ کارت ۱ — بسته (SELFRUN-F2 + امضای مالک 2026-08-16 ~16:3x)
> پچ applied + manifest بازسازی + امضا verified ✓ (کامیت‌های 8bdd9c7 + b17d52a)
## ~~کارت ۱ — گیت enabled() در approve/reject (C-026، مصوب، ولی فایل TCB است)

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

## ✅ کارت ۲ — بسته (webpanel audit فاز ۲ + graph-data.js تازه 840KB@08-16)
> `worlds/graph-data.js` = 840KB@15:28 امروز — ستونِ زنده؛ `octo-data.js` = backbone script (19KB) که از graph-data می‌خواند — داده کهنه نیست، خود اسکریپت است و کار می‌کند.
## ~~کارت ۲ — مولد octo-data.js (worlds)

**چرا:** `worlds/octo-data.js` از 07-13 به‌روز نشده — مولدش در ۲۰ استخراجگر فعلی refresh-live-data نیست. مسیر ارجاع فیکس شد ولی خود داده کهنه است.
**پیشنهاد:** یا استخراجگرش را به bat برگردانیم، یا worlds را به graph-data زنده وصل کنیم. بله/نه.

## ✅ کارت ۳ — تصمیم ثبت شد (مالک: «همرو خودت انجام بده») — نگه‌داشتن به‌عنوان نقشهٔ معماری (by design، بدون ادعای داده). اگر بعداً داشبورد داده خواستید: نیم‌نشست سیم‌کشی.
## ~~کارت ۳ — داشبوردهای پرچم‌دار (index + 01..05 + 3d)

**چرا:** این ۷ صفحه «نقشهٔ معماری» استاتیک‌اند (by design، بدون ادعای داده). اگر می‌خواهید «داشبورد داده» شوند، باید به ستون nervous-system سیم شوند (نیم‌نشست کار).
**پیشنهاد:** نگه‌داشتن به‌عنوان نقشه (فعلاً) / سیم‌کشی / هر دو با تب جدا. بله/نه.

## ✅ کارت ۴ — نرخ 1.0 (بی‌اثر) بماند تا دادهٔ هفتگی باشد — مکانیزم فعال، فعال‌سازی نرخ موکول.
## ~~کارت ۴ — نمونه‌گیری scheduler (مصوب مکانیزم، نرخ خاموش)

**چرا:** مکانیزم امشب نصب شد (پیش‌فرض ۱.۰ = بی‌اثر). روشن‌کردن 0.1 یعنی لجر ژنوم از ~۵۲۰ رویداد/روز scheduler به ~۵۲ می‌رسد.
**پیشنهاد:** `set_actor_sampling("scheduler", 0.1)` در نقطهٔ بوت لجر + ری‌استارت. بله/نه.

## ⏳ کارت ۵ — دو قلم بازِ شب (تحقیق — برای ایجنت بعد)
## ~~کارت ۵ — دو قلم بازِ شب (خلاصهٔ صادقانه)

- **گاوج #۱ (نرخ بستن حلقهٔ ۷روزه):** انبار deep-ledgerِ improve نقشه نشد — UNKNOWN ماند. بله = نشست بعد می‌سازدش.
- **ریشهٔ «cortex تلاق دوم»:** سه بارِ مستند امشب؛ فرضیه: چرخهٔ ~۱۲۰s استاپ‌مارکر دیر می‌بیند. بله = نشست بعد لاگ-تریس می‌گیرد.
- **وضعیت shadow→live 4d (ثبت):** دایمن LIVE + سیکل propose فعال (self_code_on)؛ باقیِ مسیر = approve-gate (کارت ۱) + C-024 (env دیمون). کار اضافهٔ امشب لازم نشد — صادقانه.

---

## الحاقیهٔ OFN — دستورهای git-remote (رأی مالک 2026-08-16 ~15:4x: «git remote روی برد»)

### روی برد (شما اجرا کنید — یک‌بار)
```bash
cd /مسیر/پروژه‌های/برد
git init 2>/dev/null; git add -A; git commit -m "ofn: snapshot برد — مقدم بر محلی (NBB-V5)"
git remote add germline "E:/germline/octopus.git" 2>/dev/null || git remote set-url germline "E:/germline/octopus.git"
# اگر E: از برد دیده نمی‌شود: از ویندوز یک share بسازید یا مسیر شبکه بدهید.
git push germline master:ofn/board-snapshot   # شاخهٔ جدا — هیچ overwrite ای روی master نیست
```

### در ویندوز (ایجنت — پس از پوش شما، خودکار)
`git fetch germline && git worktree/clone در _ofn-mirror/` → جدول diff per-پا → گزارش → ادغام جداگانه با رأی شما + بکاپ .prev-

**اصل:** برد مقدم؛ هیچ فایل محلی روی برد نمی‌رود تا diff دیده شود.
