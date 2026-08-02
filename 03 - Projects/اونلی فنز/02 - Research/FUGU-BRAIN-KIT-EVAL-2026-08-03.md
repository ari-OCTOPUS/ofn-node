---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: ready
tags: [creator-business, marketing, tooling]
created: 2026-08-03
updated: 2026-08-03
---

# ارزیابی «Fugu Brain + Growth Module» — راستی‌آزمایی با اجرا (2026-08-03)

> کیت خارجی ساختهٔ جلسهٔ دیگر، تحویل مالک روی دسکتاپ (`Desktop\New folder\fugu-brain-and-growth-module.zip`؛ فایل دوم `…module2` کپیِ byte-identical همان zip بدون پسوند است). طبق درس «آرتیفکت خودساخته شاهد نیست»، همهٔ ادعاها با کد و اجرا سنجیده شد — در scratchpad، بیرون از vault.

## ۱. حکم

**کیت تمیز، صادق و propose-only است و ادعاهایش ۱۰۰٪ تأیید شد — ولی «مغز» آن فقط plan-generator است، نه سیستم اجرایی؛ و «MCP»هایش تعریف‌اند، نه سرور.** نیمهٔ باارزش برای ما `growth-archaeologist` است (قابلیتی که در vault معادل کدی ندارد)؛ نیمهٔ `fugu-api-brain` با آنچه در پایتونِ پروژه داریم ~۹۰٪ هم‌پوشان و کم‌عمق‌تر است.

## ۲. راستی‌آزمایی (شواهد اجرا، نه ادعا)

| ادعای جلسهٔ سازنده | نتیجهٔ سنجش |
|---|---|
| تست GA ‏7/7 | ✅ ‏`tests 7 / pass 7 / fail 0`، ‏exit=0 |
| تست Brain ‏5/5 | ✅ ‏`tests 5 / pass 5 / fail 0`، ‏exit=0 |
| پایپ‌لاین analyze→ingest→plan | ✅ سه CLI پشت‌سرهم اجرا شد؛ ‏`brain_plan.json` تولید شد |
| ‏governance برای پروژهٔ OF: ‏`approval_required=true, risk=critical` | ✅ عیناً؛ ‏`adultProject=true`، ‏`dry_run=true`، ۱ approval ِ pending |
| حافظهٔ چندلایه + ingest ِ ماژول | ✅ ۱۲ آیتم در ۵ لایه (policy/project/procedural/evidence/semantic) |
| publishing فقط draft | ✅ تنها ابزار `publishing_create_draft`؛ صفر verb ِ publish/send/post در کل کد |
| ایمنی کد | ✅ صفر تماس شبکه، صفر `child_process`/`eval`، صفر دستکاری secret؛ ‏stdlib ِ Node، آفلاین (~۲٬۲۵۰ خط) |

## ۳. چه چیزش برای ما «نو» است

- **`growth-archaeologist`** — تحلیل کمّی creator/رقیب از دادهٔ دستی: امتیازدهی engagement/repeatability/authenticity/conversion/fit، ‏architecture cards، پلن آزمایش ۳۰روزه، evidence report با schema ِ ورودی/خروجی. **در vault معادل کدی ندارد** — تحقیق رقبای ما همه سند نثری است (COMPETITOR-MARKET-LANDSCAPE). می‌تواند موتور فاز ۳ ِ [[03 - Projects/اونلی فنز/06 - Ops & Runtime/PROP-D5-MINIAPP-SOCIAL-COCKPIT|PROP-D5]] (لاگ A/B و پیشنهاد آزمایش) و تغذیه‌کنندهٔ hypotheses ِ VaultBank باشد. آفلاین و propose-only = سازگار با قواعد.
- **الگوهای دوزبانهٔ گاردریل** — regexهای block/approval ِ کیت فارسی هم دارند («زیر سن»، «اخاذی»، «دایرکت»…). **گپ واقعی ما را رو می‌کند: همهٔ denylistهای موجود پروژه (`_BANNED_COPY`/`_BANNED_DM`/`FORBIDDEN_TERMS`/scrub ِ pf_os) فقط لاتین‌اند** — «سیدنی» فارسی رد می‌شود. این ایده مستقل از کیت قابل‌adopt است.
- تاکسونومی حافظهٔ ۷لایه و contractهای نسخه‌دار — به‌عنوان الگوی سند، نه کد.

