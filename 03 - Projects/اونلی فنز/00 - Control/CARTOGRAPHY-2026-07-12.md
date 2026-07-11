---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[BASE-DATA-REPORT-2026-07-12]]"
  - "[[BASE-DATA-REPORT-ADDENDUM-2026-07-12]]"
  - "[[00 - Control/OBSIDIAN-STRUCTURE-v1|OBSIDIAN-STRUCTURE-v1]]"
tags: [project-f, cartography, audit, os-foundation]
aliases: ["Project-F Cartography", "نقشه‌برداری Project-F"]
---

# 🗺️ CARTOGRAPHY — Project-F (2026-07-12)

> نقشه‌برداری عمیق و **راستی‌آزمایی‌شده** (md5 + grep + code deep-read). این سند BASE-DATA-REPORT همان روز را تصحیح و تکمیل می‌کند — جای آن را نمی‌گیرد، دقیق‌ترش می‌کند. Read-only بود: هیچ انتقال/اجرا/رسانه/secret.

## ۱. هویت (خلاصه)

- **چیست:** بیزنس creator دو نفره ۵۰/۵۰ (A=Operator, C=Creator)، برند faceless فقط‌پا، غیر explicit، فاز **validation**، اجرای بیرونی = **صفر** (عمدی).
- **بلاکر:** GATE 0 باز (محل اقامت C ثبت‌نشده → Branch A/B نامشخص) + ۱۱ verdict معلق + Security Gate.
- **پوسچر مؤثر:** contained propose-only. قرارداد طلایی: `PROJECT-F-CONTROL-MANIFEST.json`.

## ۲. یافته‌های راستی‌آزمایی‌شده (فراتر از BASE-DATA-REPORT)

### ۲.۱ Duplication — دقیق، با md5 (گزارش قبلی این تفکیک را نداشت)

**گروه A — ۱۳ فایل byte-identical** (dedup امن → `_Duplicates` طبق قانون §۹):
- root ↔ `docs/` (۴): `PROJECT-F-BRAIN-SPEC` · `PROJECT-F-FULL-REPORT-2026-07-09` · `TELEGRAM-CONTENT-STUDIO-v1` · `TELEGRAM-CONTENT-STUDIO-v2`
- root ↔ `research/` (۹): `ACQUISITION-ENGINE-2026-07-05` · `COMPLIANT-PLAYBOOK-M3-2026-07-10` · `DECISION-MATRIX-M2-2026-07-10` · `DECISIONLOG-ENTRIES-M4-2026-07-10` · `PROMPTS-2026-07-05` · `RESEARCH-INTEGRATION-round1` · `RESEARCH-INTEGRATION-round2-2026-07-10` · `STATE-REPORT-2026-07-05` · `THREAD-CLOSURE-D-2026-07-10`

**گروه B — ۹ فایل متفاوت** (⚠ dedup خودکار ممنوع — snapshot کهنه/encoding-variant؛ مقصد `09 - Archive`):
- root ↔ `docs/` (۷): `MASTER-BUILD` · `Feet-Content-Business-Master-Playbook` · `MONETIZATION-EXPANSION` · `architecture-blueprint` · `Fable5-Build-Spec` · `Content-Topics-Trends-2027` · `30-Faceless-Clips-ReadyToFilm` — نسخه‌های docs کهنه/mojibake؛ root تعمیر UTF-8 شده (INDEX هم «UTF-8 سالم» را تأیید می‌کند).
- root ↔ `research/` (۲): `research-prompts-lead-generation` · `research-track-BC-2026-07-04` — تعداد خط یکسان، همهٔ خطوط متفاوت → **فقط encoding/BOM/CRLF**، نه fork محتوایی.

**حکم canonical (تأیید مالک 2026-07-12): root = canonical؛ `docs/` و `research/` = آینه‌های stale.**

### ۲.۲ ساختار شماره‌دار = stub ناوبری
پوشه‌های `00–09` روی دیسک **خالی‌اند** (فقط `_INDEX.md`). ساختار «منطقی» با لینک وجود دارد، ساختار «فیزیکی» flat است. سه طرح ساختاری رقیب وجود داشت (stubهای دیسک / OBSIDIAN-STRUCTURE-v1 / طرح ۰۰–۱۲ در BASE-DATA-REPORT) → **این سند طرح `00–09` موجود را canonical اعلام می‌کند** (کمترین churn؛ لینک‌ها همین حالا به آن اشاره می‌کنند).

### ۲.۳ Code deep-read (ایجنت مستقل، ۳۸ tool-call)

