---
type: mega-prompts
group: sub-projects
date: 2026-07-24
parent: OCTOPUS-PARALLEL-COMPLETION-PLAN-2026-07-24
note: "زیرپروژه‌های مستقل — جدا از هستهٔ ارگانیسم، هر زمان قابلِ اجرا. هر بخش standalone."
---

# 🧩 زیرپروژه‌ها — Project-F/Saba · Ziman/بات‌مامان · Painting-OS

> **قوانینِ مشترک:** منبعِ حقیقت = کد+git · safe-patch · TCB دست‌نخورده · worktreeِ ایزوله · `REAL_VAULT` پین · flag-off · `run_all` سبز. این‌ها **زیرپروژه‌های جدا** هستند؛ با هستهٔ ارگانیسم قاطی نکن مگر پشتِ گیتِ صریح.

---

## WS-7 — Project-F / Saba (کانونی‌سازی + تکمیل)  🔒 GATE-0

**نقش:** معمار + مالکِ محصول. **مأموریت:** کارِ پراکندهٔ Project-F را روی برنچِ کانونی تثبیت کن و بستهٔ BUILD-ALL را تکمیل/راست‌آزمایی کن. **Project-F پشتِ GATE-0 است (پروژهٔ بزرگسال/اونلی‌فنز) — ایزوله و owner-gated بماند.**

**منبعِ کانونی:** `claude/project-f-agent-build-aa512f` (BUILD-ALL: Fable5 ۴-DB + RAGِ محلی + KPI/attribution + productionِ CI/budget/backup/health؛ ۴۵۹ تست؛ ۵۳ فایلِ نو).
**منسوخ‌ها (کارشان در کانونی جمع شده):** `optimistic-maxwell` (stage-5/KPI)، `project-analysis-planning` (MASTER-SCHEDULE/BACKLOG-50)، `saba-vaultbank-tests` (Saba co-pilot).

**گام‌ها:**
1. worktree ایزوله از برنچِ کانونی. `python -m pytest` یا `run_all` مخصوصِ Project-F → تأیید ۴۵۹ سبز.
2. از ۳ منسوخ، فقط چیزهای **گم‌شده** را cherry-pick کن (اگر چیزی در کانونی نیست): مثلِ `MASTER-SCHEDULE-2026-07-14` و `BACKLOG-50` (اسنادِ برنامه‌ریزی).
3. تصمیمِ integration با ارگانیسم: `pf_bus`/`pf_state`/دوکلیدِ approve/`/pf_kpi`/`/saba_msg` — **همه پشتِ GATE-0 + flag**. shadow-mode را درست نگه‌دار.
4. **PII:** ۸ عکسِ PII به `09-Archive/_media-quarantine` منتقل شده — تأیید کن هیچ PII در tracked نیست؛ `.gitignore`ِ پروژه‌ای برای `pf_os_state/`.

**پذیرش:** ۴۵۹ تست سبز · GATE-0 دست‌نخورده (هیچ unlockِ خودکار) · صفر PII در git · state جدا از هسته.
**هزینه/vendor:** local-first (Ollama) + Fugu با دوگیت؛ کلیدها env-only. مدل از `model_router`.
**پس از این:** ۳ برنچِ منسوخ archive-tag + حذف.

---

## WS-8 — Ziman / گالریِ مامان (بات‌مامان + برندینگِ خودکار)

**مأموریت:** پایِ Ziman و بات‌مامان را کامل و flag-off وصل کن؛ قیدِ **۰ دلار** را حفظ کن.

**منبعِ کانونی:** `claude/ziman-gif-deep-scan-19ef9a` (برندینگِ خودکار + mom-bot ساخته‌وسخت‌شده، ۲۳ تست).
**فایل‌ها:** `_ops/legs/ziman_leg.py` + `_ops/wiring.py` (هوک) + `03 - Projects/Ziman Galerry/mom-bot/` (`bot.py`, `flow.py`, `questions.py`, `staging.py` + `tests/test_mom_flow.py`).
**منسوخ:** `higgsfield-integration-setup` (mom-bot Phase 0 — کارش در deep-scan جمع شده).

