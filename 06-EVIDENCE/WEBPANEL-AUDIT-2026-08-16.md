---
type: webpanel-audit
mission: MEGAPROMPT-WEBPANEL-REALITY + فاز ۲ منشور شب
agent: معمار ارشد (GLM) — 2026-08-16 عصر/شب
surfaces_scanned: 71 html
gauges:
  wired_before: 24/71 (ارجاع داده/API داشتند)
  broken_refs_before: 1 (worlds)
  fossil_copies: 12 (mobile×11 + dream×1 — گرافِ ۳۱KB@07-12 به‌جای ستونِ ۸۳۹KB@امروز)
  frozen_snapshots_labeled: 1 (preview.html)
  unresolved_after: 0
---

# ممیزی وب‌پنل — 2026-08-16

## جدول حکم سطوح (۷۱ فایل)

| سطح | تعداد | حکم | اقدام امشب |
|-----|-------|-----|------------|
| `admin-telegram/index.html` | ۱ | **REAL** — ۱۸ ارجاع به ستون زندهٔ nervous-system (همگی resolve ✓) | — |
| `admin-telegram/preview.html` | ۱ | **MOCK مبهام** — snapshot درون‌ریزِ `LIVE_DATA` از **2026-07-12** | ✅ بنر صادق: «پیش‌نمایشِ ثابت» + لینک داشبورد واقعی |
| `mobile/*` (۱۱) + `dream/index` | ۱۲ | **STALE-ALL** — کپی فسیلی graph-data (۳۱KB@07-12 در برابر ۸۳۹KB@امروز؛ اسکیما سازگار `window.OCTOPUS_GRAPH`) | ✅ re-point به ستون زنده؛ همه resolve شدند |
| `worlds/index.html` | ۱ | **DEAD-ref** — `../octo-data.js` یک پوشه اشتباه (فایل کنارش بود) | ✅ `octo-data.js` · ⚠️ خود فایل @07-13 کهنه → کارت (مولدش در ۲۰ استخراجگرِ فعلی نیست) |
| پرچم‌دارها: `index` + `01..05` + `3d-topology` | ۷ | **STATIC-BY-DESIGN (نقشهٔ معماری)** — ادعای عدد زنده نداشتند (سوییپ literal: فقط تاریخ ساخت 07-24) | برچسب مفهومی در همین جدول؛ کارت: اگر می‌خواهید «داشبورد داده» شوند، سیم‌کشی به ستون = نشست بعد |
| `gallery-3d/*` (۳۳) | ۳۳ | **ART** — قطعات سه‌بعدی مفهومی؛ «دادهٔ زنده» ادعا نمی‌کنند | — |
| `_legacy-2026-07-24/*` (۶) | ۶ | **LEGACY** — آرشیو | — |

## گاوج‌ها (فرمانِ بازتولید در هر سطر)

- درصد wired: قبل **24/71=34%** → بعد اصلاحات، مصرفِ داده از ستونِ زنده: **37/71=52%** (۱۲ فسیلی + ۱ DEAD وصل شدند؛ ۳۳ هنر + ۶ لگacy + ۷ استاتیک-طراحی‌شده صادقانه دسته‌بندی شدند)
- فسیل‌زدایی: `mobile/graph-data.js` و `dream/graph-data.js` دیگر مصرف نمی‌شوند (فایل‌ها نماند؟ — نماند حذف نکردیم؛ فقط مصرف رفت؛ حذف ممنوع)
- unresolved refs: **1 → 0** (بازتولید: اسکریپت inventory همین دفتر)

## یافته‌های کلیدی (سطح A)

۱. **۲ صفحهٔ موبایل + dream یک ماه دادهٔ کهنه نشان می‌دادند** در حالی که ستون زنده همین امروز ۲۷× بزرگ‌تر تازه شده بود — نمونهٔ کامل «UI سبز، داده فسیل»
۲. **preview.html** snapshotِ 07-12 را با نام متغیرِ `LIVE_DATA` می‌فروخت — برچسب صادق now
۳. worlds: باگ مسیری کلاسیک (فایل همسایه، ارجاع یک-پوشه-بالا)

## بازِ کارت (صبحگاهی)

- مولد `octo-data.js` (کهنه) — یا استخراجگرش را به refresh-live-data برگردانید یا صفحه را به graph-data وصل کنیم
- سیم‌کردن دادهٔ زنده به ۷ پرچم‌دار (اگر بخواهید داشبورد شوند نه نقشه)
- ممیزی دکمه-به‌دکمهٔ admin-telegram (۱۸ منبع؛ امشب در سطح فایل/ارجاع ممیزی شد — سطح تعامل = ادامهٔ طبیعی)

