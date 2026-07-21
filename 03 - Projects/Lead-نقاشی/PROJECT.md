---
type: project
kind: area
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
owner: آری
risk_level: low
autonomy_level: read-only
tags: [lead-gen, painting, sydney, business, painting-os]
created: 2026-07-03
updated: 2026-07-20
---

# پروژه: Lead-نقاشی

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

درآمد اصلی — لیدگیری برای بیزنس نقاشی ساختمان در سیدنی با آزمایش‌های کنترل‌شده (یکی در هر زمان). معیار موفقیت: **لید واقعی، نه کلیک.** tenant #2 سیستم architect (D-26).

## Current state (شواهد)

- زیرساخت AiFarm: `AiFarm-Lead/` (نسخه canonical) شامل brushline (60_code) و `SERVER_ARCHITECTURE.md` `[Verified: وجود فایل‌ها]`
- ربات کاریابی: `کاریابی/bot/` — بازسازی کامل فازهای ۰-۴ (2026-07-03): امنیت (کلیدها فقط در .env + fail-fast)، حلقه تایید تلگرام (approve/reject/save/skip)، ۳ منبع فعال (PlanningAlerts + AusTender OCDS + NSW eTendering RSS) با زمان‌بندی per-source، `/draft` (فقط پیش‌نویس، ارسال دستی)، `/report` هفتگی، لاگ توکن، ۳۳ تست pytest → تا rotation خاموش `[Verified: tests green]`
- باگ‌های حیاتی رفع‌شده: job هارvest که با next_run_time=None برای همیشه pause بود؛ فریز event loop توسط Hunter؛ crash پیام‌های Markdown؛ حافظه Hunter که قدیمی‌ترین (نه جدیدترین) را می‌خواند؛ تجاوز از سقف ۱۰۰۰ درخواست/روز PlanningAlerts `[Fixed: 2026-07-03]`
- symlink خراب `کاریابی/bot/data/paint-data` → حذف شد `[Fixed: 2026-07-03]`
- pipeline ساختاریافته لید: تا امروز وجود نداشت → [[03 - Projects/Lead-نقاشی/Lead Pipeline & Experiments|Lead Pipeline & Experiments]] (امروز ساخته شد، خالی)
- آزمایش فعال: هیچ — آزمایش #۱ (SEGMENT-DISCOVERY طبق D5) پیش‌ثبت شد و منتظر شروع است

## Assets & resources

مهارت اجرا (نقاشی/renovation خود آری) · brushline (ایجنت لیدگیری، خاموش تا rotation) · بودجه از سقف کلی architect (D-25)

## Active workstreams

1. **🎨 Painting-OS — محصول اصلی بیزنس نقاشی (2026-07-12, P1-P3 ساخته شده):**
   - **P1 کوتیشن:** `pricing.py` + `lead_quote.py` — نرخ‌های واقعی سیدنی ($18-65/m²)، QuoteIntake 14 فیلدی، QT-YYYYMMDD-NNN
   - **P2 فاکتور:** `invoice.py` — ATO Tax Invoice، ABN، GST 10%، INV-FY{YY}-{NNN}، PAID از attribution CONFIRMED
   - **P3 ایمیل:** `email_inbound.py` — Gmail OAuth readonly، flag-gated (OCTOPUS_WIRE_EMAIL)، parse_lead_from_email
   - **reconcile v2:** گروه‌بندی CSV بر lead_id → پرداخت جزئی (deposit + balance)
   - **42 تست سبز** (pricing 10 + lead_quote 9 + lead_intake 6 + invoice 8 + email 9)
   - **محدودیت‌ها:** propose-only، $0 stdlib-only، صفر راز جدید، backward-compat
   - **نقشهٔ راه ۱۰ مرحله‌ای:** `کاریابی/08_Painting-OS_Roadmap_v2.md`
   - **تحقیق بازار:** ServiceM8 ($29-79)، Tradify ($70+/user)، AroFlo ($120+)، QuoteIQ ($150-700 USD)، hipages ($129+/ماه)

