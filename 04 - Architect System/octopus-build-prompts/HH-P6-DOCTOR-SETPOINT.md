---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, doctor, setpoint, w-slow]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P6 — دکترِ تکاملی = مدولاتورِ w-slow (نویسندهٔ setpoint، هرگز نرخ)

> gate خروج: **doctor-wired** — per-epoch باندِ target-velocity را می‌نویسد و از نتیجه یاد می‌گیرد؛ LLMِ پولی پشتِ live-gate. «Doctor setpoint می‌نویسد نه نرخ» (ADR-001).

## تحویل‌دادنی‌ها

1. **`_ops/heart/doctor_setpoint.py`** (stdlib، $0 پیش‌فرض):
   - `propose_setpoint(prev: HeartParams|None, signals: dict, lock: dict) → HeartParams` — سیاستِ قطعیِ w-slow:
     - baseline: باندِ فعلی (یا پیش‌فرضِ محافظ از config).
     - **یادگیریِ کند**: EMA-ی velocityِ محقق‌شده در وضعِ سالم → میانهٔ باند به آن میل می‌کند؛ `g_learn` بالا (Δ_selfِ authoritative) → سقفِ باند تا +۵۰٪؛ CPI بالا یا σ-alert → باند به سمتِ کف جمع می‌شود (استراحت).
     - **hysteresis سخت**: حداکثر ±۲۰٪ تغییرِ باند per epoch؛ کران‌های مطلقِ config هرگز رد نمی‌شوند؛ `epoch_seq` همیشه +۱ (monotonic).
   - `run_epoch_setpoint(write=True) → dict` — خواندنِ سیگنال‌ها/lock/قبلی → propose → `interface.write_setpoint` + `opslib.ledger_note("HEART_SETPOINT", {band, epoch_seq, rationale}, actor="heart-doctor")`. propose-only: هیچ مسیرِ merge/effector.
   - `llm_refine(setpoint, signals) → None|dict` — چند-ایجنتیِ پولی (4d_system/brain الگو): **پشتِ `opslib.live_gate_open(ACTIVATION-HEART-DOCTOR.flag)`** — امروز ساختاراً None (تاریخ). شکست/بسته = برگشتِ امن به سیاستِ قطعی (الگوی `allocate_llm`).
2. **اتصال**: در `wiring.heart_beat`، هر `CHRONO_HEART_SETPOINT_EVERY_N_BEATS` (**پیش‌فرض ۱۴۴۰ = روزانه** — واحدِ beat ضربانِ ۶۰ثانیه‌ایِ chrono است نه tickِ ۳۰۰s؛ اصلاحِ ریویو: ۲۸۸ می‌شد ۴.۸ساعت و w-slow را ۵× تند می‌کرد) با پنجرهٔ anti-alias، `run_epoch_setpoint()` صدا زده شود — همان الگوی doctor_beat.
3. **تست** (`test_heart_loop.py`): hysteresis (جهشِ بزرگِ سیگنال → حداکثر ±۲۰٪ حرکت)؛ CPI بالا → باند جمع می‌شود؛ epoch_seq یکنواخت؛ `llm_refine` امروز None؛ ساختاری: خروجی فقط HeartParams (هیچ period/rate)؛ **هیچ importِ پول در سطحِ ماژول** — مسیرِ LLM طبقِ I2 موظف است lazy از `organ_gate.reserve/settle` عبور کند (الگوی allocate_llm)، پس ممنوعیت فقط top-level است (اصلاحِ ریویو).

## خطوطِ قرمز

هرگز نرخ ننویسد — فقط باند (ساختاراً از HH-P2) · تغییرِ کند و کران‌دار (w-slow؛ ضدِ تسخیرِ قلب توسط Doctor) · σ فقط از CONFIRMED (`replication`) · LLM فقط پشتِ گیتِ دوقفلهٔ مالک+تاریخ · propose-only مطلق.
