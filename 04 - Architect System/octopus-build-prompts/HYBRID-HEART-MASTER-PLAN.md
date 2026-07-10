---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, doctor, sog, governor, velocity]
created: 2026-07-10
updated: 2026-07-10
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
extends: "[[04 - Architect System/SOG-Doctor-Synthesis-A-K]]"
---

# HYBRID-HEART — نقشهٔ اصلی + لیستِ پرامپت‌ها (قلبِ تکاملیِ ترکیبی)

> سندِ برنامه‌ریزیِ واحد. **طراحیِ نرخِ ضربان** (بخش ۱) + **لیستِ مرتبِ پرامپت‌ها** (بخش ۲) که ایجنتِ بعدی گام‌به‌گام اجرا می‌کند تا قلبِ ترکیبی زنده شود. هر پرامپت وقتی authored شد، جداگانه adversarial-review می‌شود.

## بخش ۱ — طراحیِ نرخِ ضربان (velocity + autoregulation + SOG-setpoint)

**تصحیحِ بنیادی (توصیهٔ مالک، 2026-07-10):** ضربانِ قلب = **velocity of money**، نه تورم. ضربان = فرکانسِ یک فرآیندِ واقعی = «چقدر داده/کارِ شناختی در واحدِ زمان پردازش می‌شود». نگاشتِ درست:
`ضربان ↔ velocity` · `تورم ↔ نویز/بی‌ثباتیِ واسط (Internal-CPI)` · `ثباتِ پولی ↔ autoregulation (Governor)`.

**چهار مؤلفهٔ طراحی (grounded به کد):**
1. **ضربان = velocity** — توان‌عبورِ واقعیِ شناخت در واحدِ زمان: settleهای CONFIRMED، مصرفِ effect، چرخه‌های consolidation، پیام/گام در واحدِ زمان. **gauge-invariant** و **external-provenance** (از رویدادهای CONFIRMED/effect، نه خودگزارش) → self-grading نمی‌شود (گاردِ منتقدها).
2. **SOG = setpoint، نه نرخِ خام** (ADR-001) — Δ_self بالا (یادگیریِ فعال) → target-velocity بالاتر؛ E_shadow پایدار → استراحت؛ σ (CONFIRMED) → سقفِ سختِ سلامت. SOG **باندِ هدف** را تعیین می‌کند؛ نرخ *ظاهر* می‌شود.
3. **Governor = autoregulation** — `governor_epoch.py` از قبل این است (`pressure_state → epoch_length_minutes → allocate_dry`). بین ضربان و spend می‌نشیند تا ضربانِ تند **spendِ تورمی/اتلافی** نسازد. یک **Internal-CPI** (نویزِ سیگنالِ attribution/reward) وقتی بالا رفت، Governor را سفت می‌کند («واسطِ ارزش» = budget/ATP را پایدار نگه می‌دارد).
4. **دو timescale (از قبل در کد):** ضربانِ تند = حلقهٔ متابولیسمِ `organism.py:420-431` (`_sleep_s = cardiac.effective_period(...)`)؛ autoregulationِ کند = epoch‌های Governor. این همان fast/slow (v/w) در ADR-001 و «سیگنالِ سراسریِ نازکِ کُند + خودمختاریِ محلیِ تندِ قوی» است.

**دیوارهای ایمنی (بی‌تغییر):** velocity از منبعِ read-only/external؛ ضربان حلقهٔ متابولیسم را مدوله می‌کند نه HLC/`chrono.py`؛ **sim-first**؛ **Gate-0** (producerِ زندهٔ واقعی لازم است — وگرنه توهمِ ضربانِ emergent)؛ $0 (LLM/Doctorِ پولی پشتِ live-gate تا 2026-07-21)؛ propose-only؛ σ≤1؛ reaperِ برون‌حلقه.

## بخش ۲ — لیستِ مرتبِ پرامپت‌ها (roadmap اجرا)

هر ردیف یک build-prompt است که باید نوشته شود. ترتیب = وابستگی. `gate` = شرطِ عبور به بعدی.

