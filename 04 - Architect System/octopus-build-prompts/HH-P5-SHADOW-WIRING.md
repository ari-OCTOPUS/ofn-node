---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, shadow, wiring]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
  - "[[04 - Architect System/octopus-build-prompts/M-HEART-SOG-Pacemaker-BUILD-PROMPT]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P5 — shadow + wiringِ owner-gated (seam: حلقهٔ متابولیسم)

> gate خروج: **shadow-clean** — قلب در سایه محاسبه می‌کند، هرگز set نمی‌کند؛ فعال‌سازیِ زنده فقط با predicateِ کاملِ مالک. seam = `organism.py:420-434` (`_sleep_s`)، **نه** HLC/`chrono.py`.

## تحویل‌دادنی‌ها

1. **`_ops/heart/shadow.py`**:
   - `shadow_step(beat, snap=None) → dict` — زنجیرهٔ کامل در سایه: `producers.compute_all` → `append_velocity_sample` → خواندنِ setpoint (HH-P2) → `control_law.heart_step` → append به سینکِ جدا `_ops/state/pulse/heart-params-shadow.jsonl` + `LockedJson(state/pulse/heart-shadow-latest.json)`. **هرگز `_sleep_s`/`period_s` ارگانیسم را نمی‌نویسد.**
   - `production_wire_open() → (bool, reasons:list[str])` — predicateِ کاملِ M-HEART §۴ (همه باید true):
     `SIM_PASS` (از HEART-SIM-REPORT) ∧ `equations-locked` (PULSE-EQUATIONS-LOCKED؛ e_shadow locked یا excluded-با-ack) ∧ `Gate-0` (delta_self_estimator با authoritative=true موجود) ∧ `code-hash match` (sha256 فعلیِ control_law == ثبت‌شده در lock) ∧ `OCTOPUS_WIRE_BIO=1` ∧ `OCTOPUS_WIRE_PULSE=1` ∧ `ACTIVATION-PULSE.flag` (فقط مالک) ∧ `date ≥ 2026-07-21` (`opslib.live_gate_open` الگو). امروز ساختاراً false — درست همین است.
2. **`wiring.heart_beat(beat, snap=None) → dict|None`** — الگوی خانه: پشتِ `OCTOPUS_WIRE_HEART` (پیش‌فرض خاموش، **عمداً خارج از PAPER_FULL_FLAGS** — ورود به profile فقط با رأی مالک)؛ kill-switch اول (`STOP_ORGANISM/halted`)؛ cadence با `CHRONO_HEART_EVERY_N_BEATS` (پیش‌فرض ۱ = هر tick) و پنجرهٔ anti-alias؛ try/except → `opslib.alert` (خطای خاموش ممنوع).
3. **seam در `organism.py`** (دقیقاً دو لمس، هر دو fail-soft — اصلاحاتِ ریویو):
   - در بدنهٔ tick (کنارِ بقیهٔ `*_beat`ها): `_heart_status = _w.heart_beat(...)` → واردِ state فقط شرطی: `**({"heart": _heart_status} if _heart_status else {})` (flag خاموش → هیچ کلیدی، شکلِ state بایت‌به‌بایت).
   - در بلوکِ انتهاییِ `_sleep_s` (بعد از cardiac): **کلِ بلوک پشتِ نتیجهٔ heart_beat** (نه فراخوانیِ بی‌قیدِ predicate هر tick) و در try/except محلی: فقط اگر `_heart_status` موجود و `_heart_status["production_wire"]["open"]==True` → `_sleep_s = clamp(period سایه، FLOOR..MAX)`. flag خاموش = heart_beat=None = صفر کارِ اضافه، صفر ریسکِ crash (بلوکِ `_sleep_s` بیرونِ try اصلیِ tick است).
   - **لنگرِ hash**: predicate هشِ `control_law.py` فعلی را با `code_sha256` ثبت‌شده در `HEART-SIM-REPORT.json` می‌سنجد (نه lockِ P0 — آنجا هشِ sog_math است).
4. **تست** (`test_heart_loop.py`): flag خاموش → `heart_beat` None و هیچ فایلِ سایه؛ flag روشن → سینکِ سایه پر می‌شود ولی هیچ‌چیزِ دیگرِ state دست نمی‌خورد؛ `production_wire_open` امروز false با دلایلِ کامل (تاریخ + flag غایب + …)؛ جعلِ تک‌شرط (مثلاً ساختنِ ACTIVATION-PULSE.flag در tmp) هنوز false (بقیهٔ شرط‌ها).

## خطوطِ قرمز

shadow هرگز period را نمی‌نویسد (سینکِ جدا) · `chrono.py`/Pacemaker/HLC دست‌نخوردنی · reaperِ برون‌حلقه: crashِ heart_beat نباید tick را بکشد (try/alert) · فعال‌سازی = فقط مالک (flag-file + env + تاریخ) · بدونِ flag: بایت‌به‌بایت رفتارِ فعلی (تستِ no-regression).