2. **🦵 پا (Worker):** `_ops/legs/lead_leg.py` — `LeadLeg(Leg)` حلقهٔ paper: `intake` → `draft_quote` → `claim` → `reconcile`. **propose-only:** فقط draft تولید؛ ارسال/پول human-gated. اولین دلارِ paper CONFIRMED شد.

3. آزمایش #۱: کشف segment — کدام بخش بیشترین ارزش per lead می‌دهد.

## KPIs

لید واقعی/هفته `[To measure]` · هزینه per lead per کانال `[To measure]` · نرخ تبدیل لید→quote→کار `[To measure]`

## Agent interface

- **می‌خواند:** این manifest، pipeline، لاگ آزمایش‌ها، `SERVER_ARCHITECTURE`.
- **می‌نویسد:** draft پیام/کمپین، به‌روزرسانی pipeline (پیشنهادی)، گزارش هفتگی آزمایش.
- **verdict انسانی:** ارسال هر پیام outreach به مشتری واقعی، هر خرج تبلیغ، تماس تلفنی.
- **قید قانونی:** هر outreach طبق [[03 - Projects/Lead-نقاشی/Outreach Compliance|Outreach Compliance]] (Spam Act 2003 + DNCR Act 2006).
- **Security Gate:** read-only تا بسته شدن CRITICALها.

## Open blockers

کلیدهای Anthropic/Telegram در چرخش · segment هدف = `[To measure]` تا پایان آزمایش #۱

## Active Context

