---
type: control
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-12
updated: 2026-07-12
created_by: agent
tags: [project-f, handoff, control, os-foundation]
aliases: ["Project-F Handoff", "برنامه ایجنت بعدی"]
---

# 🤝 HANDOFF — برنامهٔ کامل برای ایجنت بعدی (Project-F)

> 🧭 **از اینجا شروع کن:** [[03 - Projects/اونلی فنز/00 - Control/ROADMAP-10-STAGES-2026-07-12|ROADMAP-10-STAGES]] = نقشهٔ راهِ عملیاتیِ بعدی. مرحلهٔ ۱ (GATE 0) دستِ مالک است و کلِ زنجیره را باز می‌کند؛ **کارِ بلافاصلهٔ ایجنت بدونِ نیاز به GATE 0 = مرحلهٔ ۵** (بانکِ کپیِ واقعی + رفعِ باگِ greedyِ learning و سیم‌کردنش، طبق [[03 - Projects/اونلی فنز/06 - Ops & Runtime/PROP-D2-wire-learning-to-acquisition|PROP-D2]]).

> **وضعیت لحظهٔ تحویل (2026-07-12، جلسهٔ اکتساب):** موتورِ اکتساب به‌صورتِ **کدِ propose-only ساخته و تست شد (۲۲/۲۲)** — ولی هیچ افکتورِ زنده، هیچ اکانت، هیچ پست. GATE 0 هنوز باز؛ moves (بلوک B/C) هنوز اجرا نشده. پوسچر = contained propose-only، بدونِ تغییر.

## ✅ انجام‌شده در این جلسه (2026-07-12)

- **کارتوگرافی + ۴ سند کنترل** (00 - Control): CARTOGRAPHY، SOURCE-OF-TRUTH-MATRIX، RISK-LADDER، MIGRATION-MAP (+ بلوک اجراییِ آماده)، همین HANDOFF.
- **بلوک A (docs):** ✅ A1 [[07 - Compliance & Privacy/OPSEC-ITEMS|OPSEC-ITEMS]] · ✅ A3 [[01 - Strategy/STRATEGY-RECONCILE-2026-07-12|STRATEGY-RECONCILE]] · ✅ A2 تازه‌سازیِ `_INDEX` پوشه‌های 01/06/07 · ✅ A5 sync ‏VERDICT_QUEUE. (باقی: A4 بنرِ HOME — انجام شد پایینِ همین جلسه.)
- **بلوک D (proposals، propose-only):** ✅ [[06 - Ops & Runtime/PROP-D1-project_f_brain-fate|D1]] · ✅ [[06 - Ops & Runtime/PROP-D2-wire-learning-to-acquisition|D2]] · ✅ [[06 - Ops & Runtime/PROP-D3-missing-tests-plan|D3]] · ✅ [[06 - Ops & Runtime/PROP-D4-identifier-rename-opsec|D4]]. اسکلتِ خالیِ 01/06/07 حالا محتوای واقعی دارد.
- **⛔ بلوک B (moves) + C (drafts reset):** آماده در MIGRATION-MAP «بلوک اجراییِ آماده»، ولی auto-mode اجازهٔ اجرای دسته‌ایِ `mv` را نداد → **معطلِ اجرای مالک یا اجازهٔ Bash.** هیچ انتقالی رخ نداد.

## ✅ انجام‌شده در جلسهٔ اکتساب/تحقیق/roadmap (2026-07-12، بعد از کارتوگرافی)