- **Entrypoint واقعی فقط دوتاست:** `langar/langar_bot.py` و `studio/saba_studio.py` (هر دو `__main__` دارند). `orchestrator.py` بدون `__main__` است — حلقهٔ کتابخانه‌ای که از harness بیرونی (`_ops`) رانده می‌شود.
- **⚠ قید مهاجرت:** `orchestrator.py` با `sys.path` به `F:\backup\_ops\neural` وصل می‌شود و محاسبهٔ `_VAULT` آن عمق دقیق `…/03 - Projects/<project>/` را فرض می‌کند → **پوشهٔ پروژه و کد جابه‌جا نشود** (فقط refactor آگاهانه).
- **کد مرده/سیم‌نشده:** `brain/dual_brain.py` (جایگزین: `dual_brain_v3`) · `brain/project_f_brain.py` (**هیچ‌جا instantiate نمی‌شود** — قلب PROJECT-F-BRAIN-SPEC در runtime مرده است) · `studio/studio_telegram.py` و `_v3.py` (جایگزین: `saba_studio`) · `ab_tracker` / `kpi_dashboard` / `content_engine` / `lifecycle` (importer ندارند) · `learning.py` ساخته و تست‌شده ولی **به acquisition سیم نشده** — `acquisition.analyze()` هنوز greedy mean است (همان باگی که BRAIN-BENCHMARK ادعای رفعش را دارد).
- **State آلوده:** `studio/drafts.json` = ۲۴۴ ردیف، `drafts.json.bak` = ۶۰۸ ردیف — **۱۰۰٪ fixture تستی** (`t`/`draft`/`title`/`عنوان`). `brain/archive.json` = ۳ ردیف (۲ تست). در مقابل `brain/hebb_orch.json` دادهٔ اجرای واقعی دارد (last_seen ≈ 2026-07-11) → حلقهٔ orchestrator واقعاً اجرا شده.
- **بهداشت secret: پاک.** همهٔ token/chat-id فقط از env (بدون literal)؛ mask در `__repr__`؛ هیچ خواندن رسانه. Kill-switch/fail-closedها **در کد** پیاده‌اند نه فقط spec (KILL file، CostMeter fail-closed، OpsecGuard روی send، stranger-silence، outward-lock با regex روی PROJECT.md، HALT studio، protective-mode درد>۰.۷).
- **دو گاف opsec ثبت‌شدنی (بدون echo نام):** (۱) نام کوچک C در **خود شناسه‌های سورس** (نام ماژول/کلاس/env-var در `studio/`) هست و OpsecGuard فقط متن پیام را پاک می‌کند؛ (۲) `langar_config.json` با `blocklist: []` عرضه شده → نام خانوادگی/شناسه‌های دیگر redact نمی‌شوند (fail-open). خودِ UpgradeEngine این را کاندید #۱ ارتقا می‌داند.
- **تست‌ها:** langar=۹ (spec می‌گوید ۸)، studio=۱۰، learning=۱۱ (benchmark می‌گوید ۱۰) — پوشش فقط بات‌ها + bandit؛ هیچ تستی برای brain-core/orchestrator وجود ندارد.

### ۲.۴ سایر یافته‌ها
- **HOME.md «داشبورد زنده» موتور ندارد** — `.obsidian/plugins` در vault نیست → Dataview نصب نیست؛ فقط fallback ایستا رندر می‌شود.
- **فایل‌های غایبِ ارجاع‌شده:** `RISK-LADDER.md` (ارجاع RUNBOOK) — با همین جلسه ساخته شد. لینک‌های cross-vault (`MYCELIAL-MASTER-SPEC`، `_memory/*-BLUEPRINT`) تأییدنشده.
- **فایل خارجی/جابه‌جا:** `_inbox-other-projects/` (docx زیمان + نقشهٔ شخصی) · `test/*.jpg` (۸ عکس حساس → باید ذیل 08-PII برود) · `اونلی فنز.md` (لاگ تلگرام هم‌نام پوشه → rename به `TELEGRAM-LOG.md`).

## ۳. اسناد جدید این جلسه (همه در 00 - Control/)

- [[00 - Control/SOURCE-OF-TRUTH-MATRIX|SOURCE-OF-TRUTH-MATRIX]] — root canonical، آینه‌ها retire.
- [[00 - Control/RISK-LADDER|RISK-LADDER]] — نردبان GREEN/YELLOW/ORANGE/RED (فایل غایبِ RUNBOOK).
- [[00 - Control/MIGRATION-MAP-2026-07-12|MIGRATION-MAP-2026-07-12]] — نقشهٔ اجرایی staged (اجرا نشده).
- [[00 - Control/HANDOFF-NEXT-AGENT|HANDOFF-NEXT-AGENT]] — برنامهٔ گام‌به‌گام ایجنت بعدی.

## ۴. وضعیت OS-onboarding (چک‌لیست OLP-1)

✅ Manifest · ✅ Owner/Authority · ✅ Hard gates · ✅ Role boundaries · ✅ Telegram contract · ✅ Obsidian map (این سند) · ✅ اتصال sanitised
⚠️ Event schema (طراحی‌شده، instantiate‌نشده) · ⚠️ Memory policy (ضمنی) · ⚠️ Agent qualification (اجرا‌نشده) · ⚠️ Experiment schema (تصویب‌نشده) · ⚠️ Rollback کد (تست‌نشده)
**نتیجه: ~۱۱/۱۶ محکم — onboarding در حالت observe-only از همین امروز بلامانع است.**