- **2026-07-21 (شب، fork=دموِ dry-run) — قوسِ لید در sandboxِ worktree اجرا شد: ۹/۹ PASS، صفر ارسال.** یک لیدِ synthetic از `submit_candidate→firewall→فایل→scorer→receipt` عبور کرد و در **دو سدِّ مستقل** ایستاد: گیتِ per-effect (`synthetic_never_sends`) + transportِ `NOT_ARMED`. market_signal رد شد. دمو یک مسئلهٔ صداقتِ audit کشف و فیکس کرد (`settle_fresh` قبلاً `communication.sent` می‌زد بی‌آنکه چیزی برود → حالا `effect.settled`). گزارش: [[03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/DEMO-RUN-2026-07-21|DEMO-RUN]] + `replay.ps1` (۵ فرمان). فلگ‌های زنده همچنان خاموش، STOP سالم.
- **2026-07-21 (شب، «LEAD-SAFETY-C1») — footgunِ batch-release بسته شد + گیتِ per-effect (کامیت `5723f90`).** `chrono.release_gated_effects` دیگر همهٔ pendingها را با یک رأی آزاد نمی‌کند (allowlistِ پول؛ ارسالِ مشتری فقط `release_one` per-effect) · `lead_effect_gate` (authorize+may_release fail-closed+release_and_settle) · `outbound_worker` = stubِ NOT_ARMED (نمی‌فرستد). راستی‌آزماییِ متخاصم ۲ باگ گرفت و فیکس شد؛ تست 13/13، مسیرِ پول سبز. مانده: مسلح‌سازیِ transport (فاز D، owner-gated).
- **2026-07-21 (شب، «کامل مرتب و متصل کن») — بخشِ نقاشی/لید سیم‌کشیِ flag-off شد + handoff.** Trust-Engine از orphan به reachable رسید (کامیت `e3ffb7e`): گاردِ همگراییِ دو inbox (`lead_sense` فایل‌های LD-*/_* را skip می‌کند) · فیکسِ کرشِ نهفتهٔ `EffectorGate(db=None)` · launcherِ مرزِ HTTP پشتِ `OCTOPUS_WIRE_LEAD_BOUNDARY` · همگراییِ producer در owner_menu پشتِ `OCTOPUS_WIRE_LEAD_CANDIDATES` · freezeِ `lead_leg_inbox`. تست `test_lead_wiring` ۷/۷، صفر رگرسیون، همه flag-off/صفر ارسال. **مانده (کارِ ایجنتِ بعدی):** outbound workerِ واقعی + per-effect gate (safety، قبل از هر ارسال) + ۴ ماژولِ غایب. handoff کامل: [[03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/WIRING-HANDOFF-2026-07-21|WIRING-HANDOFF]].
- **2026-07-21 (فاز C پیاده شد — رأیِ تامِ مالک «FULL AUTHORITY + MANDATORY COMPLETION»):** لولهٔ ارزشِ P0 به‌صورتِ کدِ واقعیِ flag-off ساخته شد (همه در `_ops/legs/` و `_ops/heart/`، تست‌شده، صفر ارسالِ بیرونی، STOP دست‌نخورده): **consent_firewall** (fail-closed، 7/7)، **lead_candidate_inbox** (submit_candidate + برشِ synthetic E2E، 8/8)، **lead_boundary_http** (مرزِ HMAC روی 127.0.0.1:8774، 9/9 + smoke سوکت)، **effector_gate_bridge** (گاردِ stalenessِ releasable، 5/5)، **llm_intent** wired در `center._handle_ask` (4/4 reachability). دو ماژولِ heart (cognition_effect/fuel_meter) از HOLD خارج و ادغام شد (patchِ producers به‌صورتِ consumerِ واقعی پیاده شد، 8/8+7/7+7/7). رجیستری: بخشِ «TRUST ENGINE» در `_ops/OCTOPUS-COMPONENT-REGISTRY.md`. **فعال‌سازی owner-gated** (رأی روی قراردادها + secretهای ingestion + restart). فاز D (workerِ outbound واقعی) = رأیِ جدا.
- **2026-07-21 (فاز B ساخته شد — رأی صریح مالک «کامل و یکپارچه»):** بستهٔ طراحیِ **Octopus Trust Engine** وارد فاز B شد. خروجی در `Trust-Engine-v1.1/PHASE-B-CONTRACTS/` (۱۰ سند، master=`c4061e1`، germline×2): ۳ قراردادِ JSON (Lead/Event/Proposal — firewallِ رضایت ساختاراً در اسکیما قفل، پروب‌شده: market_signal هرگز outreach نمی‌سازد) + ماشین‌های حالتِ رضایت/قیف + مدلِ تهدید + مرزِ امضاشدهٔ `/api/v1/lead-candidates` + طرحِ مهاجرتِ دو inbox. با فن‌اوتِ چندایجنته + **راستی‌آزماییِ متخاصمِ مستقل**؛ ۲ یافتهٔ blocking اصلاحِ inline شد (ادعای غلطِ sweep_stale_effects روی `releasable`؛ سوراخِ consent در handoff → گیت بر candidate_type). سندِ حاکم: `PHASE-B-CONTRACTS/00_VERIFICATION_AND_FIXES.md`. **همه propose-only — فاز C (پیاده‌سازی) تا رأیِ مالک روی این قراردادها آغاز نمی‌شود.**
- **2026-07-21:** ماژولِ `_ops/telegram_center/llm_intent.py` (فهمِ free-text مالک → پیشنهادِ ساختاریافته) از stagedِ untracked به کانونی ادغام شد، **پشتِ فلگِ خاموشِ `OCTOPUS_TG_LLM_ASK`** (no-op مطلق)، propose-only، تست ۸/۸. دو ماژولِ heart (fuel_meter/cognition_effect) HOLD ماند (تستشان به patchِ غایبِ producers.py وابسته است).
- **2026-07-20:** به‌دستور مالک، اپ **TradeQuote Local** (Flutter/Drift — پیش‌فاکتور/فاکتور ATO-compliant با GST/ABN، PDF، اشتراک تلگرام/Gmail، بکاپ نسخه‌دار؛ MVP کامل ولی هنوز کامپایل‌نشده) وارد شد → `tradequote_local/` (بدون `.git` داخلی). نقش: ابزار کوتیشن/فاکتور دستِ مالک برای همین پا؛ الحاق به `lead_leg` فقط به‌صورت bridge پیشنهادیِ flag-off (بعد از پایان delta-scan نوشته می‌شود). گام حیاتی بعدی روی ماشین مالک: `tradequote_local/docs/BUILD_AND_RELEASE.md` §1 (create→pub get→build_runner→analyze→test→APK).
- **2026-07-06 (جلسه ۱۷):** کد پروژه به `_code/` منتقل شد (B1 پلن NONMD-TRIAGE؛ propose→executed با verdict آری). لاگ کامل: `00 - Inbox/nonmd-move-log-2026-07-06.csv`.

