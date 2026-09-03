# MIRROR-CLEANUP-20260902 — رسید پاکسازی آینه‌های والت

---
schema: octopus.vault.cleanup.v1
issued_utc: 2026-09-02T04:50:00Z
author: ari322 local agent session (F:\ scope)
owner_go: "ابسیدین رو بروز کن و همه چیو مرتب کن میخوایم اپدیتای بعدی رو روی این دایرکتوری پیاده کنیم" (owner, 2026-09-02) — اجرای MIRROR-01 (D-34-open-decisions.csv) با درمان pointer طبق D-33 §E
scope_measured: "سرشماری کانونی‌شدهٔ فایل‌های CURRENT-TRUTH/OWNER-BOARD در F:\backup (با شاخه‌زنی node_modules/.git/آرشیوها) + هش sha256 همهٔ نسخه‌ها"
scope_not_measured: ["محتویات کامل پوشه‌های تویین فراتر از CURRENT-TRUTH (BOARD.md/SEASON-LOG.md آن‌ها دست‌نخورده ماند)", "OCTOPUS/CURRENT-TRUTH.md (machine-written — عمداً دست‌نخورده)", "پوشه‌های پشتیبان خارج از والت"]
---

## چکار شد

قانون: کانونیکال می‌ماند، آینه‌ها pointer یک‌خطی می‌شوند، محتوای قدیمی هش‌پیچ در 99-ARCHIVE، 01-TRUTH به redirect تبدیل شد نه حذف. **همهٔ به‌روزرسانی‌های بعدی فقط در همین پوشهٔ کانونیکال (06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24) پیاده می‌شوند.**

## جدول: ۹ آینهٔ CURRENT-TRUTH

| # | مسیر | هش قدیم | سرنوشت |
|---|---|---|---|
| ۱ | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md` | fad882560c88 | **کانونیکال — دست‌نخورده** |
| ۲ | `01 - Dashboard/OCTOPUS-OWNER-BOARD/CURRENT-TRUTH.md` | 8b08dcd3d4d1 | → pointer (خلاصهٔ مشتوع امروز آرشیو شد) |
| ۳ | `01-TRUTH/CURRENT-TRUTH.md` | 6b0e10c09aed | → redirect (هدر بالای محتوای ۱۵ اوت حفظ شد) |
| ۴ | `00 - Inbox/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md` | c8485fad401c | → pointer |
| ۵ | `07-HANDOFF/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md` | c8485fad401c | → pointer |
| ۶ | `agent-prompts/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md` | c8485fad401c | → pointer (+ خط SUPERSEDED روی README پوشه) |
| ۷ | `06-EVIDENCE/FUGU-BIZ-SPRINT-2026-08-24/OWNER-BOARD/CURRENT-TRUTH.md` | c8485fad401c | → pointer |
| ۸ | `06-EVIDENCE/FUGU-BIZ-SPRINT-2026-08-24/cockpit/CURRENT-TRUTH.md` | c8485fad401c | → pointer |
| ۹ | `03 - Projects/Lead-نقاشی/06-Board/OCTOPUS-OWNER-BOARD/CURRENT-TRUTH.md` | c8485fad401c | → pointer |
| ۱۰ | `03 - Projects/Ziman Galerry/06-Board/OCTOPUS-OWNER-BOARD/CURRENT-TRUTH.md` | c8485fad401c | → pointer |
| ۱۱ | `03 - Projects/اونلی فنز/06-Board/OCTOPUS-OWNER-BOARD/CURRENT-TRUTH.md` | c8485fad401c | → pointer |

پس از D-34 (شش کپی)، پنج کپی دیگر پیدا شد: هر پنج همان snapshot دوقلوی ۲۴ اوت (c8485fad401c). بیماری از عدد اولیه بزرگ‌تر بود — عین پیش‌بینی pointer ریشه.

## استثنا: OCTOPUS/CURRENT-TRUTH.md

آینه نیست — تبار جدا: `type: octopus-auto`، ۱۳KB، محتوا از ۲۰۲۶-۰۸-۱۱ تا امروز، و نویسنده‌های فعال کد هستند (`_ops/agi2027_control/runtime.py`، `_ops/cortex/cortex.py`، `_ops/telegram_center/miniapp_state.py`، `_refresh_obsidian.py`). عمداً دست نخورد — تبدیلش نویسنده‌ها را می‌شکند یا توسطشان بازنویسی می‌شود. دو خط truth (انسانی/ماشینی) حالا رسماً از هم تفکیک شده‌اند.

## آرشیو

همهٔ محتوای قدیمی (۱۰ فایل، نام‌مسطح با مسیر اصلی) در `99-ARCHIVE/mirror-cleanup-20260902/` — حذف صورت نگرفت (قانون append-only).

## pointer ریشهٔ والت

`F:\backup\OCTOPUS-OWNER-BOARD.md` بازنویسی شد: سیاست آینهٔ جدید + فهرست محل‌های pointer + تفکیک دو خط truth.

## آنچه نسنجیدم

پوشه‌های board فراتر از عمق ۵ در Projects؛ فایل‌های غیر-CURRENT-TRUTH پوشه‌های تویین؛ صحت اینکه هیچ process ای جز نویسنده‌های فهرست‌شده فایل octopus-auto را نمی‌نویسد.

## الحاقیه (همان شب) — ریشهٔ عمیق‌تر پیدا شد

سرشماری کاملِ پس‌از-پاکسازی (pruned find) یک منبع تکثیر بزرگ‌تر لو داد: **`.claude/worktrees/` داخل خود والت، ۷+ کپی کامل از کل درخت والت** را نگه می‌دارد (worktree های Claude مورخ ۲۰۲۶-۰۸-۳۰: octopus-docs-sync ×2، octopus-reality، core-live-cl01، fugu-ultra-remediation، great-spence، hybrid-control-plane، octopus-p0-fixes، organism-alive، sul-brain/heart/memory، telegram-operational-control) — هر کدام با نسخه‌های پیشا-پاکسازی همهٔ آینه‌ها. این‌ها عمداً دست نخوردند (تصمیم حذف/نگهداری با مالک)؛ خطر resurrect از این مسیر در pointer ریشه قید شده. هیچ فایل TRUTH دیگری خارج از پوشش این رسید به‌عنوان آینهٔ برد مالک شناسایی نشد (فایل‌های TRUTH نام‌دار دیگر — Architecture Maps، OCTOPUS-PRIME، continuity — تبارهای مستقل تاریخی‌اند، نه آینه).