| # | پرامپت | دامنه (چه می‌سازد) | gate | استفاده از | وضعیت |
|---|---|---|---|---|---|
| **P0** | **[[04 - Architect System/octopus-build-prompts/HH-P0-SOG-MATH-LOCK\|HH-P0]]** | anchorهای `4.py` را بازتولید کن؛ **E_shadow و I_pred را مستقلاً MC-validate کن** (نه دوباره‌مشتقِ همان فرمول)؛ ثابت‌های قفل‌شده + provenance را در یک lock-file بنویس | math-locked (اثباتِ مستقل، نه دوری) | `4d_system/core`, `Desktop/4D/4.py`, SOG-synthesis §C/G | ✅ built (`_ops/heart/sog_math.py` + lock رسمی) |
| **P1** | **[[04 - Architect System/octopus-build-prompts/HH-P1-LIVE-PRODUCERS\|HH-P1]]** | سه سنجهٔ زنده و $0: `velocity_meter`، `internal_cpi`، `delta_self_estimator` (blind/informed) — read-only، external-provenance، نمونه‌گیریِ ساعت-ثابت → state-file | live-producers-exist (بدونِ اینها production بلاک) | `attribution/ledger`, `chrono.db`, `consolidation.json` | ✅ built (`_ops/heart/producers.py`) |
| **P2** | **[[04 - Architect System/octopus-build-prompts/HH-P2-INTERFACE-RATIFY\|HH-P2]]** | `HeartParams`/`HeartSignal` (§۵ ADR)؛ seam در `organism.py:420-434`؛ ADR-001 ratify شد (append، بازنویسی نه) | interface-locked | `ADR-001`, `cardiac.py`, `organism.py` | ✅ built (`_ops/heart/interface.py` + ADR ratified) |
| **P3** | **[[04 - Architect System/octopus-build-prompts/HH-P3-GOVERNOR-AUTOREGULATION\|HH-P3]]** | `velocity → governor_epoch → spend-cadence`؛ CPI بالا → Governor سفت؛ **نرخِ خام هرگز مستقیم spend را تعیین نکند** | governor-decoupled | `governor_epoch.py`, P1 | ✅ built (`_ops/heart/autoregulation.py` + کوپلِ additive پشتِ flag) |
| **P4** | **[[04 - Architect System/octopus-build-prompts/HH-P4-CONTROL-LAW-SIM\|HH-P4]]** | Living-Beat برای velocity؛ period ظاهر می‌شود، SOG باند؛ sim closed-loop (S1..S9 + G<1) | SIM-PASS | M-HEART, P0..P3 | ✅ built + **SIM-PASS** (گزارشِ رسمی در state/sim) |
| **P5** | **[[04 - Architect System/octopus-build-prompts/HH-P5-SHADOW-WIRING\|HH-P5]]** | کلِ قلب در shadow (سینکِ جدا) + predicateِ ۸شرطیِ owner-gated در seam | shadow-clean | organism.py, wiring.py | ✅ built (`heart_beat` + `production_wire_open`) |
| **P6** | **[[04 - Architect System/octopus-build-prompts/HH-P6-DOCTOR-SETPOINT\|HH-P6]]** | دکترِ w-slow: باندِ target-velocity per-epoch (hysteresis ±۲۰٪)؛ LLM پشتِ live-gate | doctor-wired | ADR-001, P2 | ✅ built (`_ops/heart/doctor_setpoint.py`) |
| **P7** | **[[04 - Architect System/octopus-build-prompts/HH-P7-COCKPIT-ACCEPTANCE\|HH-P7]]** | کارتِ قلب در کابین (velocity/باند/CPI/قفل‌ها/predicate) + سوییتِ کامل سبز | suite-green | cockpit v2 | ✅ built (کارتِ ♥️ ضربان + ۴ فایلِ تست در run_all) |

**اجرا شد (2026-07-10، جلسه ۴۶):** هر ۸ پرامپت authored + adversarial-reviewed (۲ بازبین، ۱۳ یافته، همه fold شد — از جمله ضدِ self-grading کوواریت‌ها، taintِ σ، cadence دکتر ۱۴۴۰، بهرهٔ حلقهٔ Δ) و **کد کامل ساخته شد**: پکیجِ `_ops/heart/` (۹ ماژول) + ۴ فایلِ تست (۴۱ چک). قفلِ ریاضی: هر سه کمیت `locked` (E_shadow برای اولین بار MC-validated — کاری که 4.py نکرده بود). فعال‌سازی: `OCTOPUS_WIRE_HEART=1` فقط سایه؛ زنده = predicateِ ۸شرطی (تاریخ ≥ live-gate + ACTIVATION-PULSE.flag مالک + SIM_PASS + Gate-0 + hash + BIO + PULSE).

**مسیرِ بحرانی:** P0 (قفلِ ریاضی) + P1 (Gate-0) **پیش‌شرطِ همه‌چیزند** — طبقِ ریویوِ M-Heart، بدونِ ریاضیِ قفل‌شده + producerِ زنده، «ضربانِ emergent» توهم است. اول این دو.

**اصلِ حاکم بر کلِ لیست:** coupled-not-merged (ADR-001) · velocity-not-inflation · autoregulation-between-beat-and-spend · sim-before-wire · $0-until-live-gate · هیچ self-grading.
