---
type: project
kind: project
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
owner: آری
risk_level: high
autonomy_level: read-only
tags: [creator-business, faceless]
created: 2026-07-03
updated: 2026-07-29
aliases: ["Project-F", "پروژه اونلی فنز", "Active Context"]
---

# پروژه: اونلی فنز

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

**وضعیت:** creator brand با مدل faceless (فقط پا در فاز فعلی) — تیم دونفره ۵۰/۵۰، فاز validation. سند کامل: [[03 - Projects/اونلی فنز/project-master-reference|master-reference]].

**نقش در اکوسیستم:** درآمد آزمایشی؛ زیر نظارت architect (رئیس کل). کد ارجاع در خروجی‌های cross-domain: **«Project-F»**.

> 🆕 **HANDOFF پس از بازآرایی (۲۰۲۴-۰۷-۲۴):** ساختار مرتب شد + pf_os کامل شد. اول [[00 - Control/HANDOFF-NEXT-AGENT-2026-07-24-REORG|این سند]] را بخوان.

## 🎛 رابطِ کنترلِ ایجنتِ مادر (Architect) — cross-domain
- قراردادِ ماشین‌خوان: `PROJECT-F-CONTROL-MANIFEST.json` (صفر-PII، کدِ A/C) · روایت: [[03 - Projects/اونلی فنز/AGENT-CONTROL-INTERFACE|AGENT-CONTROL-INTERFACE]].
- مدلِ کنترلِ مادر: **رصد + صف‌بندیِ verdict + قطعِ اضطراری** — اجرای هیچ اکشنِ بیرونی، بدونِ دورزدنِ GATE 0/Hard-Gated، بدونِ تغییرِ قاعدهٔ قفل‌شده. مجریِ نهاییِ کارِ پرمخاطره = انسان (A).

## Agent interface (تا پیش از ARCHITECT_CHARTER — نسخه حداقلی)

- **خواندن مجاز:** PROJECT.md، master-reference، نوت‌های validation و لاگ آزمایش‌ها.
- **نوشتن مجاز:** فقط پیشنهاد (proposal)، گزارش و draft داخل همین پوشه؛ هیچ اکشن خارجی (پست، پیام، ساخت اکانت، پرداخت) بدون verdict انسانی.
- **ممنوع مطلق:** echo هویت پارتنر، عکس/محتوا، یا هر جزئیات شناسایی‌پذیر در تلگرام، داشبورد یا هر خروجی خارج از این پوشه — فقط کد «Project-F».
- **Security Gate:** تا وقتی ردیف‌های CRITICAL در [[ROTATION_CHECKLIST]] باز است، همه ایجنت‌ها روی این پروژه read-only هستند.

## KPIs (فاز validation)

delivery-rate پارتنر در trial sprint `[To measure]` · engagement روی teaserها `[To measure]` · نتیجه Track B (payment/banking پایدار: بله/خیر) — متریک درآمد از ابتدا به صبا گزارش شود (شرط تعهد او).

## Open blockers