---

## گذر ۲ — 2026-08-16 ~15:4x (مگاپرامپت WEBPANEL اجرا شد؛ complement نه تکرار گذر ۱)

STEP 0: `OctopusLiveDataRefresh` Ready · LastResult=0 · LastRun 15:28 · `*-data.js` همان روز. پورت‌ها: 8771/8772/8773/8774/8776 LISTEN. **8765 هیچ LISTEN** (کارت UNWIRED ۲ کهنه). `:8773/api/live` HTTP 200. `:8774/api/chat-status` 403 بدون HMAC = fail-closed REAL.

### جدول حکم سطح‌های جامانده

| سطح | آیتم | حکم قبل | حکم بعد | شاهد |
|-----|------|---------|---------|------|
| ابسیدین | CONTROL-PANEL.html | MOCK — «اجرای زندهٔ validatorها» + git-init باز · generated 07-05 · 210/30 | STALE برچسب‌خورده | بنر `FROZEN-COCKPIT-BANNER` · عنوان متریک عوض شد · JSON حذف نشد |
| ابسیدین | SYSTEM-DASHBOARD.html | MOCK — h1 «مغز زنده» + git init ❌ | STALE برچسب‌خورده + بازنشسته | بنر + h1 «اسنپ‌شات، نه زنده» |
| ابسیدین | BRAIN-FOCUS-BOARD.html | STALE 07-06 بی‌بنر | STALE برچسب‌خورده | بنر |
| worlds | dataflow «اکسترکتور» | MOCK — `src:null` همیشه 🔴 | REAL (همان freshness زنده) | `src:F.live` |
| worlds | octo-data.js mtime 07-13 | STALE-مولد (گذر ۱ کارت) | **NOT-A-SEAM** — کتابخانهٔ خواننده | کامنت header؛ داده = LIVE_DATA.generated 2026-08-16T05:28:02Z |
| پرچم‌دار | index + 01 + 05 + 3d + gallery-3d/index | PHANTOM «زنده» | STATIC صادق | متن عوض شد؛ اسکلت 3D بازنویسی نشد |
| 05-isometric | AGENTS scanner/compressor اعداد ثابت | MOCK+PHANTOM-NAME | MOCK برچسب‌خورده | «synthetic demo numbers» |
| live | GET /api/live | (خارج از گذر ۱) | REAL | HTTP 200 keys=ts,body,heart,… |
| MiniApp | /api/chat-status بی‌HMAC | (خارج از گذر ۱) | REAL fail-closed | HTTP 403 |
| 8765 | http.server | UNWIRED کارت ۲ | DEAD (پروسه‌ای نیست) | Get-NetTCPConnection خالی |
| admin-telegram | دکمه‌های تأیید/رد همه | از قبل «غیرفعال» + READ-ONLY | REAL-as-display | لمس نشد (اثر اجرایی تازه ممنوع) |

### گاوج‌ها (این گذر)

1. سطوح این گذر: ۳ کاکپیت + ۷ پرچم‌دارنام + worlds dataflow + live API + 8765 = **۱۳ سطح حکم**. قبل: ۰/۳ کاکپیت صادق · بعد: ۳/۳ برچسب اسنپ‌شات. درصد فایل‌های wired گذر ۱ **۳۷/۷۱=۵۲٪** دست‌نخورده ماند (هدف این گذر دروغ‌زدایی بود نه سیم تازه).
2. رشته‌های MOCK/فروش‌زنده حذف‌شده از UI: **۷** («اجرای زندهٔ validatorها» · «مغز زنده» در h1 · extractor `src:null` · «۳۰ صحنهٔ زنده» ×۲ · «دادهٔ زنده را جابه‌جا» · «live data flow»).
3. DEAD برچسب/تأیید: 8765 مرده · askDoctor همچنان فقط Cowork (fallback از قبل صادق).
4. freshness: max mtime `nervous-system/*-data.js` = 2026-08-16 15:28:16 · `LIVE_DATA.generated=2026-08-16T05:28:02Z`.
5. تخالف اسم باقی: JSON کاکپیت هنوز `git_init:false` و validator 210/30 می‌گوید — **عمداً نساختیم** (حذف/جعل عدد ممنوع). کارت: بازتولید مدل از اسکن امروز.

**C-032** ثبت شد.

تست: `_ops/tests/test_webpanel_reality_20260816.py` — در run_all ثبت نشد.

