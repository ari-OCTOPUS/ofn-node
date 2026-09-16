---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, governor, autoregulation]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
  - "_ops/budget/governor_epoch.py"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P3 — کوپلِ autoregulation: velocity → Governor → spend (additive)

> gate خروج: **governor-decoupled** — نرخِ خامِ ضربان هرگز مستقیم spend را تعیین نمی‌کند؛ بینشان همیشه Governor است. پیش‌نیاز: HH-P1.

## مأموریت

`governor_epoch.py` از قبل autoregulation است (`pressure_state → epoch_length_minutes → allocate_dry`). این پرامپت حلقهٔ ضربان↔spend را می‌بندد بدونِ اینکه یک بایت از مسیرِ پول عوض شود: velocity و Internal-CPI به‌عنوانِ ورودیِ *فشار/سفتی* واردِ Governor می‌شوند — نه واردِ تخصیص.

## نگاشتِ اقتصادی (توصیهٔ مالک)

`ضربان ↔ velocity` · `تورم ↔ Internal-CPI (نویزِ سیگنالِ attribution)` · `ثباتِ پولی ↔ همین ماژول`. درسِ کلیدی: «نگذار نرخِ خامِ oscillator مستقیم spend را تعیین کند؛ یک لایهٔ autoregulation بگذار.» CPIِ بالا یعنی سیگنالِ ارزش نویزی است → تخصیصِ سریع‌تر فقط دنبال‌کردنِ نویز است → **Governor سفت می‌شود** (بازبرنامه‌ریزیِ کندتر + explore محتاطانه‌تر)، مثلِ بانکِ مرکزی در تورم.

## تحویل‌دادنی‌ها

1. **`_ops/heart/autoregulation.py`** (stdlib):
   - `velocity_pressure(velocity_state, setpoint) → dict` — گپِ نرمالِ velocity نسبت به باند (استال زیرِ باند → مؤلفهٔ فشارِ کران‌دار `0..0.5` برای بازبرنامه‌ریزیِ زودتر؛ داخل باند → 0).
   - `cpi_tightening(cpi_state) → dict` — `tighten ∈ [0..1]` از Internal-CPI؛ خروجی: `epoch_damping ∈ [1.0..2.0]` (epoch را کش می‌دهد) + `explore_advice_pct` (پیشنهادِ کاهشِ explore — advisory فقط).
   - `governor_view(snap=None) → dict` — ترکیبِ دو تای بالا از state-fileهای HH-P1 + setpointِ HH-P2؛ fail-soft (فایل غایب → `{"available": False}`).
2. **پیوندِ additive در `governor_epoch.run_epoch`** — پشتِ `OCTOPUS_WIRE_HEART` (پیش‌فرض خاموش = بایت‌به‌بایت رفتارِ فعلی):
   - `record["heart_autoreg"] = governor_view(snap)` (مشاهده در epoch-file + کابین).
   - فشارِ مؤثرِ epoch: `p_eff = min(1.0, max(p, heart_pressure) ) / epoch_damping` فقط وقتی flag روشن؛ در recordِ epoch هر دو (خام و مؤثر) ثبت شوند.
   - **`allocate_dry` و `pressure_state` بایت‌به‌بایت دست‌نخورده** — کوپل فقط در `run_epoch` (لایهٔ orchestration).
3. **تست** (`test_heart_loop.py`): flag خاموش → خروجیِ `run_epoch` بدونِ کلیدِ `heart_autoreg` و طولِ epoch عیناً قبلی؛ flag روشن + CPI بالا → epoch بلندتر (سفت‌تر)، نه کوتاه‌تر؛ استال → فشارِ کران‌دار؛ ساختاری: `autoregulation.py` هیچ importی از `organ_gate/money_gate/attribution-write` ندارد و `allocate_dry` امضایش/بدنه‌اش عوض نشده.

## خطوطِ قرمز

هیچ تغییری در تخصیصِ پول (I2: صفر enforce در shadow) · مؤلفهٔ فشارِ قلب هرگز `>0.5` (ضربان نمی‌تواند Governor را تسخیر کند) · epoch_damping هرگز `<1.0` (CPI فقط سفت می‌کند، شل نمی‌کند) · flag خاموش = no regression اثبات‌شده با تست.