- **موتورِ اکتساب — کدِ propose-only، ساخته + تست‌شده، هیچ افکتورِ زنده:**
  - `brain/acquisition_pipeline.py` — draft→صف→approve→آمادهٔ پستِ **دستیِ انسان**. ساختاراً **هیچ متدِ post/send/dm/publish/pay ندارد**؛ `PF_LIVE_PUBLISH` فقط برچسب می‌زند (`auto_posted` همیشه False)؛ finalize fail-closed. (commit `c7124df`)
  - `studio/affirm.py` — لایهٔ گرم/تحسین‌گرِ استودیوی خالق (content-free، **بی‌هیچ برچسبِ شخصیت**، `/halt` همیشه حاضر). (commit `c7124df`)
  - سیم‌کشی: `langar/pf_admin.py` (دستورهای `/pf_status·plan·queue·ok·no·ready`) + هوکِ `/pf_*` در `langar_bot.py` + `affirm` در `saba_studio.home()`. (commit `ae31bfd`)
  - **تست ۲۲/۲۲ آفلاین** (pipeline + affirm + pf_admin). طراحی: [[03 - Projects/اونلی فنز/05 - Acquisition/AUTO-ACQUISITION-BLUEPRINT|AUTO-ACQUISITION-BLUEPRINT]] (commit `1d5b363`).
  - ⚠️ **دو بار ریویوِ خصمانهٔ ایجنتی** روی pipeline اجرا شد → گافِ گاردِ کپی (فقط caption گارد می‌شد، hook/tag رد می‌شدند؛ codename/platform در banlist نبود) پیدا و بسته شد. حالا containment روی **caption+hook+tag** + banlistِ هم‌تراز با `_ops/events.py` است.
- **تحقیقِ رقبا/بازار:** [[03 - Projects/اونلی فنز/02 - Research/COMPETITOR-MARKET-LANDSCAPE-2026-07-12|COMPETITOR-MARKET-LANDSCAPE]] — اولین نوتِ رقیب‌محور (۸ منبع؛ FeetFinder فروشِ سریعِ ۷–۱۴روزه، پولِ واقعی در PPV/custom، **retention گافِ اصلیِ ما**؛ منابع جهت‌نما نه حسابرسی‌شده). (commit `e7889b6`)
- **دستورالعملِ ۱۰-مرحله:** [[03 - Projects/اونلی فنز/00 - Control/ROADMAP-10-STAGES-2026-07-12|ROADMAP-10-STAGES]] — **نقشهٔ راهِ عملیاتیِ بعدی.** (commit `e7889b6`)

## ۰. ترتیب لود (قبل از هر کاری)

1. `_memory/onlyfans-project-memory-2026-07-05.md`
2. `PROJECT-F-CONTROL-MANIFEST.json` 🏆
3. `CLAUDE.md` (منشور — قواعد قفل‌شده §۱)
4. `PROJECT.md` (Active Context)
5. `00 - Control/CARTOGRAPHY-2026-07-12.md` ← **نقشهٔ فعلی؛ BASE-DATA-REPORT را تصحیح می‌کند**
6. `00 - Control/SOURCE-OF-TRUTH-MATRIX.md` · `RISK-LADDER.md` · `MIGRATION-MAP-2026-07-12.md`
7. `00 - Control/ROADMAP-10-STAGES-2026-07-12.md` ← 🧭 **بعدی چه کن (۱۰ مرحله با گیت/owner-agent split)**
8. `02 - Research/COMPETITOR-MARKET-LANDSCAPE-2026-07-12.md` ← **چرا این مسیر (رقبا/بازار)**

## ۱. حکم‌های قفل‌شدهٔ این جلسه (دوباره‌کاری نکن)

- ✅ **root = canonical؛ `docs/` + `research/` = آینهٔ stale** (تأیید مالک 2026-07-12؛ مبنا md5).
- ✅ **طرح پوشهٔ canonical = همان `00–09` موجود** (نه طرح ۰۰–۱۲ BASE-DATA-REPORT).
- ✅ dedup دقیق: ۱۳ byte-identical → `_Duplicates` · ۹ متفاوت (stale/encoding) → `09 - Archive`. لیست کامل در MIGRATION-MAP.
- ✅ قیود کد: پوشهٔ پروژه و `brain/langar/studio/orchestrator.py` **جابه‌جا نمی‌شوند** (وابستگی مسیر `_ops/neural`).
- ✅ بهداشت secret پاک است؛ kill-switchها در کد واقعی‌اند؛ `drafts.json` = ۲۴۴ ردیف تستی (reset پشت verdict).

