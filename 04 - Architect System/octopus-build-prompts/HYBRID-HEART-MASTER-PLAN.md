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
| **P0** | **قفلِ ریاضیِ SOG** | anchorهای `4.py` را بازتولید کن؛ **E_shadow و I_pred را مستقلاً MC-validate کن** (نه دوباره‌مشتقِ همان فرمول)؛ ثابت‌های قفل‌شده + provenance را در یک lock-file بنویس | math-locked (اثباتِ مستقل، نه دوری) | `4d_system/core`, `Desktop/4D/4.py`, SOG-synthesis §C/G | planned |
| **P1** | **producerهای زنده (Gate-0)** | سه سنجهٔ زنده و $0: `velocity_meter` (throughput از CONFIRMED/effect/beat)، `internal_cpi` (signal-to-noise سیگنالِ attribution)، `delta_self_estimator` (blind/informed losses) — همه read-only، external-provenance → state-file | live-producers-exist (بدونِ اینها production بلاک) | `replication.py`, `telemetry.py`, پورتِ `4d_system/core/scores.py` | planned |
| **P2** | **interfaceِ typed + ratify ADR-001** | `HeartParams`/`HeartSignal` (§۵ ADR)؛ seam در `organism.py:420-431`/`cardiac.effective_period`؛ ADR-001ِ موجود را ratify کن (بازنویسی نکن) | interface-locked | `ADR-001`, `cardiac.py`, `organism.py` | planned |
| **P3** | **کوپلِ autoregulation** | `velocity → governor_epoch (autoregulation) → spend`؛ Internal-CPI بالا → Governor سفت؛ **نرخِ خام هرگز مستقیم spend را تعیین نکند** | governor-decoupled | `governor_epoch.py` (موجود), P1 | planned |
| **P4** | **control-law + شبیه‌سازی** | بازنگریِ `M-HEART-SOG-Pacemaker` برای velocity+autoregulation؛ period از velocity ظاهر می‌شود، SOG باندِ هدف؛ **sim-first** ($0، closed-loop، bounded، محترمِ σ-cap) | SIM-PASS | `M-HEART-…-BUILD-PROMPT`, `4d_system/core/simulator.py` | planned |
| **P5** | **shadow + wiringِ owner-gated** | کلِ قلبِ کوپل در shadow (محاسبه می‌کند ولی set نمی‌کند) → پشتِ flag + فعال‌سازیِ مالک | shadow-clean | cockpit (نمایشِ shadow beat) | planned |
| **P6** | **دکترِ تکاملی = مدولاتورِ w-slow** | محققِ خودمختارِ چند-ایجنتی که per-epoch باندِ target-velocity را می‌نویسد و یاد می‌گیرد؛ LLMِ پولی پشتِ live-gate | doctor-wired | `doctor.py`, `4d_system/brain`, تصمیم‌های دکترِ تکاملی | planned |
| **P7** | **سطحِ کابین + پذیرش** | قلبِ زنده را در کابینِ تلگرام نشان بده (velocity، Internal-CPI، باندِ هدف، Governor، shadow-vs-live)؛ کلِ سوییت سبز | suite-green | cockpit v2 | planned |

**مسیرِ بحرانی:** P0 (قفلِ ریاضی) + P1 (Gate-0) **پیش‌شرطِ همه‌چیزند** — طبقِ ریویوِ M-Heart، بدونِ ریاضیِ قفل‌شده + producerِ زنده، «ضربانِ emergent» توهم است. اول این دو.

**اصلِ حاکم بر کلِ لیست:** coupled-not-merged (ADR-001) · velocity-not-inflation · autoregulation-between-beat-and-spend · sim-before-wire · $0-until-live-gate · هیچ self-grading.
