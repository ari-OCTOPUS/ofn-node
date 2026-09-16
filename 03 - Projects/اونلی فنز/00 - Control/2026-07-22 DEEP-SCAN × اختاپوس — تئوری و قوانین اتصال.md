---
type: deep-scan
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-22
created_by: agent (ZCode, grounded deep-scan)
tags: [project-f, octopus, deep-scan, theory, connection-rules, handoff]
aliases: ["دیپ‌اسکن Project-F × اختاپوس", "تئوری اتصال Project-F"]
purpose: "یک سند واحدِ کامل برای ایجنت بعدی: دیپ‌اسکنِ واقعیِ Project-F + استعارهٔ ارگانیسم + قوانینِ دقیقِ اتصال به اختاپوس و متصل‌ماندن."
sources_note: "همه‌چیز از خواندنِ کد/فایل/state واقعی برداشت شده. هر ادعا مسیر منبع دارد. هیچ‌چیز حدسی نیست."
---

# 🐙 DEEP SCAN — Project-F (اونلی فنز) × اختاپوس
### تئوری، استعاره و قوانینِ اتصال — برای فردا

> **برای ایجنتِ فردا.** این سند یک‌جا: (۱) Project-F چیست و کجاست؛ (۲) استعارهٔ ارگانیسمِ اختاپوس چطور کار می‌کند؛ (۳) Project-F چطور به اختاپوس وصل است و چطور **متصل بماند**. همه‌چیز از کد و فایل واقعی خوانده شده، نه حدس.
>
> **قاعدهٔ containment همیشگی (قفل‌شده #۷):** بیرون از پوشهٔ Project-F فقط «Project-F». صفر echo هویت/شهر/قومیت/محتوا. در این گزارش creator = **C**، operator = **A**.

---

## فهرست
۱. [خلاصهٔ یک‌صفحه‌ای](#۱-خلاصهٔ-یک-صفحه‌ای)
۲. [Project-F چیست — حقایقِ ثابت از فایل‌ها](#۲-project-f-چیست--حقایق-ثابت-از-فایل‌ها)
۳. [ساختارِ واقعیِ پروژه (Inventory)](#۳-ساختار-واقعی-پروژه-inventory)
۴. [کد واقعی: brain / studio / langar / orchestrator](#۴-کد-واقعی-brain--studio--langar--orchestrator)
۵. [استعارهٔ اختاپوس — فرهنگنامهٔ کامل](#۵-استعارهٔ-اختاپوس--فرهنگنامهٔ-کامل)
۶. [مدلِ اندامی: قلب، مغز، متابولیسم، پاها](#۶-مدل-اندامی-قلب-مغز-متابولیسم-پاها)
۷. [اتصالِ واقعیِ Project-F ↔ اختاپوس](#۷-اتصال-واقعی-project-f--اختاپوس)
۸. [قوانینِ متصل‌ماندن (Connection Discipline)](#۸-قوانین-متصلا-ماندن-connection-discipline)
۹. [واقعیتِ اجرا همین امروز (Reality Check)](#۹-واقعیت-اجرا-همین-امروز-reality-check)
۱۰. [نردبانِ ریسک و گیت‌ها](#۱۰-نردبان-ریسک-و-گیت‌ها)
۱۱. [نقشهٔ راه ۱۰ مرحله‌ای](#۱۱-نقشه-راه-۱۰-مرحله‌ای)
۱۲. [خطرات و تله‌ها](#۱۲-خطرات-و-تله‌ها)
۱۳. [ترتیبِ لود (Load Order)](#۱۳-ترتیب-لود-load-order)
۱۴. [فهرستِ کاملِ فایل‌های کلیدی](#۱۴-فهرست-کامل-فایل‌های-کلیدی)

---

## ۱. خلاصهٔ یک‌صفحه‌ای

| محور | وضعیت (از فایل/state واقعی) |
|---|---|
| **Project-F چیست؟** | کسب‌وکار faceless محتوای **فقط‌پا** (غیر-explicit) با مدل OnlyFans/Fansly، اجرا از استرالیا، تیم دونفره ۵۰/۵۰: **A** (ops/tech) + **C** (تولید محتوا). فاز = validation. |
| **اتصال به اختاپوس** | Project-F یک **پا (leg)** از ارگانیسمِ اختاپوس است. پلِ واقعی = `_ops/legs/langar_bridge.py`. در `_octopus/config/projects.yaml` ثبت‌شده (`project_f: active, money_locked, deadline 2026-07-20`). |
| **کد ساخته‌شده** | همه propose-only و تست‌شده: ۱۴۸ تست سبز (۱۲ فایل). pipeline + studio + cockpit + brain + ۳ safety net + Layer-2 (Fan CRM, Vault, KPI, Octopus bridge, FAQ). |
| **اجرای بیرونی** | **صفر.** هیچ اکانت، پست، شوت، درآمد واقعی. |
| **بلاکر ریشه‌ای** | **GATE 0** (محل اقامت C) — به‌صورت temporary-A فرضی حل‌شده (۲۰۲۶-۰۷-۱۶) ولی کامل ثبت/قفل نیست. |
| **ارگانیسم اختاپوس** | زنده ولی **کهنه**: `ORGANISM-STATE.json` = ۴۹–۶۲ ساعت پیش. coherence = ۰.۱۸۴ (پایین). ۹ عضو stale. wiring = ۲۵ پل، همه True. |
| **استعاره** | اختاپوس = ارگانیسم چندلایه (قلب/مغز/خون/پا/چشم). Project-F = یک بازو/پا. لنگر = کاکپیتِ اپراتور. استودیو = ساحتمغزِ خالق. |
| **یک‌خطی** | پروژه‌ای ۱۰۰٪ برنامه‌ریزی‌شده، ۰٪ اجرا — حالا باید یا لانچ کنی، یا پلِ اختاپوس را سالم نگه داری. |

---

## ۲. Project-F چیست — حقایقِ ثابت از فایل‌ها

> منبع: `PROJECT-F-CONTROL-MANIFEST.json` ( ماشین‌خوان، منبعِ حقیقتِ کنترلی) + `DEEP-SCAN-2026-07-17` + `CLAUDE.md` (منشور).

**هشت قاعدهٔ قفل‌شده (immutable — تغییر فقط با verdict انسانی):**
1. فقط پا — بدون صورت/بدن/explicit.
2. geo-block کامل ایران در همهٔ لایه‌ها + بدون هدف‌گیری کاربر داخل ایران.
3. پرداخت فقط داخل‌پلتفرم — هرگز P2P/crypto/PayPal با خریدار.
4. بدون نقض ToS هیچ پلتفرمی.
5. privacy دوطرفه (creator + buyer).
6. بدون geo-fact شهری در کپی عمومی (فقط «Aussie»); سیگنال فرهنگی فارسی فقط بصری.
7. بیرون پوشه فقط «Project-F»; صفر echo هویت.
8. ۱۸+ با consent ثبت‌شده; مرزِ C (ردِ بدن) بر همهٔ پلن‌ها حاکم.

**گیت‌ها (مترقی):**
- **G0** (بلاکر): محل اقامت C + توافق دونفره + Branch A/B. وضعیت: temporary-A فرضی.
- **G1**: ≥۲۰۰ کلیک + ≥۱۰٪ click→follow + delivery-rate ≥۸۰٪.
- **G2**: ≥۳۰ free-subs + ≥۵٪ free→paid + اولین AUD ۱۰۰.
- **G3**: ≥AUD ۲k/ماه ×۳ماه + churn <۳۰٪ → ABN + مشاور.
- **G4**: ۱۲ ماه سودآور + ابزار داخلی + کانال توزیع اثبات‌شده.

**مدل خودمختاری:**
- خودمختار (GREEN): کارِ برگشت‌پذیرِ درون‌پوشه (تحقیق، درفت، تست، KPI loop، پیشنهاد).
- hard-gated (RED، فقط انسان): ساخت اکانت، publish، DM، پرداخت، login، echo هویت، تغییر قاعدهٔ قفل‌شده.

---

## ۳. ساختارِ واقعیِ پروژه (Inventory)

> منبع: `find` واقعی روی مسیر. پروژه در **main-vault** روی شاخهٔ `master` زندگی می‌کند:
> `F:\backup\03 - Projects\اونلی فنز\` (مسیر مطلق).
> ⚠️ **کپی‌های `.claude/worktrees/*` ممکن است stale باشند** — همیشه با مسیر مطلقِ main-vault کار کن.

### ۳.۱ پوشه‌بندیِ canonical (۰۰–۰۹)
```
اونلی فنز/
├── 00 - Control/        ← اسناد حاکمیتی: ROADMAP, RISK-LADDER, SOURCE-OF-TRUTH, HANDOFF, DEEP-SCAN
├── 01 - Strategy/        ← Identity (BRAND-CHARTER, VOICE, CLAIMS), STRATEGY-RECONCILE
├── 02 - Research/        ← COMPETITOR-MARKET-LANDSCAPE و تحقیقات
├── 03 - Experiments/
├── 04 - Content Studio/
├── 05 - Acquisition/     ← AUTO-ACQUISITION-BLUEPRINT
├── 06 - Ops & Runtime/   ← KPI, PROP-D1..D4, WEEKLY-BRIEF
├── 07 - Compliance & Privacy/  ← OPSEC-ITEMS
├── 08 - Partner (PII)/   ← صفر-echo بیرون
├── 09 - Archive/
├── brain/                ← مغزِ پروژه (Python)
├── studio/               ← رابطِ خالق C (Python + تلگرام)
├── langar/               ← کاکپیتِ اپراتور A (Python + تلگرام)
├── tests/                ← ۱۴۸ تست
├── orchestrator.py       ← (DEAD at runtime — به _ops/neural وابسته)
├── PROJECT.md            ← Active Context + Progress
├── CLAUDE.md             ← منشور (قواعد قفل‌شده §۱)
├── PROJECT-F-CONTROL-MANIFEST.json  🏆 ماشین‌خوان
└── DecisionLog.md
```

### ۳.۲ توضیحِ نقشِ هر پوشه
- **`00 - Control`** = مغزِ حاکمیت. اول بخوان.
- **`brain/`** = موتورِ هوش (acquisition, learning, dm_pipeline, guards, dual_brain_v3).
- **`studio/`** = رابطِ خالق C: ثبت درفت، تقویم، PPV، ظرفیت، `/halt` (kill-switch مرز).
- **`langar/`** = کاکپیتِ اپراتور A: ~۴۶ دستور، OpsecGuard، CostMeter، SelfModel.
- **`orchestrator.py`** = ⚠️ **DEAD at runtime** (وابسته به `_ops/neural` که در scope پروژه نیست). اجرای standalone = کرش.

---

## ۴. کد واقعی: brain / studio / langar / orchestrator

> منبع: `DEEP-SCAN-2026-07-17` §۴ + خواندن مستقیم فایل‌ها. هر فایل با وضعیتِ واقعی.

### ۴.۱ مغز (`brain/`)
| فایل | خط | وضعیت | نقش |
|---|---|---|---|
| `dual_brain_v3.py` | ۴۱۸ | ✅ **فعال** | ۱۰ ThinkingBrain + ۷ CommBrain. در orchestrator/langar/studio به‌کاررفته. |
| `acquisition.py` | ۳۲۱ | ✅ فعال | هوشِ اکتساب؛ `with_bandit()` اختیاری. |
| `acquisition_pipeline.py` | ۲۹۳ | ✅ فعال | صف propose-only: draft→approve→finalize. `_SAFE_HOOKS` = ۵ هوکِ نمونه. |
| `learning.py` | ۲۹۶ | ✅ فعال | ThompsonBandit + UCB1 — **باگِ greedy رفع شد**. |
| `dm_pipeline.py` | ۲۰۴ | ✅ فعال | صف DM HITL — **هیچ متد send/transmit ندارد**. |
| `guards.py` | ۲۸۷ | ✅ فعال | WarmupGuard + ChannelLocks (fail-closed). |
| `store.py` | ۴۷۰ | ✅ فعال | DataSpine: FanDB + VaultBank + KPIRollup + OctopusState. |
| `faq_engine.py` | ۱۳۸ | ✅ فعال | auto-draft برای DM ورودی (HITL). |
| `ab_tracker.py` | ۹۷ | ⚠️ orphan | A/B test — ساخته‌شده، هیچ callerی. |
| `content_engine.py` | ۹۹ | ⚠️ orphan | ایده‌پردازی — seed دترمینیستیک. |
| `lifecycle.py` | ۹۲ | ⚠️ orphan | churn prediction — هیچ callerی. |
| `kpi_dashboard.py` | ۷۶ | ⚠️ orphan | HTML renderer. |
| `project_f_brain.py` | ۲۴۸ | 🔴 dead | superseded توسط v3. |
| `dual_brain.py` | ۳۱۸ | 🔴 dead | superseded. |

### ۴.۲ کاکپیت/استودیو (`langar/` + `studio/`)
| فایل | خط | وضعیت | نقش |
|---|---|---|---|
| `langar/langar_bot.py` | ۹۱۶ | ✅ فعال | کاکپیتِ A. ~۴۶ دستور. OpsecGuard fail-closed، CostMeter، SelfModel. |
| `langar/{pf,dm,fan,vault}_admin.py` | ~۱۰۰ | ✅ فعال | dispatcherهای `/pf_* /dm_* /fan_* /vault_*`. |
| `studio/saba_studio.py` | ۵۰۳ | ✅ فعال | رابط C با inline-keyboard + cert-gate. |
| `studio/content_studio.py` | ۲۲۵ | ✅ فعال | موتورِ مدیریت درفت. |
| `studio/affirm.py` | ۶۷ | ✅ فعال | لایهٔ تحسینِ content-free. |
| `studio/studio_telegram.py` + `_v3.py` | ۲۳۹/۱۹۵ | 🔴 dead | superseded. |

### ۴.۳ DataSpine (Layer 2 — مرکز دادهٔ یکپارچه)
`brain/store.py`: `FanDB` + `VaultBank` + `KPIRollup` + `OctopusState`. State در `langar/{fan_db,vault,kpi,octopus}.json`. **صفر PII** (fan_id = sha1(alias)[:12]).

### ۴.۴ تست‌ها
**۱۴۸ تست سبز** در ۱۲ فایل: `tests/` + `*/test_*.py`. پوشش: store (۲۴)، layer2-integration (۲۴)، dm-hitl (۱۴)، langar-failclosed (۱۰)، warmup-guard (۱۱)، warning-kill (۱۳)، acquisition-pipeline (۱۲)، learning (۱۱)، langar (۹)، pf_admin (۷)، saba_studio (۱۰)، affirm (۳).
**بدون تست مستقیم:** `dual_brain_v3.py` (مغزِ فعال!)، `dm_pipeline.py` (تست غیرمستقیم).

---

## ۵. استعارهٔ اختاپوس — فرهنگنامهٔ کامل

> منبع: `OCTOPUS/ARCHITECTURE-BIBLE.md` §2 (metaphor dictionary) + `شناخت اختاپوس/02-OCTOPUS-KNOWLEDGE-SNAPSHOT.md`. این فرهنگنامه استعاره → معنای مهندسی → پیاده‌سازیِ واقعی است.

اختاپوس یک سیستم **چندلایه** است، نه یک پوشهٔ واحد. لایه‌ها:

| لایه | مسیر | نقش |
|---|---|---|
| **بدنِ اجرایی/حاکم** | `_ops/` | organism, cortex, heart, budget, legs, doctor, state |
| **هستهٔ v2** | `octopus_core/` | event bus, actuator, telemetry, health |
| **کنترل‌پلینِ مالی/گیت** | `app/` | NBB Control Plane, invariants, budget, ledger (DORMANT) |
| **مغزِ پژوهشی** | `4d_system/` | SOG / Brain-OS (DORMANT/independent) |
| **ویژوال‌سازی** | `OCTOPUS/` | HTML worlds، architecture bible |
| **سیستمِ عصبیِ داده** | `nervous-system/` | extractors، JS globals، live-data |
| **ابزارِ نقشه‌برداری** | `نقشه اختاپوس/` | vault scanner |
| **پاها (legs)** | `03 - Projects/` | ۶ پای درآمدی + Project-F |

### فرهنگنامهٔ استعاره → مهندسی
| استعاره | معنای مهندسی | پیاده‌سازیِ واقعی |
|---|---|---|
| **Organism (ارگانیسم)** | runtime چندزیرواحدیِ حاکم | `_ops/organism.py` (port 8771) |
| **Heart / pulse (قلب)** | زمان‌بند/پیس‌میکر | `_ops/heart/control_law.py`، `innervation.heart_period_now` |
| **Blue blood (خونِ آبی)** | جریانِ پیام/داده (hemocyanin آبی) | event bus (`octopus_core/event_bus.py`) |
| **Brain / cortex (مغز)** | تصمیم + مسیریابی + یکپارچه‌سازی | `_ops/cortex/cortex.py` (port 8772) |
| **Arm / leg (بازو/پا)** | دامنهٔ اجرایی (یک tenant/پروژه) | هر پروژهٔ `03 - Projects/` یک پاست. **Project-F = یک پا** |
| **Tentacle (شاخک)** | پایپ‌لاینِ وظیفه | mode-cycle pipeline در brain |
| **DNA / genome (ژنوم)** | قراردادِ استراتژیِ تغییرناپذیر + لنگرها | `strategy.json` + ledgerِ hash-chain |
| **Mutation / evolution** | تکاملِ استراتژی پشتِ test-gate | `self_evolve`، `self_code` |
| **Immune / healing (ایمنی/شفا)** | خودترمیمی: rollback + backup | `housekeeping.py`، `backup.py` |
| **Reflex (رفلکس)** | چکِ invariant → haltِ فوری | `guardrails.check_invariants` |
| **Owner Gate** | choke-pointِ verdict انسانی | approval state machine |
| **Risk tier** | سطحِ ریسکِ حاکمیتی | `risk_tier ∈ {low, medium, high}` |
| **Shadow (سایه)** | دیدپذیریِ وضعیتِ پنهان | SOG `E_shadow` |

> **نکتهٔ کلیدی (صداقت):** استعارهٔ اختاپوس تزئینی نیست ولی **ناقص است**. observability/truth-cards زنده‌اند، ولی **actuation فلج است** (هیچ motor cortex واقعی). `octopus_core` ساخته‌شده ولی نیمه‌سیم‌شده.

---

## ۶. مدلِ اندامی: قلب، مغز، متابولیسم، پاها

> منبع: `شناخت اختاپوس/02` §2 (مدل اندامی) + `ARCHITECTURE-BIBLE.md`.

```
                Owner / GOALS / Verdict / Kill
                         ↓
                _ops/organism.py (port 8771)
                         ↓
    ┌────────────────────┼────────────────────┐
    ↓                    ↓                    ↓
 [cortex]            [heart]              [budget]
 تصمیم/synthesis      ضربان/work pump      متابولیسم/پول/گیت/fitness
 (port 8772)         (pacemaker)          (approval channel)
    ↓                    ↓                    ↓
 [doctor]            [state]              [legs]
 خودبهبود/RFC        حافظه/event/chrono    پاهای اجرایی
 sandbox/critic      queue/telemetry       (Project-F اینجاست)
    ↓
 app / octopus_core / 4d_system / nervous-system / OCTOPUS
```

### Project-F کجای این ارگانیسم است؟
Project-F = **یک پا (leg)**. پاها در `_ops/legs/` قرار دارند. پلِ Project-F = `_ops/legs/langar_bridge.py` (بخش ۷).

**نقشِ هر جزءِ Project-F در استعاره:**
- `langar/langar_bot.py` = **کاکپیتِ اپراتور** (رابطِ A با پا — فرمان‌ها اینجا وارد می‌شوند).
- `studio/saba_studio.py` = **ساحتمغزِ خالق** (رابطِ C — تولیدِ محتوای certify‌شده).
- `brain/` = **مغزِ پا** (هوشِ اکتساب، یادگیری، صفِ درفت).
- `brain/store.py` = **حافظهٔ پا** (DataSpine — Fan/Vault/KPI/Octopus state).
- `guards.py` = **سیستمِ ایمنیِ پا** (WarmupGuard، fail-closed).
- `studio/HALT` + `langar/KILL` = **رفلکس‌های پا** (kill-switch‌ها).

---

## ۷. اتصالِ واقعیِ Project-F ↔ اختاپوس

> منبع: خواندنِ واقعیِ `_ops/legs/langar_bridge.py` + `_octopus/config/projects.yaml` + `ARCHITECTURE-SOT.md` + `_ops/live_loop.py`.

این **مهم‌ترین بخش** برای متصل‌ماندن است. اتصال از **سه کانال** تشکیل می‌شود:

### ۷.۱ کانال ۱ — ثبت در رجیستری (Registration)
Project-F در `_octopus/config/projects.yaml` ثبت شده:
```yaml
projects:
  project_f:
    title: "Project-F"
    active: true
    money_locked: true          # درآمد هنوز قفل (GATE 0)
    deadline: "2026-07-20"
    control_only: true          # فقط کنترل، نه اجرای بیرونی
  studio:
    title: "استودیو 🎬"
    active: true
    money_locked: true
    deadline: "2026-07-20"
```
**قانون:** تا `money_locked: true` است، پا در حالتِ کنترل‌فقط زندگی می‌کند.

### ۷.۲ کانال ۲ — پلِ فرمان (langar_bridge)
فایلِ `_ops/legs/langar_bridge.py` پلِ واقعی است. **این پل لا‌مزاحم است (قانونِ بزرگِ پروژه):**

> `langar_bot.py` **لمس نمی‌شود**. این ماژول فقط `LangarBot` را instantiate می‌کند و متدِ موجودِ `.handle(chat_id, text)` را صدا می‌زند — دوباره‌نویسی نمی‌کند. OpsecGuardِ langar (scrub روی هر خروجی، fail-closed) همچنان فعال است.

**نحوهٔ کار:**
- دستورهای langar (`/pf_*`, `/saba`, `/drafts`, `/dm_*`, `/fan_*`, `/vault_*`, `/guards`, `/kpi*`, `/octopus*`, `/brief`, `/think`, `/upgrade`, `/gates`, `/verdicts`, `/rules`, `/kill`, `/revive`...) از **رباتِ واحدِ اختاپوس** پاسخ می‌گیرند — بدونِ توکنِ جدا.
- مسیرِ langar از env `OCTOPUS_LANGAR_DIR` یا fallbackِ کانونیکال (`F:\backup\03 - Projects\اونلی فنز\langar`) پیدا می‌شود.
- شکستِ هر import → `None` (fail-soft)؛ رباتِ واحد برای بقیهٔ دستورها کار می‌کند.

### ۷.۳ کانال ۳ — پلِ برگشتی به ledger (Genome Ledger)
برای کارهایی که **فعلیتِ واقعی** دارند (`/pf_ok`, `/pf_no`, `/pf_ready`, `/kpi_record`, `/clear_full_stop`, `/set_karma`, `/kill`, `/revive`) یک `NOTE` در ledger ژنوم (LANGAR) زده می‌شود:
- **content-free** (صرفاً `kind=verdict/result/ts`، بدونِ هویت/محتوا).
- **قرنطینهٔ مطلق:** هرگز محتوای Project-F در ledger نمی‌رود. این الگوی `unified_bus.publish` است.

### ۷.۴ کانال ۴ — UnifiedBus / live_loop
`_ops/live_loop.py` پاسِ نهاییِ wiring است: مغزِ Project-F ↔ کاکپیتِ A روی یک `UnifiedBus`. این live state را در `langar/octopus.json` و `_ops/state/saba-bridge.jsonl` (scaffold، آینده) نگه می‌دارد.

### ۷.۵ خلاصهٔ جریانِ دادهٔ کامل
```
مالک (تلگرام)
    ↓ دستور
رباتِ واحد اختاپوس (_ops/budget/approval_channel.py)
    ↓ allowlist چک
_ops/legs/langar_bridge.py  ← (پلِ لا‌مزاحم)
    ↓ .handle(chat_id, text)
Project-F/langar/langar_bot.py  ← (کاکپیت A)
    ↓ OpsecGuard scrub (هر خروجی)
    ↓ پردازش
brain/ + studio/ + store.py
    ↓ برای کارهای واقعی: NOTE → ledger ژنوم (content-free)
07 - Knowledge/genome-system/ledger/ledger.jsonl
```

---

## ۸. قوانینِ متصل‌ماندن (Connection Discipline)

> این قوانین از `_PROJECT_INSTRUCTIONS.md` + `ARCHITECTURE-SOT.md` + `langar_bridge.py` + `DEEP-SCAN` استخراج شده‌اند. **برای متصل‌ماندنِ Project-F به اختاپوس، این‌ها را رعایت کن.**

### ۸.۱ قوانینِ لا‌مزاحمی (Non-Interference) — ناقض‌ناپذیر
1. **`langar_bot.py` را هرگز بازنویسی نکن.** پل از `.handle()` موجود استفاده می‌کند.
2. **OpsecGuardِ langar پابرجاست** (scrub روی هر خروجی، fail-closed). قواعدِ قفل‌شدهٔ ۵/۷ (privacy دوطرفه) هرگز نقض نشود.
3. **هیچ محتوای Project-F در ledger ژنوم نمی‌رود.** فقط NOTE‌های content-free (`kind=verdict/result/ts`).
4. **توکن/owner از همان env رباتِ واحد** تغذیه می‌شود (`TELEGRAM_BOT_TOKEN` / `TELEGRAM_OWNER_CHAT_ID`) — نه توکنِ جدا.

### ۸.۲ قوانینِ ثبت و رجیستری
5. **هر فایلِ canonical جدید** باید در `ARCHITECTURE-SOT.md` ثبت شود.
6. **تغییر در وضعیتِ ثبت** (active/money_locked/deadline) باید در `_octopus/config/projects.yaml` به‌روز شود.
7. **هر دایرکتوریِ dormant** باید `DEPRECATED.md` داشته باشد که به canonical اشاره کند.

### ۸.۳ قوانینِ نبضِ ارگانیسم (Heartbeat)
8. **ارگانیسم برای زنده‌ماندن نیاز به نبض دارد.** `_memory/HEARTBEAT.md` logِ نبض است. سکوت > ۲× دورهٔ انتظار = ردیف regress.
9. **State snapshot** باید تازه بماند: `_ops/state/ORGANISM-STATE.json`، `_ops/state/events.jsonl` (append-only)، `_ops/state/cortex/cortex-state.json`.
10. ⚠️ **الان ارگانیسم کهنه است** (ORGANISM-STATE = ۴۹–۶۲ ساعت پیش). برای متصل‌ماندن، ارگانیسم باید دوباره START شود (بخش ۹).

### ۸.۴ قوانینِ commit و git
11. **commit فقط با pathspec صریح** — هرگز `git add -A`. این tree ~۳۰۵ فایل dirty از `_ops` دارد.
12. **commit با pathspec:** `git commit -- <files>` نه `git commit` خالی.
13. **آنتی‌ویروس:** `git add` گاهی Permission denied `.git/objects` می‌دهد → retry با `sleep`.
14. **همیشه با مسیر مطلقِ main-vault کار کن** نه worktree‌های stale.

### ۸.۵ قوانینِ صداقت و حاکمیت
15. **propose-only by default.** هر اکشنِ برگشت‌ناپذیر = verdict انسانی.
16. **verdict منفی = موفقیت.** اگر چیزی non-executable است، صریحاً بگو؛ نتایج را متورم نکن.
17. **هرگز حذف؛ فقط انتقال** به `_Archive`/`_Duplicates`.
18. **هرگز به `.git`، `_code`، یا فایل‌های حاوی secret دست نزن.** مسیرهای ممنوع: `.agentignore`.

---

## ۹. واقعیتِ اجرا همین امروز (Reality Check)

> منبع: خواندنِ مستقیمِ state واقعی در `_ops/state/`. این **وضعیت زنده** است، نه مستند.

### ۹.۱ ارگانیسم — کهنه ولی سالم
- `ORGANISM-STATE.json`: آخرین `ts` = **۲۰۲۶-۰۷-۱۹** (۳ روز پیش). `stop_organism: true`. month = AU$0.00. beat = ۹۶۳۱.
- **نتیجه:** ارگانیسم STOP کرده و دوباره START نشده. برای متصل‌ماندن، باید START شود.
- **برای START:** `_ops/organism.py` (port 8771). wiring = ۲۵ پل، همه True (`wire_doctor, wire_telegram, wire_unified, wire_lead, wire_neural, wire_school, wire_consolidation, wire_live_loop, wire_evolution, wire_box, wire_leg_tick, ...`).

### ۹.۲ cortex — coherence پایین
- `cortex-state.json`: cycle 53، **coherence = ۰.۱۸۴** (پایین). ۹ عضو stale (organism, heart, producers, work_pump, doctor_setpoint, governor, sigma, fitness, reconcile). همه awareness ≈ ۰.۰.
- **نتیجه:** مغز می‌چرخد ولی اعضا کهنه‌اند. نمونه: `organism` age_s=225758 (۶۲h) با SLA=1800s.

### ۹.۳ self-model
- `self-model.json`: ۲۵۲ ماژول، ۵۹۷۴۹ خط کد، **۲۶۱ تست**، **۷۴ wire-flag**. شامل `langar_bridge_dispatch` و `live_loop` (Project-F wiring).

### ۹.۴ نبض (HEARTBEAT)
- `_memory/HEARTBEAT.md`: آخرین beat‌های real = **۲۰۲۶-۰۷-۱۵ تا ۰۷-۱۷**. سپس silence. آخرین ورودی: `2026-07-21T16:25:03 · live-cockpit=START port=8773 · cortex=START port=8772`.
- **events.jsonl** آخرین = **۲۰۲۶-۰۷-۲۲T00:36:20** (part-loops + business-brain چرخیدند). پس مغز هنوز می‌چرخد، ولی ارگانیسم نیست.

### ۹.۵ ledger ژنوم
- آخرین NOTE‌ها = **۲۰۲۶-۰۷-۲۱**: `EFFECT_SETTLED`، `EFFECT_REQUEST` (PAY/LEAD_OUTBOUND — demo)، `SELF_IMPROVE_DIGEST` (n=34، maturity ۷۵.۶٪). top issues: «ORGANISM-STATE کهنه»، «Lead-نقاشی: هنوز درآمدِ تأییدشده‌ای ثبت نشده».

### ۹.۶ جمع‌بندی reality check
| جزء | زنده؟ | تازه؟ | اقدام لازم |
|---|---|---|---|
| organism.py (8771) | ❌ STOP | ۳ روز پیش | START دوباره |
| cortex.py (8772) | ✅ | ۲۰۲۶-۰۷-۲۱ | coherence پایین — members کهنه |
| live-cockpit (8773) | ✅ | ۲۰۲۶-۰۷-۲۱ | OK |
| langar_bridge | سیم‌شده ✅ | — | وابسته به START organism |
| Project-F ثبت | ✅ | — | money_locked=true (GATE 0) |

---

## ۱۰. نردبانِ ریسک و گیت‌ها

> منبع: `00 - Control/RISK-LADDER.md` + `PROJECT-F-CONTROL-MANIFEST.json`.

| سطح | معنا | مثال |
|---|---|---|
| 🟢 **GREEN** | خودمختار (برگشت‌پذیر، درون‌پوشه) | read، classify، analyse، research، draft، offline test، propose |
| 🟡 **YELLOW** | propose + log (مالک مرور می‌کند) | پیشنهاد سند governance، prompt candidate، schema candidate |
| 🟠 **ORANGE** | verdict انسانی لازم | جابه‌جایی فایل (PF-STRUCT)، reset state، آماده‌سازی فعال‌سازی تلگرام |
| 🔴 **RED** | فقط انسان (تا GATE 0 + Security Gate قفل) | ساخت اکانت، publish، DM، پرداخت، login، echo هویت، تغییر قاعدهٔ قفل‌شده، **اجرای کد** |

### Kill-switch‌ها (پیاده‌شده در کد)
- `langar/KILL` (`/kill`) → کاکپیت تمام دستورها را جز `/status,/revive` رد می‌کند.
- `studio/HALT` (`/halt`، مرز C حاکم) → استودیو halt؛ اپراتور مطلع می‌شود.
- **CostMeter fail-closed** (سقف AUD ۱۵/ماه LLM).
- **platform-warning** → توقف اتوماسیون + ثبت DecisionLog.

### قاعدهٔ تشدید
تضاد با قاعدهٔ قفل‌شده → اجرا نکن، با تگ «⚑ برای معمار» flag کن + جایگزین امن پیشنهاد بده.

---

## ۱۱. نقشهٔ راه ۱۰ مرحله‌ای

> منبع: `00 - Control/ROADMAP-10-STAGES-2026-07-12.md`. هر مرحله دروازهٔ بعد است.

| # | مرحله | مسئول | دروازه | «تمام» وقتی |
|---|---|---|---|---|
| ۱ | بستنِ GATE 0 + verdictها | **تو** | — | G0 ثبت، Branch A/B، نام برند |
| ۲ | پایهٔ حقوقی/بانکی/opsec | تو + ایجنت | G0 | پول‌گیری ممکن + opsec سبز |
| ۳ | ساختِ اکانت‌ها و پلتفرم | **تو (فقط تو)** | ۲ | اکانت verify + link-hub |
| ۴ | سیستمِ تولیدِ محتوا (خالق) | صبا + ایجنت | G0 | بانکِ محتوای certify‌شده |
| ۵ | بانکِ کپی + سیم‌کشیِ مغز | **ایجنت** | ۴ | pipeline از بانک واقعی |
| ۶ | زنده‌کردنِ قیفِ اکتساب | تو (flip+post) | ۳ و ۵ | اولین ترافیک → فروش |
| ۷ | نردبانِ درآمد و قیمت | تو(verdict)+ایجنت | ۶ | قیمت/PPV/custom زنده |
| ۸ | نگه‌داری و CRM | صبا/تو + ایجنت | ۶ | auto-renew در صعود |
| ۹ | تحلیل، یادگیری، حلقهٔ هفتگی | ایجنت + تو | ۶ | تصمیمِ داده‌محورِ هفتگی |
| ۱۰ | مقیاس، تفویض، پایداری | **تو** | ۷–۹ | SOP-محورِ پایدار |

> **قانونِ طلاییِ هر مرحله:** AI draft می‌زند، **انسان می‌فرستد/پست می‌کند**.

---

## ۱۲. خطرات و تله‌ها

> منبع: `DEEP-SCAN-2026-07-17` §8. **حتماً بخوان.**

1. **PII در `langar/langar_config.json`:** نام واقعی، شماره تلفن، آدرسِ A. در `.gitignore` ولی اگر push شده، rotate شود. **بزرگ‌ترین opsec ریسک.**
2. **`docs/` و `research/` آینهٔ stale‌اند** — همیشه نسخهٔ root را بخوان (تأیید md5 در CARTOGRAPHY).
3. **`studio/drafts.json`** حالا `[]` است (ریست ۰۷-۱۶) — دیگر fixture تستی نیست.
4. **commit با pathspec:** این tree ~۳۰۵ فایل dirty از `_ops` دارد. همیشه `git commit -- <files>`.
5. **آنتی‌ویروس:** `git add` گاهی Permission denied می‌دهد → retry با sleep.
6. **۲۳ worktree** در `.claude/worktrees/` — بعضی stale. فقط روی main-vault کار کن.
7. **`orchestrator.py` dead:** آن را standalone اجرا نکن؛ کرش می‌کند (وابسته به `_ops/neural`).
8. **استعارهٔ اختاپوس تزئینی نیست ولی ناقص است:** observability زنده، **actuation فلج**. `octopus_core` نیمه‌سیم.
9. **verdict منفی = موفقیت:** نتایج را متورم نکن.
10. **هرگز حذف؛ فقط انتقال** به `_Archive`/`_Duplicates`.

### تعارض‌های باز (باید reconcile شوند قبل از اجرا)
| # | موضوع | تعارض | وضعیت |
|---|---|---|---|
| ۲ | نام برند | **Anar Soles** vs Arch & Amber / Yalda Arch | ⚠️ منتظر verdict نهایی |
| ۳ | نردبان قیمت | MASTER-BUILD VIP $۳۵ / Playbook $۲۰ / EXT-04 $۳-۵/۸-۱۵/۱۵-۳۰ | ⚠️ ۳ نسخه |
| ۴ | نقش Fansly | mirror-of-OF vs equal-weight-day-1 | ⚠️ منتظر verdict |
| ۵ | «Persian»/«Sydney» در کپی | تحقیق بیرونی توصیه می‌کند vs ۲ قاعدهٔ قفل‌شده ممنوع | ⚠️ OPEN (P0-opsec) |
| ۶ | body expansion | production plan دارد vs C رد کرده | ⚠️ OPEN |

---

## ۱۳. ترتیبِ لود (Load Order)

> منبع: `HANDOFF-NEXT-AGENT.md` §0 + `DEEP-SCAN` §9.

در اولین جلسه، به‌ترتیب بخوان:
۱. این فایل (دیپ‌اسکن × اختاپوس).
۲. `_memory/onlyfans-project-memory-2026-07-05.md` — حافظهٔ پروژه.
۳. `PROJECT-F-CONTROL-MANIFEST.json` 🏆 — قراردادِ ماشین‌خوان.
۴. `CLAUDE.md` — منشور (قواعد قفل‌شده §۱).
۵. `PROJECT.md` — Active Context.
۶. `00 - Control/ROADMAP-10-STAGES-2026-07-12.md` — 🧭 بعدی چه کن.
۷. `02 - Research/COMPETITOR-MARKET-LANDSCAPE-2026-07-12.md` — چرا این مسیر.
۸. `ARCHITECTURE-SOT.md` (repo root) — نقشهٔ منبعِ حقیقتِ اجرایی.
۹. `_ops/legs/langar_bridge.py` — پلِ اتصال به اختاپوس (اگر روی اتصال کار می‌کنی).

---

## ۱۴. فهرستِ کاملِ فایل‌های کلیدی

### کنترل (`00 - Control/`)
- `DEEP-SCAN-2026-07-17-FOR-NEXT-AGENT.md` — خلاصهٔ فشردهٔ کل پروژه.
- `HANDOFF-NEXT-AGENT.md` — برنامهٔ ایجنت بعدی (توجه: ۰۷-۱۲، قدیمی‌تر از چرخشِ ۰۷-۱۶).
- `NEXT-AGENT-PROMPT-2026-07-17-PF-LAUNCH.md` — پرامپتِ مسیر الف (لانچ).
- `ROADMAP-10-STAGES-2026-07-12.md` — 🧭 نقشهٔ راه.
- `RISK-LADDER.md` — نردبان ریسک.
- `SOURCE-OF-TRUTH-MATRIX.md` — منبع حقیقت.
- `CARTOGRAPHY-2026-07-12.md` — نقشهٔ فعلی.
- `MIGRATION-MAP-2026-07-12.md` — نقشهٔ مهاجرت (پشت verdict PF-STRUCT-V2).

### استراتژی/هویت (`01 - Strategy/Identity/`)
- `BRAND-CHARTER.md` — منشور برند.
- `BRAND-NAME-DECISION.md` — تصمیم نام (Anar Soles).
- `CLAIMS-REGISTER.md`، `IDENTITY.md`، `VOICE-AND-STYLE.md`.

### مغز/استودیو/کاکپیت
- `brain/dual_brain_v3.py`، `brain/acquisition_pipeline.py`، `brain/learning.py`، `brain/store.py`، `brain/guards.py`، `brain/dm_pipeline.py`، `brain/faq_engine.py`.
- `langar/langar_bot.py`، `langar/{pf,dm,fan,vault}_admin.py`.
- `studio/saba_studio.py`، `studio/content_studio.py`، `studio/affirm.py`.

### اتصال به اختاپوس (repo-wide)
- `_ops/legs/langar_bridge.py` — **پلِ Project-F به اختاپوس**.
- `_ops/live_loop.py` — UnifiedBus (مغز Project-F ↔ کاکپیت A).
- `_octopus/config/projects.yaml` — ثبتِ Project-F.
- `ARCHITECTURE-SOT.md` — منبعِ حقیقتِ اجرایی.
- `07 - Knowledge/genome-system/ledger/ledger.jsonl` — ledger ژنوم (content-free NOTE‌ها).
- `_ops/state/ORGANISM-STATE.json`، `_ops/state/events.jsonl`، `_ops/state/cortex/cortex-state.json`.

### مستنداتِ ارگانیسم
- `OCTOPUS/ARCHITECTURE-BIBLE.md` — فرهنگنامهٔ استعاره (۲۶ بخش).
- `شناخت اختاپوس/02-OCTOPUS-KNOWLEDGE-SNAPSHOT.md` — شناخت فعلی.
- `نقشه اختاپوس/SYSTEM-PROMPT.md` — مدل ۶-فیلدِ رجیستری.
- `_PROJECT_INSTRUCTIONS.md` — قانون اساسی ایجنت‌ها.

---

## ✅ چک‌لیستِ متصل‌ماندن (برای فردا)

برای اینکه Project-F به اختاپوس **متصل بماند**، این موارد را چک کن:

- [ ] **ارگانیسم زنده است؟** `_ops/state/ORGANISM-STATE.json` را چک کن. اگر کهنه (>۲ ساعت)، organism.py را START کن (port 8771).
- [ ] **cortex coherence بالاست؟** اگر <۰.۵، members کهنه‌اند؛ ارگانیسم را START کن تا دوباره fresh کنند.
- [ ] **langar_bridge کار می‌کند؟** `OCTOPUS_LANGAR_DIR` یا fallbackِ کانونیکال را چک کن.
- [ ] **Project-F در projects.yaml ثبت‌شده؟** `_octopus/config/projects.yaml` → `project_f: active`.
- [ ] **تست‌ها سبزند؟** `cd "F:/backup/03 - Projects/اونلی فنز" && python -m pytest tests/ -q` + `*/test_*.py`.
- [ ] **GATE 0 وضعیت؟** اگر باز، همهٔ کارهای بیرونی بلاک‌اند (temporary-A فرضی).
- [ ] **PII ریسک؟** `langar/langar_config.json` در `.gitignore` است؟ اگر push شده، rotate.
- [ ] **ledger قرنطینه؟** هیچ محتوای Project-F در `ledger.jsonl` نمی‌رود (فقط content-free NOTE).

---

> **یک‌خطیِ نهایی:** Project-F یک **پا** از اختاپوس است که ۱۰۰٪ برنامه‌ریزی/کد شده، ۰٪ اجرا، ۱۴۸ تست سبز، و پلِ `langar_bridge.py` آن سالم ولی وابسته به ارگانیسمِ زنده است. ارگانیسم الان کهنه‌ست — اول آن را START کن، بعد جلو برو.

---

*تولیدشده توسط ZCode deep-scan، ۲۰۲۶-۰۷-۲۲. همه‌چیز از خواندنِ کد/فایل/state واقعی. مسیرِ هر منبع در متن ذکر شده.*
