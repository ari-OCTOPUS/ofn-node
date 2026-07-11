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

> **وضعیت لحظهٔ تحویل (2026-07-12):** نقشه‌برداری کامل و راستی‌آزمایی‌شده انجام شد؛ ۵ سند کنترل ساخته شد؛ **هیچ فایلی جابه‌جا نشده، هیچ کدی اجرا نشده.** GATE 0 هنوز باز؛ Security Gate بسته؛ پوسچر = contained propose-only.

## ۰. ترتیب لود (قبل از هر کاری)

1. `_memory/onlyfans-project-memory-2026-07-05.md`
2. `PROJECT-F-CONTROL-MANIFEST.json` 🏆
3. `CLAUDE.md` (منشور — قواعد قفل‌شده §۱)
4. `PROJECT.md` (Active Context)
5. `00 - Control/CARTOGRAPHY-2026-07-12.md` ← **نقشهٔ فعلی؛ BASE-DATA-REPORT را تصحیح می‌کند**
6. `00 - Control/SOURCE-OF-TRUTH-MATRIX.md` · `RISK-LADDER.md` · `MIGRATION-MAP-2026-07-12.md`

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
4. ادعای «۲۹ تست سبز» تاریخی است (2026-07-10) — بازاجرا نشده؛ بدون اجازهٔ sandbox اجرا نکن.
5. `orchestrator.py` را standalone اجرا نکن و مسیر پروژه را تغییر نده.
6. لینک‌های cross-vault (MYCELIAL-MASTER-SPEC، `_memory/*-BLUEPRINT`) تأییدنشده‌اند — قبل از استناد، وجودشان را چک کن.