- تمرکز فعلی: rotation کلیدها → روشن کردن ربات → آزمایش #۱ (SEGMENT-DISCOVERY)
- تغییرات اخیر: 2026-07-03 — بازسازی کامل ربات (فازهای ۰-۴، ۳۳ تست سبز) + ۱۰ پرامپت تحقیقاتی در `کاریابی/06_پرامپت‌های_تحقیقاتی_گسترش_لیدگیری.md` · 2026-07-04 — [[03 - Projects/Lead-نقاشی/Report - Lead-نقاشی - Sydney Lead Channels 2026|Report - Sydney Lead Channels 2026]] از Inbox منتقل شد (Google LSA هنوز در AU نیست) · 2026-07-04 — کیت مغز پروژه (INDEX·DecisionLog·OpenQuestions طبق LIVING-BRAIN-BLUEPRINT) ساخته شد
- ۳ قدم بعدی: (۱) rotation ۵ کلید + `pytest tests/ -q` + `python test_run.py` (۲) اجرای main.py و بررسی push های تلگرام (۳) شروع آزمایش #۱ با دیتای واقعی ربات
- تصمیم‌های باز: کانال آزمایش #۱ (letterbox/آنلاین/ارجاع؟)

## Progress

- چه کار می‌کند: Painting-OS P1-P3 کامل (کوتیشن + فاکتور + ایمیل) · زیرساخت brushline · چارچوب آزمایش
- چه مانده: وایر `/lead` تلگرام · Gmail OAuth E2E · فرم وب‌سایت · PDF کوتیشن · فاکتور خودکار · داشبورد · SEO · **build اولین APK از `tradequote_local/` (R30) + پل lead_leg→TradeQuote (flag-off)** · **فاز C پیاده شد؛ مانده: رأیِ مالک روی قراردادها + secretهای ingestion + workerِ outboundِ واقعی (فاز D، رأیِ جدا) + جذبِ producerها (harvest/email → submit_candidate) + freezeِ lead_leg_inbox**
- مشکلات شناخته: ABN واقعی هنوز وارد نشده · Gmail token هنوز صادر نشده

## Next actions

- [ ] (مالک) build اول TradeQuote روی PC: `tradequote_local/docs/BUILD_AND_RELEASE.md` §1 → APK روی S23 FE
- [ ] (ایجنت، بعد از delta-scan) bridge پیشنهادی flag-off: draft کوتیشنِ `lead_quote.py` → قالب سازگار با TradeQuote (فقط فایل خروجی، صفر ارسال)
- [ ] وایر `/lead` تلگرام → `parse_lead_intake()` + `render_quote_html()` (مرحله ۱ roadmap)
- [ ] پر کردن ABN واقعی در `budgets.yaml` (مرحله ۲ roadmap)
- [ ] Gmail OAuth token → تست E2E ایمیل لید (مرحله ۳ roadmap)
- [ ] rotation کلیدها (مالک): Anthropic + Telegram + Tavily + PlanningAlerts + Serper
- [x] تعمیر symlink (2026-07-03)
- [x] Painting-OS P1-P3 ساخته و تست شده (2026-07-12)

## نوت‌های مرتبط

- [[03 - Projects/Lead-نقاشی/Lead Pipeline & Experiments|Lead Pipeline & Experiments]] · [[03 - Projects/Lead-نقاشی/Outreach Compliance|Outreach Compliance]]
- [[03 - Projects/Lead-نقاشی/Report - Lead-نقاشی - Sydney Lead Channels 2026|Report - Sydney Lead Channels 2026]]
- [[03 - Projects/Lead-نقاشی/knowledge-base|knowledge-base]] · [[03 - Projects/Lead-نقاشی/AiFarm-Lead/ARCHITECTURE_MASTER|AiFarm ARCHITECTURE_MASTER]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|لاگ پیام‌های تلگرام]]
- [[03 - Projects/Lead-نقاشی/کاریابی/07_Painting-OS_P1_Quotation_Design|P1 Quotation Design]]
- [[03 - Projects/Lead-نقاشی/کاریابی/08_Painting-OS_Roadmap_v2|10-Stage Roadmap v2]]
