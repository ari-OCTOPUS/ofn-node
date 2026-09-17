# OCTOPUS-FORGOTTEN-ITEMS — حافظهٔ گم‌شده/فراموش‌شده 2026-09-17
# lane: OCTOPUS-UNIFIED-RECOVERY-20260917 · هیچ‌کدام حذف/ادغام نشدند — فقط ثبت (حکم مالک 2A)

## ۱. در repoها (ofn-node)
- **۱۵۷ شاخهٔ unmerged — همه با commit جلوتر از main** (فقط ۸ از ۱۶۵ merge شده‌اند). بزرگ‌ترین‌ها: `codex/executor-safety-20260915` و `receipts/durability-snapshot-20260916` (هر ۲۱۳ جلوتر)، `rescue/octopus-live-tree-20260821` (۲۰۹، آخرین کامیت Jul-14)، `docs/octopus-os-incidents-20260902` (۱۲۶)، `rootfix/phase1-rca-20260916` (۱۱)، `landing/release-p0-20260902` (=PR#71، ۱۰). جزئیات: BRANCH-ANALYSIS.csv.
- **۲۳۲ commit پنجرهٔ اخیر، همه branch-only** (صفر روی main) — پیشرفت واقعی در صف merge نشسته.
- **runtime 138 روی `63938eb` (main محلی) که در GitHub main نیست** + ۴۵ dirty — بدنهٔ deploy جلوتر از کانون سورس.
- `F:\ofn-node` روی `fix/opslib-import-boundary` با ۰da921b محلی جلوتر از remote خودش (5e3254f) — کار محلی unpushed + ۲۴۶ dirty.
- ۶ تست قرمز pre-existing روی main (نام‌شان در RECON-REPORT lane قبلی).
- PRهای stale: #251 #248 (از 09-09)، #242 (09-08)، #212 #211 #215 (09-06).
- فایل `.obsidian/` داخل خود repo (۳ فایل) — پیکربندی Obsidian در سورس.

## ۲. در والت (census امروز: 71,235 فایل/16.5GB)
- **7,082 نوت orphan** (بدون لینک ورودی) · **1,052 لینک شکسته** (baseline) · **7,026 گروه duplicate با hash برابر** · 530 تداخل نام نوت.
- **`.claude/worktrees` داخل F:\backup = 121,718 فایل / 32.3GB** — بزرگ‌ترین جرم فراموش‌شده (کلاس excluded؛ سیاست 2A: حفظ + pointer).
- ۶۴,۵۶۲ فایل در ۷ ریشهٔ vault تودرتو + ۱۷۴ `.obsidian` در کل درایو F.
- **۱۲ نسخهٔ CURRENT-TRUTH**؛ نقش `01-TRUTH/CURRENT-TRUTH.md` نامعلوم.
- ۲۶۴ فایل با نام sensitive (فقط طبقه‌بندی نام — محتوا هرگز خوانده نشد).
- دو فایل NUL ویندوزی (نام رزروشده) که ابزارها را می‌شکنند (۲ خطای census).

## ۳. بین‌سیستمی
- `langar`: موتور خفته با service-file که نصب نیست + `_verify/` سایه + `.fuse_hidden` tracked + P1 امضا (اندازه‌گیری مجدد نشده).
- `vbaa-patches`: ۳ primitive تست‌سبز که هیچ مسیر adoption ندارند (قرارداد انتقال غایب).
- `Armin`: ۵ فایل سند؛ نقش اجرایی صفر (تأیید ممیزی + runtime).
- ۲ alert باز `telegram_bot_token` (rotation = «بعداً»).
- تناقض باز AUTO1 (سه‌گانه: season/registry/sender-identity) · G22 (unverified) · CHECKOUT-1 (بسته — هرگز دوباره پرسیده نشود).
- واگرایی نام kill-switch: مستند=`HALT`، کد main=`HALT-ALL` (تأیید سورس امروز).
- workflows به نام observation-* هنوز فعالند درحالی‌که مفهوم OBSERVATORY بازنشسته است.

## قاعده
طبق حکم مالک 2A هیچ‌یک از این موارد حذف/merge/archive نمی‌شود؛ هر اقدام آینده = جراحی کلاس‌بندی‌شده در OCTOPUS-SURGICAL-ROADMAP.md با رأی مالک.