> ⚠️ **خط زیر خالی = GATE 0 باز = هر اکشن بیرونی ممنوع.** «temporary-A» (07-16) فقط مجوز آماده‌سازی propose-only بود، نه بستن G0. ثبت رسمی فقط با امضای [[03 - Projects/اونلی فنز/DecisionLog#DL-2026-07-20-G0 — حقیقتِ GATE 0|DL-2026-07-20-G0]].

**GATE 0: محل اقامت پارتنر ثبت و شاخه A/B انتخاب شود** — «محل اقامت پارتنر: ___ · تاریخ: ___ · پیامد: Branch A/B» ([[03 - Projects/اونلی فنز/architecture-blueprint-2026-07-04|بلوپرینت §۱]])

بلاکرهای باز (به‌روز 2026-07-20 عصر، بعد از ballot — [[03 - Projects/اونلی فنز/00 - Control/SCAN-LOCK-2026-07-20|SCAN-LOCK]]):
- **PAGE_SETUP = NO-GO** ([[03 - Projects/اونلی فنز/00 - Control/GATE-STAMP-2026-07-20|GATE-STAMP]]) — تا بسته‌شدن P0های باز [[03 - Projects/اونلی فنز/00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/09_NOGO_PAGE_SETUP|NOGO]]
- ✅ PF-V5 = **REVOKED** (‏`APPROVED: REVOKE` — ‏DL-2026-07-20-PF-V5) · ✅ body-freeze **امضا شد** · ✅ Fansly قفل شد · ✅ remote=NO
- G0: ‏Branch A ‏**attested** (اظهار A) ولی باز — نوع منبع + تاریخ تأیید C خالی؛ سؤال آخر پرسشنامه حل‌نشده
- توافق: **A-SIGNED** — تأیید مکتوب C مانده (قبل از Day-Zero)
- PII در فایل‌های tracked (دو سند/۸ عکس `test/`) — انتقال R10 با رأی مالک؛ **الزامی قبل از هر remote آینده**
- Security Gate بسته (R11) · «Sydney» در کپی عمومی (R9) · ریسک #۱ (consistency زیر friction) تست‌نشده

## Active Context

- تمرکز فعلی: **حاکمیت + سخت‌سازی (Forced Completion Sprint ‏2026-07-20) تمام شد — PAGE_SETUP = NO-GO تا سه امضای A.** اجرای بیرونی همچنان صفر.
- **2026-07-29 (اسکنِ گروهِ تلگرام):** طبق حقیقتِ پایهٔ [[../../OCTOPUS-DOCTOR/50-اسکن‌ها/TG-GROUP-SCAN-PACKAGE-2026-07-29|TG-SCAN-PACKAGE]]، هر دو مسیرِ `pf_os` → تلگرام پشتِ فلگِ غایب خوابیده‌اند: `bridge.py` فقط به `saba-bridge.jsonl` می‌نویسد و مصرف‌کننده‌اش (`bridge_beat`) پشتِ `OCTOPUS_WIRE_SABA_BRIDGE` ست‌نشده است؛ `event_bus` هم از راهِ `event_bridge` می‌گذرد که `OCTOPUS_WIRE_EVENT_BRIDGE` آن هم غایب است (غیبت‌ها عمداً staged در `_ops/ARMING-ORDER-2026-07-29.md`). کنترلِ زندهٔ این پا از تلگرام فعلاً فقط از باتِ دوم (دستورهای لنگر `/pf_*`) و pause/resume مرکز است؛ در مرکز فقط دایجستِ content-free با نامِ «استودیو».
- **2026-07-20 — Forced Completion Sprint (برنچ `claude/project-f-governance-sprint-515cf3`):**
  - **حاکمیت:** ۷ ورودی DL-2026-07-20-* به [[03 - Projects/اونلی فنز/DecisionLog|DecisionLog]] (G0 باز/فیلدهای انسانی · PF-V5 ‏INVALID تا REVOKE|RATIFY · متن کامل توافق دونفره · body-FREEZE · تست صادق · پروندهٔ PII · قاعدهٔ SoT)؛ هر دو VERDICT_QUEUE محافظه‌کارانه reconcile؛ manifest ‏`last_governance_pass` گرفت؛ [[03 - Projects/اونلی فنز/00 - Control/OWNER-BALLOT-2026-07-20|برگهٔ رأی ۱۲سؤالی]] آماده.
  - **کد:** فیکس P0 بای‌پس compliance (‏orchestrator حالا از manifest ‏fail-closed می‌خواند + tick ‏blocked_compliance) · importهای `_ops/neural` ‏lazy با fallback (استقلال کامل) · فیکس fail-open ‏ChannelLocks روی JSON خراب · RLock+atomic روی acq/dm · dedup ‏md5 · ‏approvals.jsonl · ‏/pf_dryrun · LinkState+کد tracking روی /pf_ready · فیلدهای funnel ‏KPI + ‏/kpi_import · join استودیو↔اکتساب (DraftSubmission+handoff_to_vault) · **C1 rename کامل استودیو** (creator_studio/creator_brain/PF-Studio UA/envهای STUDIO_* با fallback قدیمی) · پاکسازی PII از selftest/فیکسچر/runbook.
  - **تست صادق: 209/209 سبز** (126+43+23+17؛ خط پایه 152) — [[03 - Projects/اونلی فنز/00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/08_TEST_REPORT|08_TEST_REPORT]]؛ ادعاهای 155/148/100 بازنشسته.
  - **اسناد:** [[03 - Projects/اونلی فنز/00 - Control/SCAN-LOCK-2026-07-20|SCAN-LOCK]] · [[03 - Projects/اونلی فنز/00 - Control/PF_OS_CANONICALITY|ADR pf_os (incubating)]] · بستهٔ ۱۰فایلی [[03 - Projects/اونلی فنز/00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/01_RUNTIME_MAP|ARCHITECTURE-COMPLETE]] · [[03 - Projects/اونلی فنز/00 - Control/GATE-STAMP-2026-07-20|GATE-STAMP: NO-GO]] · بنر SUPERSEDED روی SYNTH-05 (درخت زنده).
  - **کشف PII جدید:** ۸ عکس git-tracked در `test/` — کنار دو سند PII، منتظر رأی مالک (R10).
- **2026-07-17 — مسیر الف / Launch infra (جلسهٔ راستی‌آزمایی + تکمیل):** کارِ ایجنتِ قبلی روی UI Creator + VaultBank wiring را راستی‌آزمایی شد، تست‌ها اجرا شدند (۱۵۵/۱۵۵ سبز)، و کارهای ناتمام تکمیل/commit شدند:
  - **commit `f72a83e`** — UI مخصوص Creator سخت‌شد (shadow-mode واقعاً کار می‌کند، alias‌های متنی برای تستِ بدونِ تلگرام، HALT fail-closed، navigation cancel-safe، ارقام فارسی، opsec copy)؛ `pf_admin._default_pipe()` حالا `VaultBank()` را inject می‌کند؛ `langar_bot._global_stop()` به STOP-ORGANISM اختاپوس احترام می‌گذارد + رفعِ RESIL-4. تست‌های سبا ۱۰→۱۶، pf_admin ۷→۸.
  - **commit `0a871e0`** — **VaultBank با ۲۲ asset برند seed شد** (از P4-persona-hooks؛ همه از گاردِ containment + warm-up رد شدند؛ ۱۲ reddit SFW + ۷ x + ۳ of soft-cta). `/pf_plan` حالا از محتوای واقعی/certified draft می‌زند نه `_SAFE_HOOKS`. flow کامل راستی‌آزمایی شد: `/pf_plan 5` → `/pf_queue` → `/pf_ok` → `/pf_ready`، همگی از vault با fair rotation. **.gitignore سخت‌شد**: runtime state (drafts.json/acq_queue.json/state files/log) با wildcard‌های encoding-proof ignored شدند؛ دو فایل runtime که قبلاً tracked بودند (drafts.json/langar_log.jsonl) از tracking خارج شدند. `vault.json` عمداً commit شد (seedِ برند، صفر PII).
  - ⚠️ **نکتهٔ ابزاری:** git روی ویندوز با کاراکتر فارسی در pathspec مشکلِ byte-exact دارد؛ همیشه با `-c core.quotepath=false` و مسیرهای glob-resolve‌شده کار کن.
- **2026-07-12 — موتورِ اکتساب + تحقیقِ رقبا + ROADMAP:** اسکلتِ کدِ propose-only ساخته و تست شد (commitها `1d5b363`/`c7124df`/`ae31bfd`؛ ۲۲/۲۲ تست): `brain/acquisition_pipeline.py` (draft→صف→approve→آمادهٔ پستِ دستی، بدونِ افکتورِ بیرونی) + `studio/affirm.py` + سیم‌کشیِ `/pf_*` در لنگر + `affirm` در استودیوی صبا.
- **2026-07-12 — موتورِ اکتساب + تحقیقِ رقبا + ROADMAP:** اسکلتِ کدِ propose-only ساخته و تست شد (commitها `1d5b363`/`c7124df`/`ae31bfd`؛ ۲۲/۲۲ تست): `brain/acquisition_pipeline.py` (draft→صف→approve→آمادهٔ پستِ دستی، بدونِ افکتورِ بیرونی) + `studio/affirm.py` + سیم‌کشیِ `/pf_*` در لنگر + `affirm` در استودیوی صبا. **تحقیقِ رقبا/بازار** → [[03 - Projects/اونلی فنز/02 - Research/COMPETITOR-MARKET-LANDSCAPE-2026-07-12|COMPETITOR-MARKET-LANDSCAPE]] (dual-platform؛ FeetFinder = موتورِ فروشِ سریعِ ۷–۱۴روزه؛ پولِ واقعی در PPV/custom؛ **retention = گافِ اصلیِ ما**). **دستورالعملِ کاملِ ۱۰-مرحلهٔ بعدی** → [[03 - Projects/اونلی فنز/00 - Control/ROADMAP-10-STAGES-2026-07-12|ROADMAP-10-STAGES]]. همه پشتِ GATE 0.
- **2026-07-12 — Brand pack (propose-only):** لایهٔ هویتِ برند در [[03 - Projects/اونلی فنز/01 - Strategy/Identity/_INDEX|01-Strategy/Identity]] ساخته شد (IDENTITY، BRAND-CHARTER، VOICE-AND-STYLE، CLAIMS-REGISTER، BRAND-NAME-DECISION) با ورک‌فلوِ ۴-ایجنتهٔ کالیبراسیون. یافته‌ها: نامِ #۱ = **Anar Soles** / reserve Yalda Arch (تنها صفر-collision؛ منتظر verdict #۶، به #۹ گره‌خورده) · نام‌های شهری (Softly Sydney/Harbour Soles) حذف شدند (نقضِ #۶) · #۹ نامتقارن است (قاعدهٔ #۶ حاکم؛ سیگنالِ دیاسپورا فقط غیرمتنی) · صدا = warm/unhurried/wry · گافِ AI-image بسته شد (قفلِ human-only پیشنهادی) · نقصِ انطباقِ «Sydney light» در Playbook برای اصلاحِ گیت‌دار flag شد. هیچ انتشار/اکانت/کپیِ فارسی.
- **2026-07-12 — نقشه‌برداری (Cartography) + بستهٔ handoff:** نقشهٔ راستی‌آزمایی‌شده در [[03 - Projects/اونلی فنز/00 - Control/CARTOGRAPHY-2026-07-12|CARTOGRAPHY]] (dedup دقیق md5: ۱۳ identical + ۹ stale mirror؛ root = canonical تأیید شد؛ code deep-read: project_f_brain مرده در runtime، learning سیم‌نشده، drafts.json = ۲۴۴ ردیف تستی، secretها پاک، kill-switchها واقعی) · [[03 - Projects/اونلی فنز/00 - Control/SOURCE-OF-TRUTH-MATRIX|SoT-Matrix]] · [[03 - Projects/اونلی فنز/00 - Control/RISK-LADDER|RISK-LADDER]] · [[03 - Projects/اونلی فنز/00 - Control/MIGRATION-MAP-2026-07-12|MIGRATION-MAP]] (⛔ اجرا نشده — verdict ‏PF-STRUCT-V2) · برنامهٔ ایجنت بعدی: [[03 - Projects/اونلی فنز/00 - Control/HANDOFF-NEXT-AGENT|HANDOFF-NEXT-AGENT]] · ۳ verdict جدید در VERDICT_QUEUE (STRUCT-V2 / STATE-RESET-V1 / CODE-REFACTOR-V1)
- **2026-07-10 — Round 2 تحقیق جامع ۷-محوره integrate شد** → [[03 - Projects/اونلی فنز/RESEARCH-INTEGRATION-round2-2026-07-10|round2]]: تأیید سوم مسیر (dual-platform/Reddit-engine/AI-درفت-انسان-می‌فرستد) · ریسک جدید R4 (فوت Radvinsky + فروش سهم OF ‏>$3B) · AU زیر-۱۶ live · یافتهٔ free-page/price-lock → تقویت EXT-04 برای #۱۰ · کاتالوگ ۵۸-روشی جذب + unit-economics + spec تکمیلی مغز (~AUD 8–12/ماه) + سؤالات مشاور AU · سؤال‌های باز جدید #۱۷–#۲۰
- **2026-07-10 — M2/M3/M4 + PROMPT D + لنگر:** ماتریس تصمیم ‏[[03 - Projects/اونلی فنز/DECISION-MATRIX-M2-2026-07-10|M2]] · پلن ‏[[03 - Projects/اونلی فنز/COMPLIANT-PLAYBOOK-M3-2026-07-10|M3]] · بستن threadها ‏[[03 - Projects/اونلی فنز/THREAD-CLOSURE-D-2026-07-10|THREAD-CLOSURE-D]] (T1–T8) · ۵ درفت در `drafts-awaiting-gate/` · **کاکپیت تلگرامی «لنگر»** در `langar/` (propose-only، خودآگاه، مسئول ارتقا، ۸/۸ تست منطق سبز، فعال‌سازی گیت‌دار). ساعت صبا بسته (~۳h). ۱۱ verdict منتظر تصمیم آری (THREAD-CLOSURE §۹).
- تغییرات اخیر: 2026-07-03 — ثبت [[03 - Projects/اونلی فنز/پرسشنامه پارتنر - پاسخ‌های صبا|پاسخ‌های صبا]]؛ مرز محتوا قفل شد: فقط پا، بدون صورت/بدن + geo-block ایران · 2026-07-04 — کیت مغز پروژه ساخته شد · 2026-07-05 — [[03 - Projects/اونلی فنز/STATE-REPORT-2026-07-05|STATE-REPORT]] + verification pass (۸/۹ تناقض تأیید، ۱ اصلاح) + اعمال patch بلوپرینت §۱۱ · **2026-07-06 — Round 1 تحقیق بیرونی integrate شد → [[03 - Projects/اونلی فنز/RESEARCH-INTEGRATION-round1|RESEARCH-INTEGRATION-round1]]**: مسیر فعلی تأیید مستقل؛ REJECT تلگرام/کریپتو (قاعدهٔ #۳)؛ ToS ‏OF ممنوعیت AI-chat را [FACT] کرد → الگوی «درفت در کنسول جدا + paste دستی» ابقا؛ ۳ سؤال باز جدید (#۱۴ شفافیت DM، #۱۵ ‏C2PA، #۱۶ ‏B2B)؛ KPI کاندید: unlock-rate، $/script-start، چرخهٔ Custom، $/ساعت DM
- ۳ قدم بعدی: (۱) Track B/C — تحقیق desk درباره payment/banking و automation-fit، time-box یک هفته (۲) بازپرسیدن سؤال آخر پرسشنامه به زبان ساده‌تر (۳) طراحی Track A sprint با متریک صریح و گزارش‌دهی زودهنگام نتیجه مالی به صبا
- تصمیم‌های باز: ~~«مسیر safe expansion به body»~~ → **منجمد شد (پیش‌فرض) 2026-07-20** — DL-2026-07-20-BODY-FREEZE؛ فقط امضای A مانده. تصمیم‌های باز واقعی: REVOKE/RATIFY برای PF-V5 + فیلدهای G0 + امضای توافق ([[03 - Projects/اونلی فنز/00 - Control/OWNER-BALLOT-2026-07-20|OWNER-BALLOT]])

## Progress

- چه کار می‌کند: دوکاکپیت propose-only کامل و سخت‌شده (لنگر + استودیوی Creator با نام‌های neutral) · ۹/۹ safety net واقعی با اثبات ([[03 - Projects/اونلی فنز/00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/03_SAFETY_NETS|03_SAFETY_NETS]]) · compliance ‏tick از manifest ‏fail-closed · زنجیرهٔ کامل C→vault→pipeline→payload دستی با کد tracking · KPI+funnel قابل‌سنجش (‏/kpi_import) · audit ‏HITL ‏(approvals.jsonl) · **209/209 تست سبز با runner مستند** · حاکمیت روی DecisionLog قفل (NO-GO stamp)
- چه مانده: **۳ امضای انسانی A** (G0 · REVOKE|RATIFY · توافق) + پر کردن [[03 - Projects/اونلی فنز/00 - Control/OWNER-BALLOT-2026-07-20|ballot]] · backlog ‏R-* ([[03 - Projects/اونلی فنز/00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/07_BACKLOG_REMAINING|07_BACKLOG]]): scrub ‏Sydney از کپی عمومی (R9، پیش‌نیاز bio) · انتقال PII ‏tracked (R10، رأی مالک) · چک‌لیست OpSec ۲۴بندی (R11) · scrub مشترک (R3) · merge برنچ sprint با رأی Q10/Q11
- مشکلات شناخته: تعهد پارتنر مشروط به دیدن مسیر پول‌دهی · تاریخچهٔ git حاوی PII است تا مالک دربارهٔ remote جواب دهد (ballot ‏Q8) · pf_os فقط در درخت زندهٔ untracked (ریسک تک‌نسخه — R5) · `_global_stop` روی exception ‏fail-open (R2) · نوت‌های top-level ‏۱۳۵ خطای frontmatter ‏pre-existing (پاکسازی جدا)

## Next actions

- [ ] 🗺 **دستورالعملِ اجرا = [[03 - Projects/اونلی فنز/00 - Control/ROADMAP-10-STAGES-2026-07-12|ROADMAP ۱۰-مرحله]]** — مرحلهٔ ۱ (بستنِ GATE 0) کلِ زنجیره را باز می‌کند
- [ ] **۱۱ verdict منتظر تو** (THREAD-CLOSURE §۹): G0 · Playbook+M3-a · قاعدهٔ بالانس >$100 · سقف مغز AUD 15 · نردبان EXT-04 · برند Anar Soles · Fansly discovery-first · حالت labeling X · بلاک AU · فعال‌سازی لنگر · انجماد body
- [ ] **G0** — ثبت محل اقامت پارتنر + انتخاب Branch A/B (بلوپرینت §۱)
- [ ] ارسال پیام آماده به صبا (بازپرسیدن سؤال آخر + انتظارات — بلوپرینت §۴.۲) و ثبت جواب
- [ ] توافق مکتوب دونفره (بلوپرینت §۴.۱) — فقط بعد از Branch A
- [x] انجماد «expansion به body» — پیش‌فرض اعمال شد 2026-07-20 (DL-2026-07-20-BODY-FREEZE؛ ratify با امضای A) · hours واقعی از 07-10 بسته: ~۳h/هفته
- [ ] روز صفر زیرساخت (بلوپرینت §۵، ~۴–۵ ساعت) → شروع warm-up هفته ۱
- [x] Track B + C (desk research) — انجام شد 2026-07-04: GO conditional / GO limited
- [x] 2026-07-17: UI Creator hardening + VaultBank wiring + 22-asset seed (commits f72a83e/0a871e0) — ۱۵۵ تست سبز
- [ ] **مرحلهٔ ۵ (باقی‌مانده، بی‌نیاز به گیت):** `LearningBridge` را در `pf_admin._default_pipe()` پیش‌فرض کن (الان `AcquisitionBrain.with_bandit()` وجود دارد ولی به‌صورتِ اختیاری فعال نیست)؛ تستِ regression بنویس

## نوت‌های مرتبط

- [[03 - Projects/اونلی فنز/پرسشنامه پارتنر - پاسخ‌های صبا|پرسشنامه پارتنر — پاسخ‌های صبا]]
- [[03 - Projects/اونلی فنز/اونلی فنز|لاگ پیام‌های تلگرام — اونلی فنز]]
- [[03 - Projects/اونلی فنز/Knowledge_Base_Memory_Synthesis|Knowledge_Base_Memory_Synthesis]]
- [[03 - Projects/اونلی فنز/project-master-reference|project-master-reference]]

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]

## 🎛 کابین کنترل (two-brain)

- کابین مشترک: ارتیفکت `fleet-live-dashboard` · نقشه: [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT|TWO-BRAIN]] · نقشهٔ ساخت: [[_memory/FRANKENSTEIN-BUILD-PLAN|FRANKENSTEIN-BUILD-PLAN]]
- عملیات استاندارد از کابین (intent → sendPrompt): «تست <پروژه>» = validators + چک کد + تست قرارداد · «بساز» = اسکلت از `_Templates` + ثبت همین‌جا · «آرشیو» = فقط انتقال به `_Archive`/`_Duplicates` (هرگز حذف واقعی).
- تست قرارداد این پروژه: هنوز تعریف نشده — طبق BUILD-PLAN §۲ تعریف شود.