**گام‌ها:**
1. worktree ایزوله. دیف `ziman_leg.py` + `wiring.py` نسبت به master؛ additive/flag-off بیاور.
2. mom-bot را به‌عنوان زیرپروژهٔ `03 - Projects/Ziman Galerry/` نگه‌دار (جدا از `_ops` هسته). تست‌های mom-flow سبز.
3. قیدِ **`$0` = وابسته به `CORTEX_LOCAL_FIRST=1`** (Ollama رایگان؛ Fugu فقط gated-burst). این شرط را نشکن.
4. تست: `run_all` هسته سبز + `test_ziman_branding` + `test_mom_flow`.

**پذیرش:** flag-off صفر تغییر · mom-bot ایزوله · قیدِ $0 محفوظ (بدونِ `CORTEX_LOCAL_FIRST` هیچ فراخوانِ پولی) · فعال‌سازی owner-gated.
**پس از این:** `higgsfield-integration-setup` archive-tag + حذف.

---

## WS-9 — Painting-OS (کسب‌وکارِ نقاشیِ خودت)  💰 با احتیاطِ بالا

**نقش:** معمار + مالکِ محصولِ کسب‌وکار. **مأموریت:** «سیستم‌عاملِ نقاشی» را راست‌آزمایی و تکمیل کن — چهار ستون: **کار / کوت / اینویس / ایمیل**. این جریانِ درآمدِ واقعیِ توست؛ هر مسیرِ پول/مشتری پشتِ فلگ + تأییدِ مالک.

**منبع:** `claude/telegram-governance-integration-832984` (۱۲ commit: موتورِ quotation + invoice + email inbound + structured intake + درِ ورودیِ واحدِ تلگرام W6/W7).
**Add-on (verify-first):** `wave1/a-telegram` → Menu v2 + `_ops/outcomes/verdict_recorder.py` (durable OutcomeStore، رأیِ احرازهویت‌شدهٔ مالک). اگر در `telegram_center`ِ فعلی نیست، fold کن.

**گام‌ها:**
1. worktree ایزوله. **اول با `telegram_center`/legsِ فعلیِ master دیف بگیر** — کدام از ۴ ستون از قبل هست، کدام تازه.
2. ستون‌های تازه را additive/flag-off بیاور: `quotation engine` → `invoice engine + partial-payment reconcile` → `email inbound` → `structured intake`. UI از طریقِ درِ ورودیِ واحدِ تلگرام (رأیِ مالک: «UI از طریقِ اختاپوس»).
3. **مرزِ پول:** اینویس/پرداخت پشتِ فلگِ خاموش + دوکلید؛ هیچ ارسالِ خودکار به مشتری بدونِ arm. reconcileِ پرداخت = propose-only تا تأیید.
4. Menu v2 + OutcomeStore را (اگر تازه) وصل کن — رأیِ مالک durable شود.
5. تست: `run_all` سبز + تست‌های telegram/quote/invoice.

**پذیرش:** flag-off صفر تغییر · هیچ اینویس/ایمیلِ خودکار به مشتری بدونِ arm · reconcile propose-only · Menu v2 صادق (بدونِ green-lie). ⚠️ چون کسب‌وکارِ واقعی است: قبل از arm، مالک یک end-to-end با دادهٔ تستی ببیند.
**هزینه/vendor:** ایمیل IMAP App-Password (env-only)؛ enrichment محلی‌اول. بدونِ lock-in به یک provider.

---

*پایانِ زیرپروژه‌ها. ترتیبِ اجرا آزاد است (مستقل از هسته). Painting-OS بالاترین اولویتِ کسب‌وکاریِ توست.*