## ۴. چه چیزش تکراری/کم‌عمق‌تر از داشته‌های ماست

`fugu-api-brain` ‏(memory/governance/approval/registry/planner) در برابر آنچه داریم: صف‌های واقعی با state machine ِ قفل‌شده و تست (`acquisition_pipeline`/`dm_pipeline`)، ‏audit ِ origin-stamped، گاردهای fail-closed ِ سیم‌شده به کاکپیت تلگرام و gateway ِ 8774، ‏capability registry ِ pf_os با دلیل پویا. کیت هیچ‌کدام را اجرا نمی‌کند — فقط JSON ِ پلن می‌سازد. **مغز سوم** (بعد از DualBrainV3 و pf_os ِ incubating) خلاف روح ADR ِ [[03 - Projects/اونلی فنز/00 - Control/PF_OS_CANONICALITY|PF_OS_CANONICALITY]] است.

## ۵. گپ‌های صادقانهٔ خود کیت

- ابزارهای research/analytics/strategy فقط **entry ِ رجیستری‌اند، پیاده‌سازی ندارند** («MCPها آماده شدند» = تعریف‌شده، نه ساخته‌شده).
- گاردریل substring-based و دورزدنی است (همان محدودیت denylistهای خودمان؛ خود کد اذعان دارد).
- جستجوی حافظه keyword-scoring است نه embedding؛ ‏idempotency فقط در حد `stableId`.
- برای production خودش ۸ پیش‌نیاز لیست کرده (vault ِ credential، صف job، ‏PostgreSQL، ‏OAuth…) — یعنی فاصلهٔ واقعی تا «کنترل زنده» را صادقانه گفته.

## ۶. پیشنهاد ادغام (verdict مالک)

1. **ADOPT ‏(پیشنهادی): `growth-archaeologist`** به‌عنوان ابزار تحلیلی مستقل آفلاین — ورودی: دادهٔ دستی رقبا/کریتورها با schema ِ fixtures؛ خروجی: architecture cards + پلن آزمایش → ثبت در `02 - Research` و خوراک فاز ۳ مینی‌اپ. محل نگهداری کد و نحوهٔ اجرا (Node ِ محلی) = رأی مالک؛ تا آن موقع کیت روی Desktop می‌ماند، کپی کاری در scratchpad.
2. **ADOPT ‏(پیشنهادی): دوزبانه‌کردن denylist/scrubهای موجود** — افزودن الگوهای فارسی به `_BANNED_*` ِ brain و `_PII_TERMS` ِ pf_os (کار کوچک، تست‌پذیر، بدون فلگ جدید).
3. **REJECT ‏(پیشنهادی): `fugu-api-brain` به‌عنوان مغز/رانتایم** — تکرارِ کم‌عمق‌ترِ داشته‌ها؛ فقط contractها/تاکسونومی‌اش به‌عنوان مرجع سندی نگه داشته شود.
4. فایل تکراری `fugu-brain-and-growth-module2` روی Desktop = کپی byte-identical ِ zip؛ حذف/نگه‌داشتنش با مالک (بیرون از vault است).

## ۷. منابع

- کد: `scratchpad/fugu-kit/` (استخراج از zip ِ دسکتاپ) — بررسی read-only ِ `governance.js`، ‏`brain.js`، ‏`mcpRegistry.js`، ‏`ingest.js`، ‏`scoring.js` + grep ِ کل درخت.
- اجرا: دو سوییت `node --test` + پایپ‌لاین سه‌مرحله‌ای CLI در scratchpad؛ خروجی‌ها: `ga_out/`، ‏`brain_data/memory.json`، ‏`brain_out/brain_plan.json`.
