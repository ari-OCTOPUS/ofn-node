---
type: architecture-plan
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
created_by: agent
sources:
  - "Downloads/Telegram: CHRONOS-FABLE_OS_Unified_Master_Prompt_and_Data (2).md"
  - "Downloads/Telegram: OCTOPUS CHRONO ARCHITECTURE (2).md"
  - "Downloads/Telegram: OCTOPUS GAP AUDIT E15-E25.md"
  - "Downloads/Telegram: OCTOPUS INTEGRATION SPEC.md"
  - "Downloads/Telegram: OCTOPUS CHRONO INTEGRATION SPEC.md"
  - "Downloads/Telegram: octopus-atlas.tsx"
  - "recon workflow wthvcewz9 (7 read-only agents، HEAD=fb90fab، ۷۵۳k توکن)"
tags: [octopus, chrono, architecture, grounding, roadmap, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# 🐙 CHRONO GROUNDING + PLAN — نگاشتِ طراحی↔واقعیت، roadmap، گیت‌های تصمیم

> سنتزِ ۶ سندِ طراحیِ تلگرام روی کدِ واقعیِ repo (۱۰۲ فایلِ _ops، HEAD=fb90fab). حاصلِ یک شناساییِ موازیِ ۷-بُعدیِ فقط‌خواندنی. **هیچ کدی زده نشد.** اپیستمیک: 【E】مستند در کد · 【P】استنتاجِ موجه · 【S】گمانه.

---

## ۰. TL;DR — بازتعریفِ کار

**اسناد فرض می‌کنند greenfield/«Brushline»؛ واقعیت این است که هستهٔ Chrono از قبل ساخته و تست‌شده است.** کارِ واقعی = چند gap-fixِ مشخص + wiringِ قطعاتِ جامانده + بهداشتِ نام — **نه** بازسازی. خطرِ اصلی: اگر ایجنتِ کدنویس اسناد را لفظی بگیرد، ledger/جدولِ موازی و کدِ phantom می‌سازد (فاجعهٔ دوپارگیِ منبعِ حقیقت).

**اولویت‌بندیِ کار (خلاصه):** T0 باگ‌های واقعی (۲) → T1 wiringِ جامانده (۴، پشتِ flag) → T2 سخت‌سازیِ امنیت پیش از هر live (۶) → T3 بهداشتِ اسناد/نام (۴، بدونِ کد). هشت گیتِ تصمیم برای Ari باز است (§۵).

---

## ۱. نگاشتِ نام: سند ↔ واقعیت (اولین چیزی که کدنویس باید بداند)

| نامِ سند/ادعا | واقعیتِ repo | شدت |
|---|---|---|
| `OCTOPUS_V2_REDESIGN.md` | **غایب** (۰ تطبیق). بزرگ‌ترین شکافِ مرجع | — |
| `octopus-atlas.tsx` | **غایب** در repo (فقط Downloads) | — |
| TINV-1..**11** (V2) | فقط **TINV-1..7** وجود دارد و در `_ops/chrono.py` کدشده | high |
| E15–E25 / C1–C12 / R-x | **غایب** — فقط در اسنادِ تلگرام | — |
| «Brushline / 60_code / main.py / orchestrator.py / audit.py / database.py» | **پروژهٔ نقاشی** (`_code/Lead-نقاشی/.../brushline/`)، نه اختاپوس | high |
| کدِ اختاپوس | **کاملاً `_ops/`**: organism.py · chrono.py · unified_bus.py · wiring.py · doctor/ · budget/ · neural/ · legs/ · afferent/ | 【E】 |
| «langar_ledger» (جدولِ SQLite §8) | عمداً ساخته نشده؛ LANGAR = **همان genome ledger JSONL** (`07 - Knowledge/genome-system/ledger/ledger.py`) — «extend، not rival». تصمیمِ درست | 【E】 |
| INV-*/AP-* | namespaceِ جدا (CHRONOS-FABLE INV-01..17 / AP-01..14) | — |
| ۱۲ سندِ زنده | فقط `SYSTEM_MAP.md` (06) و `AGENT_REGISTRY.md` (05) واقعاً live؛ MASTER_ARCHITECTURE=Inbox-draft؛ KNOWLEDGE_GRAPH غایب | high |
| گیت‌های D1–D7 / B1–B4 | تحتِ این کدها ردگیری نمی‌شود؛ در repo `DECISIONS.md` D-01..D-29 و AGENT_QUESTIONS «open-decision #N» است (تصادمِ نامِ D) | med |

**پنج مفهومِ provisionalِ V2:** فقط **فرسایش/wear** کد دارد (`chrono.py`: `metabolic_age`/`WEAR_BASE`). چهارتای دیگر (effect-lease، sleep-leg، quarantine-reader، lineage-archive) صفر footprint.

---

## ۲. gap-register per subsystem (design ↔ reality)

قالب: ✅ کامل · 🟡 ناقص · ❌ غایب/گپ. severity فقط برای گپ‌ها.

### A. Chrono/heart — عمدتاً ✅ (بهترین بخش)
- ✅ Pacemaker (~60s، daemon thread)، HLC (tick/merge/max کاک‌روچ)، heartbeat loop ۷-مرحله‌ای، ۵ از ۶ جدولِ §8 + ۳ جدولِ اضافه (checkpoint/gated_effect/metabolic_age)، TINV-1/6/7 کامل، EffectorGate، phi-accrual.
- 🟡 **HIGH گپ:** رکوردهای LANGAR **هیچ فیلدِ HLC ندارند** — ترتیبِ کلیِ قلب از HLC جداست (اسناد §0.3/§10 می‌گویند هر رویداد HLC-stamped در LANGAR). [design mismatch واقعی]
- 🟡 TINV-3 در v0.4.6 به heart-driven بازتعریف شده (age با human **یا** heartbeat هر ۱۴۴۰ ضربان) — تصمیمِ عمدیِ مالک؛ **متنِ اصلیِ spec کهنه است** (نه باگ؛ نیازِ به‌روزرسانیِ سند).
- 【E】 **E19 واقعی:** broadcast `max(HLC)` هر ضربان ساعتِ پای کند را به max می‌کشد → زمانِ ذهنیِ متفاوت له می‌شود.
- 【E】 **E20 واقعی:** `anticipation_queue` فقط `due_beat` دارد؛ هیچ world-deadline (مثل «۹ صبح بفرست»).
- ❌ **E15 مصداق ندارد** (کد threaded است نه asyncio) — ولی shared-fate درون‌process واقعی است (pacemaker daemon-thread + doctor_beat + legs in-memory؛ یک crash هر سه را می‌کشد)، کاهش‌یافته با watchdogِ بیرونی (PS1).
- 🟡 TINV-5 نشتی: `_ops/neural/sprint.py:25` deadline را با `time.time()` می‌سنجد (خلافِ روح).

### B. Ledger/heart security — گپ‌های امنیتیِ واقعی
- ✅ append-only + SHA-256 hash-chain (روی کلِ بدنهٔ canonical — قوی‌تر از فرمولِ سند)، verify()، age_tick صعودی، fsync + قفلِ دولایه.
- ❌ **E16 HIGH (واقعی — شدیدترین حفره):** `is_human=1` صرفاً یک پارامترِ بولی است؛ هر مسیرِ کد می‌تواند `append(is_human=True)` بزند. کانالِ احرازشده (`approval_channel.py`: allowlist+token+hmac) «افکت» را گیت می‌کند نه «نوشتنِ ledger» را، و پیش‌فرض **NotWired** است.
- ❌ **E17 MED:** payload با hash تغییرناپذیر است ولی content-addressed نیست (inline، بدونِ CAS).
- ❌ **E21 HIGH:** durability = مانیتورِ germline_lag + بکاپِ نیمه‌دستیِ محلی (git+tar). off-site copy#3 خودکار **نیست**؛ شاهدِ بیرونیِ head-hash نیست؛ `germline-backup.ps1` untracked.
- 🟡 `ledger-fallback.jsonl` هنگام شکستِ append = سینکِ ثانویهٔ خارج از زنجیره (ریسکِ خفیفِ گم‌شدنِ رویداد).

### C. Legs/effect-gating — بزرگ‌ترین گپِ ساختاری
- ✅ Leg پایه + TaskPacket (verifyِ ساختاری: no-wildcard، spawn=0، secrets خالی، propose-only)؛ EffectorGate (TINV-7)؛ money_gate/capability_gate/organ_gate (fail-closed).
- ❌ **فقط ۱ پایِ واقعی** (LeadLeg) از ۶ ادعایی. «۶ پا» = برچسب‌های UIِ cockpit (سطوحِ کسب‌وکار)، نه role-leg.
- ❌ **HIGH: پاها حلقهٔ خودمختار ندارند** — `make_lead_leg()` ساخته و دور ریخته می‌شود (returnش ذخیره نمی‌شود)؛ در tick loop رانده نمی‌شوند. HLC در `ChronoBus.LegHandle` است، **به آبجکتِ Leg وصل نیست**.
- ❌ **E18 HIGH (واقعی):** `release_gated_effects` با یک human-append **همهٔ** pendingها را آزاد می‌کند (بدونِ بندِ اثرِ خاص)؛ `effect_id` تصادفی (بدونِ dedupِ محتوایی)؛ Effect Lease نیست؛ حالتِ outbox 'failed' نیست.
- 🟡 C7: TaskPacket ممنوعات+budget دارد ولی goal/escalation فرمالیزه نشده؛ فقط ۱ نقش نمونهٔ عینی.
- 🟡 C5: فقط cost-cap (نه step/token-cap، نه stop-condition فرمال)؛ verifier مستقل فقط برای Lead (reconcile).
- 🟡 TINV-2/R13: single-writer درون‌process سفت است ولی cross-process best-effort («روی timeout بدونِ قفل ادامه» → امکانِ fork زنجیره)؛ مسیرهای مستقیمِ قدیمیِ ledger.append deprecated-not-deleted.
- ✅ **money-lock سالم تأیید شد** (capability_gate پیش‌فرض بسته، money_gate AU$20 fail-closed، هیچ auto-spend).

### D. Neural/Doctor — عمدتاً ✅ (۲ قطعهٔ unwired)
- ✅ هر ۸ ماژولِ عصبی موجود **و wired** پشتِ `OCTOPUS_WIRE_NEURAL`. **protective-override (S-fix-3) واقعاً enforce می‌شود** (ایجنتِ مستقل تأیید کرد: ابتدای tick محاسبه، epoch/fitness/doctor را گیت می‌کند، غیرقابل‌سرکوب).
- ✅ Doctor: monitor→propose→sandbox→critic→submit→(human)merge + restart_from_known_good، پشتِ `OCTOPUS_WIRE_DOCTOR`. verifier-independence برقرار (C5/H-4 **آسیب‌پذیر نیست** — خوب).
- ❌ **HIGH: Doctor Evolution** (`evolution.py`: RFCArchive/measured_lift/tournament_rank) ساخته+تست‌شده ولی **هرگز از run_cycle صدا نمی‌شود** — additive-but-unwired.
- ❌ **MED: Box-of-Agents B3 bridge** (box→doctor.submit) هیچ مسیرِ runtime ندارد — capability-on-shelf.
- ⚠️ **B1 «neural≫null» گمراه‌کننده است:** «neural Dreamer» یک **stub** است (hardcoded good_fixes)؛ سبزبودنِ B1 = تستِ لوله‌کشی، نه مدلِ یادگیرندهٔ واقعی. [این چراییِ flakyِ `test_box_b134` است که قبلاً یافتم — تسکِ task_aed6ebad].

### E. Memory/context/taint
- ✅ مسیرِ afferent کامل: sensory_bus → school_bridge → AwarenessField (ȧ=−L·a+input) → insights (propose-only)، persist در `_ops/state/school-awareness.json`.
- ❌ **HIGH باگِ واقعی:** `wiring.canonical_consolidation` (خط ۲۸۲) متدِ ناموجودِ `school_bridge.mean_awareness()` را صدا می‌زند → AttributeError که با `except` بی‌صدا بلعیده می‌شود → **School هرگز به consolidation نمی‌رسد**. تست‌ها با SchoolBridgeِ واقعی این را نمی‌گیرند.
- ❌ **HIGH: `canonical_consolidation` در organism/live_loop سیم‌کشی نشده** — فقط تست‌ها صدایش می‌زنند. پس ادعای «یک مسیرِ حافظه» محقق نشده؛ یادگیری هنوز از ۲ مسیرِ جدا (school_bridge.learn_from + ConsolidationCycle) می‌گذرد.
- 🟡 verification-gate فقط در ConsolidationCycle؛ `school_bridge.learn_from` گیتِ CONFIRMED ندارد (از هر afferent=True یاد می‌گیرد).
- ❌ **E23/C6 (واقعی):** هیچ برچسبِ taint/provenance روی دادهٔ بیرونی‌تبار؛ وراثتِ taint نیست. **کاهش‌یافته ساختاری** (فقط لیبلِ انتزاعی وارد می‌شود، insightها propose-only) — پس گپ = نبودِ taint-label، نه مسیرِ اجرای خودکار.
- 🟡 seed_curriculum ۴۸ نود (نه ۲۰۰؛ deferred، verdictِ مالک).
- ✅ L6 cache≠truth رعایت شده.

### F. Safety/ops — عمدتاً ✅ در کد (نه کاغذی)
- ✅ kill-switch belt-and-suspenders (halted() + organism + EffectorGate.force_closed + watchdog همه STOP را چک می‌کنند)؛ money-stack واقعاً strictest-min fail-closed؛ همهٔ مسیرهای پول فعلاً بسته (postureِ درستِ paper).
- ❌ **MED:** `settings.json` فقط `permissions.deny` (۲۳ قاعده) دارد؛ **هیچ hooks ندارد** (منشور §10 ادعای «deny + hooks» می‌کند → نیمهٔ hooks غایب).
- ❌ **MED:** تاریخِ money-lock 2026-07-21 فقط برای debate/replication (live_gate_open) enforce است، **نه** در گیت‌های پولِ واقعی (capability_gate: «calendar ≠ capability»). ادعای ۴-جزئیِ money-lock دربارهٔ تاریخ نادقیق است.
- ❌ **MED:** «Project-F↛Fugu pass-2 privacy guard» **به‌عنوان کدِ نام‌دار وجود ندارد** — فقط PII blacklistِ عمومی. (`fugu` = نامِ یک مدلِ LLM، نه مقصدِ داده!). containmentِ Project-F فقط متنِ UIِ cockpit است نه منطقِ enforce‌شده.
- ✅ **E24/C9 آسیب‌پذیر نیست:** هر دو سرور 127.0.0.1، تلگرام owner-allowlist+quarantine+env-token.
- 🟡 R16 سیاستِ third-party skill: unenforced (فقط سیاست).

### G. Docs/naming — بهداشتِ بحرانی
- 🔴 **CRITICAL: «لنگر/LANGAR/Anchor» ≥۶ موجودِ متمایز را نام می‌دهد** (بات langar تریدینگ · Anchor Ledgerِ مفهومی · LANGAR arrow · genome ledger.py [واقعی] · Brushline LANGAR · langar_redteam هیپنوتیزم · لنگرزادِ داستانی). قانونِ هم‌نامی مستند است ولی فقط ۳ از ≥۶ را پوشش می‌دهد. **تصادمِ live و آشتی‌نشده.**
- 🟡 genome-system inner .git خالی → به‌جای submodule به‌صورتِ فایلِ ساده commit شد (open decision، AGENT_QUESTIONS ~line 110).

---

## ۳. roadmap (تیر‌بندی + وابستگی + walls)

**walls حاکم بر همهٔ تیرها:** additive-only · propose-only · fail-closed · human-gate برای پول/spawn · secret فقط env · Project-F containment · money قفل تا (capability∧LIVE_ENABLED∧approval) · بدونِ auto-merge · هر قدم path-scoped commit.

### T0 — باگ‌های واقعی (امن، بی‌نیاز به تصمیم، اول)
- **T0-1** فیکسِ `wiring.canonical_consolidation` → باگِ `mean_awareness()` (memory HIGH). + تست با SchoolBridgeِ **واقعی** (نه fake). [فایل: `_ops/wiring.py`]
- **T0-2** رفعِ گمراهیِ B1: یا `test_box_b134` را قطعی/معنادار کن، یا صراحتاً برچسب بزن «B1 = تستِ لوله‌کشی، نه capability» (چون Dreamer یک stub است). [تسکِ موجود task_aed6ebad]

### T1 — wiringِ جامانده (additive، پشتِ flag، بدونِ capability/پولِ نو)
- **T1-1** سیم‌کشیِ `canonical_consolidation` در حلقهٔ زنده پشتِ flag (M-unification واقعی). وابسته به T0-1.
- **T1-2** سیم‌کشیِ Doctor Evolution (RFCArchive/measured_lift/tournament) در `Doctor.run_cycle` پشتِ flag (propose-only حفظ). [نیازِ گیتِ D-E]
- **T1-3** سیم‌کشیِ Box B3 bridge پشتِ flag، یا تصمیمِ صریحِ «on-shelf بماند». [نیازِ گیتِ D-E]
- **T1-4** HLC per-leg: اتصالِ آبجکتِ Leg به ChronoBus.LegHandle + راندنِ legs از حلقهٔ خودمختار. [بزرگ‌تر؛ نیازِ گیتِ D-F]

### T2 — سخت‌سازیِ امنیت (طبقِ تقدمِ اسناد: پیش از هر ورودی/liveِ بیرونی)
- **T2-1 (E16/C1) قلبِ احرازشده** — `is_human=1` جز از کانالِ احرازشده نوشتنی نباشد (امضا/فرآیندِ جدا). **شدیدترین حفره؛ پیش از هر پولِ live الزامی.** [نیازِ گیتِ D-C]
- **T2-2 (E18) idempotencyِ اثر** — بندِ per-effect release + کلیدِ dedupِ محتوایی + Effect Lease + حالتِ 'failed'. پیش از هر اثرِ live.
- **T2-3 (E23/C6) taint** — برچسبِ origin/trust روی Observation→AfferentEvent→Insight + وراثت. (اولویتِ پایین‌تر چون propose-only فعلاً مهارش می‌کند.)
- **T2-4 (E21) durability** — off-site خودکار + شاهدِ بیرونیِ head-hash. (نیمه ops/runbook.)
- **T2-5** hooksِ `settings.json` (منشور §10 ادعای hooks دارد ولی نیست) — یا لایهٔ hook اضافه، یا ادعای منشور اصلاح.
- **T2-6** نشتیِ TINV-5 در `sprint.py` (wall-clock → beat-budget).

### T3 — بهداشت/اسناد (بدونِ کد، ولی برای جلوگیری از فاجعه بحرانی)
- **T3-1 (CRITICAL) هم‌نامیِ LANGAR** — هر ≥۶ referent را در قانونِ ALIAS ثبت کن؛ پیش از اینکه کدنویس چیزی با نامِ «langar» را لمس کند باید بداند کدام است. جلوگیری از R2.
- **T3-2** آشتیِ specِ کهنه — TINV-3 اصلی (human-only) در برابرِ کد (heart-driven v0.4.6): ORGANISM-SPEC آپدیت / CHRONO ARCH §7 «stale» علامت.
- **T3-3** اصلاحِ name-mapِ phantom اسناد (Brushline≠Octopus) تا ایجنت‌های آینده به `_ops/` اشاره کنند.
- **T3-4** لایهٔ مرجعِ «V2/E-codes/atlas» غایب است — تصمیم: در repo authored شود یا اسنادِ تلگرام به‌عنوان ثانویه دور ریخته شوند. [گیتِ D-H مرتبط]

---

## ۴. نقشهٔ اثر (چه گپی به کجای roadmapِ اسناد می‌خورد)
- «P-Chrono-1..7» اسناد → **عمدتاً DONE** (chrono.py). کارِ باقی‌مانده = HLC-on-ledger (A گپ) + world-deadline (E20/D-B).
- «C1 authenticated heart» → T2-1. «C2 external watchdog» → **DONE** (organism-watchdog.ps1). «C3 shadow+witness» → T2-4. «C4 دو صفِ زمان» → D-B/E20. «C5 budget packet» → C ناقص. «C6 taint» → T2-3. «C7 role contract» → C ناقص. «C9 exposure» → **DONE**.
- «H-2 memory ladder / پای خواب» → ConsolidationCycle هست ولی نه معماریِ Letta. «H-4 دکترِ لنگردار» → verifier-independence **DONE**؛ evolution wiring = T1-2.

---

## ۵. گیت‌های تصمیم — **بسته‌شده با پیش‌فرضِ توصیه‌شده** (قابلِ وتوی Ari؛ ثبت‌شده در AGENT_QUESTIONS)

> به‌دستورِ Ari («تموم پرامپت‌ها را انتخاب کن، هیچی جا نذار») هر گیت با پیش‌فرضِ توصیه‌شده بسته شد تا هیچ پرامپتی HOLD نماند. این‌ها defaultِ قابلِ‌وتو‌اند: تا وقتی Ari وتو نکرده، پرامپتِ متناظر آمادهٔ اجراست. مکانیزم‌های heart-touch (D-C) پیش از merge نیازِ germline-backup + review دارند.

| # | تصمیم | گزینه‌ها | ✅ تصمیمِ اتخاذشده |
|---|---|---|---|
| **D-A** (E19) | معناشناسیِ زمانِ ذهنی | broadcast max(HLC) بماند / HLC فقط علّی + نرخ در meter | **HLC فقط علّی + نرخ در meter** (P-A2) |
| **D-B** (E20/C4) | صفِ world-deadline کنارِ beat-deadline؟ | بله / خیر | **بله** (P-A3) |
| **D-C** (E16/C1) | مکانیزمِ قلبِ احرازشده | امضا+فرآیندِ جدا / فیزیکی / تلگرامِ wired | **امضا + wire کانالِ موجود** (P-H1) — بحرانی، pre-merge review |
| **D-D** (TINV-3) | فلشِ heart-driven (v0.4.6) | تثبیت + آپدیتِ spec / بازگشت | **تثبیت + آپدیتِ متن** (P-D2) |
| **D-E** | Doctor Evolution + Box B3 در حلقهٔ زنده؟ | wire / on-shelf | **wire پشتِ flagِ خاموش** (P-N1/N2) |
| **D-F** | ناوگانِ ۶-پا؟ | بساز / تک‌پا | **فعلاً تک‌پا + اتصالِ HLC به LeadLeg** (P-L1) |
| **D-G** | مفاهیمِ V2 | effect-lease الان / بقیه بعداً | **فقط effect-lease** (P-L2) |
| **D-H** | genome submodule یا plain؟ | submodule / plain | **plain + لایهٔ نامیِ V2 در repo** (P-D4/D5) |

---

## ۶. مدیریتِ تصادم با GLM (کارگرِ هم‌زمانِ master)
- GLM فعال روی `wiring.py`/`doctor.py`/`neural/`/`box/` commit می‌کند. پرامپت‌های T0-1/T1-1/T1-2 این فایل‌های hot را لمس می‌کنند → **path-scoped + چکِ HEAD قبل از edit + هماهنگی** (نه parallel-build روی همان فایل).
- T2 (امنیت) و T3 (اسناد) کم‌تصادم‌اند.
- self-report ≠ proof: هر ادعای «سبز» را با تستِ رفتاریِ مستقل تأیید کن (درسِ S-fix و flakyِ B1).

---

**نوتِ خواهر:** پرامپت‌های آماده‌ی build → [[octopus-build-prompts/CHRONO-BUILD-PROMPTS — grounded]].