## ۲. کارها به ترتیب — با گیت هرکدام

### بلوک A — بدون نیاز به verdict (🟢 همین الان شروع کن)

- [ ] **A1. سند `07 - Compliance & Privacy/OPSEC-ITEMS.md`** بساز: دو گاف ثبت‌شده — (۱) نام کوچک C در شناسه‌های سورس `studio/` (ماژول/کلاس/env-var) که OpsecGuard پوشش نمی‌دهد؛ (۲) `langar/langar_config.json` با `blocklist: []` (fail-open برای نام خانوادگی). **هیچ نامی echo نکن** — فقط توصیف مکان. راه‌حل پیشنهادی: rename شناسه‌ها به `creator_studio`/`CreatorStudio`/`TELEGRAM_CREATOR_*` به‌عنوان refactor گیت‌دار + پرکردن blocklist توسط A (نه ایجنت).
- [ ] **A2. `_INDEX.md` پوشه‌های 01–09** را با ارجاع به SOURCE-OF-TRUTH-MATRIX تازه کن (فقط لینک، نه انتقال).
- [ ] **A3. reconcile-note استراتژی** (`01`-scope ولی فعلاً root): جدول تعارض MASTER-BUILD ↔ Playbook (قیمت/برند/ساعت/Fansly) با تگ منبع دو طرف — **بدون انتخاب برنده** (تصمیم مالک).
- [ ] **A4. HOME.md**: بنر «Dataview نصب نیست — فقط نمای ایستا» + پیشنهاد نصب پلاگین به مالک (نصب پلاگین = تصمیم مالک).
- [ ] **A5.** `VERDICT_QUEUE.md` را sync نگه دار (سه ردیف جدید این جلسه اضافه شده: PF-STRUCT-V2، PF-STATE-RESET-V1، PF-CODE-REFACTOR-V1).

### بلوک B — پشت verdict ‏`PF-STRUCT-V2` (🟠 صبر کن تا مالک جواب دهد)

- [ ] **B1.** قبل از شروع: `agent-checkpoint:` commit.
- [ ] **B2.** فاز ۱ MIGRATION-MAP (retire آینه‌ها — ۲۲ فایل). بعدش هر دو validator + آپدیت `_گزارش تکراری‌ها.txt`.
- [ ] **B3.** فاز ۲ (کد مرده → Archive) — فقط اگر verdict ‏`yes-phases-1-2` یا بالاتر؛ قبلش grep نهایی importer.
- [ ] **B4.** فاز ۳ (filing اسناد به 00–09) — فقط با `yes-all-doc-phases`. بعد از هر batch: validatorها + fix لینک‌های INDEX/HOME.
- [ ] **B5.** پایان: آپدیت Active Context/Progress در PROJECT.md + commit فاز.

### بلوک C — پشت verdict ‏`PF-STATE-RESET-V1` (🟠)

- [ ] **C1.** `studio/drafts.json` → `[]` (نسخهٔ فعلی اول به `09 - Archive/state-2026-07/drafts-2026-07-12.json` منتقل شود — حذف ممنوع). `.bak` هم آرشیو.

### بلوک D — تصمیم‌های معماری (🟠/🔴 — فقط پیشنهاد بنویس، اجرا نکن)

- [ ] **D1. سرنوشت `project_f_brain.py`:** spec-canonical ولی runtime-dead. سه گزینه برای verdict: (a) سیم‌کشی به orchestrator (tiered HITL زنده شود)، (b) spec به DualBrainV3 بازنویسی شود، (c) آرشیو. پیشنهاد تحلیلی بنویس با diff/ریسک/rollback.
- [ ] **D2. سیم‌کشی `learning.py` به `acquisition.py`:** باگ greedy هنوز در مسیر زنده است. پیشنهاد patch propose-only + تست regression بنویس (اجرای تست پشت اجازهٔ sandbox).
- [ ] **D3. تست‌های غایب:** brain-core/orchestrator صفر تست دارند. طرح test-plan بنویس؛ اجرا پشت verdict.
- [ ] **D4. رجیستری `PF-CODE-REFACTOR-V1`:** rename شناسه‌های حاوی نام C (از A1) — refactor گیت‌دار با import-fix + تست.

### بلوک E — گیت‌های مالک (فقط یادآوری؛ ایجنت هیچ‌کدام را انجام نمی‌دهد)

GATE 0 (Branch A/B) · ۱۱ verdict معلق (THREAD-CLOSURE §۹) · PF-STRUCT-V2 · PF-STATE-RESET-V1 · انجماد body · فعال‌سازی لنگر.

## ۳. قواعد پایان جلسه (هر جلسه)

Active Context/Progress در `PROJECT.md` تازه شود · HANDOFF vault (01 - Dashboard) فقط wikilink · بیش از ~۵ فایل → commit ‏`agent-checkpoint:` · هر دو validator اجرا شوند · **بیرون پوشه فقط «Project-F»؛ صفر echo هویت/محتوا.**

## ۴. ضد-گاف (اشتباه‌هایی که نکن)

1. BASE-DATA-REPORT طرح پوشهٔ ۰۰–۱۲ پیشنهاد داده — **منسوخ است**؛ طرح canonical = `00–09` موجود.
2. `docs/` و `research/` را «محتوای جدید» فرض نکن — آینهٔ stale‌اند؛ همیشه نسخهٔ root را بخوان.
3. `studio/drafts.json` را صف واقعی نگیر — ۱۰۰٪ fixture تستی است.
4. ادعای «۲۹ تست سبز»ِ brain تاریخی است (2026-07-10، بازاجرا نشده). ولی **suiteِ اکتساب ۲۲/۲۲ در جلسهٔ 2026-07-12 واقعاً اجرا و سبز شد** (`brain/test_acquisition_pipeline.py` + `studio/test_affirm.py` + `langar/test_pf_admin.py`). تستِ brain-core را بدون اجازه اجرا نکن.
5. `orchestrator.py` را standalone اجرا نکن و مسیر پروژه را تغییر نده.
6. لینک‌های cross-vault (MYCELIAL-MASTER-SPEC، `_memory/*-BLUEPRINT`) تأییدنشده‌اند — قبل از استناد، وجودشان را چک کن.
7. **worktree/main-vault:** فایل‌های واقعیِ پروژه در main-vault `F:\backup\03 - Projects\...` روی `master`اند. کپیِ داخلِ `.claude/worktrees/*` ممکن است **قدیمی** باشد (Glob بدونِ path آنجا را می‌گردد و ساختارِ ۰۰–۰۹ را از دست می‌دهد). همیشه با مسیرِ مطلقِ main-vault کار کن + `git worktree list`.
8. **commit با pathspec:** این tree ~۷۶۰ فایلِ dirty از پروسهٔ همزمانِ `_ops` دارد. `git commit` بدونِ pathspec کلِ index را می‌گیرد (یک‌بار `_ops/budget/reconcile.py`ِ همسایه را جارو کرد). **همیشه `git commit -- <files>`.**
9. **قفلِ آنتی‌ویروس:** `git add` گاهی «Permission denied `.git/objects`» می‌دهد → retry با `sleep` per-file.
10. **گاردِ containment روی خروجی:** هر متنِ برون‌ده (caption/hook/tag) باید از banlist رد شود؛ ریویوِ خصمانه ثابت کرد گاردِ تک‌فیلدی کافی نیست. الگوی «AI draft، انسان send» و صفر echo هویت/شهر/قومیت مطلق است.
