---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, calibration, post-merge]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
  - "[[01 - Dashboard/HANDOFF]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P8 — کالیبراسیونِ پس از merge (سه رأیِ مصوبِ مالک، 2026-07-10)

> اجرا: **فقط بعد از merge** شاخهٔ `claude/heartbeat-velocity-governor-777b92` به master، روی درختِ زنده. این سه تصمیم در مشورتِ مستقیم با مالک قفل شده‌اند — گزینه‌ها را دوباره باز نکن؛ فقط پیاده و تست کن.

## رأی ۱ — seedِ خودکارِ باندِ اولیه از واقعیت

**مشکل:** باندِ پیش‌فرضِ `HeartParams` (0.5..6.0 بر ساعت) برای ارگانیسمِ فعلی (velocity واقعی ~۰.۰۸) خیلی بالاست؛ همگراییِ w-slow با ±۲۰٪/روز ۲-۳ هفته طول می‌کشد.

**پیاده‌سازی در `_ops/heart/doctor_setpoint.py`:**
- در `propose_setpoint`، وقتی `prev is None` (هیچ setpointِ قبلی روی دیسک نیست) **و** `velocity_per_hr` موجود است (حتی non-authoritative): باند را از مشاهده seed کن — `mid = max(v_obs, 0.02)`، `width = max(v_obs, 0.1)` → `lo = max(0.02, mid − width/2)`، `hi = mid + width/2` (validate طبقِ کران‌های مطلق). در rationale صریح بنویس `seeded-from-observation`.
- اگر در اولین epoch velocity هنوز None بود، **seed را به تعویق بینداز**: setpoint ننویس (return با `written:false, reason:"awaiting-first-velocity"`)، تا اولین epochی که مشاهده هست. hysteresis ±۲۰٪ فقط از epoch دوم به بعد اعمال می‌شود (seed از قیدش معاف است — یک‌باره).
- تست: `test_heart_loop.py` — یک چکِ نو: بدونِ setpointِ قبلی + سیگنالِ v=0.08 → باندِ نوشته‌شده حدودِ [0.02..0.13] (نه 0.5..6.0) و rationale شاملِ seed؛ و بدونِ velocity → `written:false`.

## رأی ۲ — وزنِ پول در velocity: CONFIRMED ×۳

**پیاده‌سازی در `_ops/heart/producers.py`:**
- در `velocity_meter`، دیکشنریِ وزن‌ها: `confirmed = float(os.environ.get("HEART_W_CONFIRMED", "3.0"))`؛ بقیه بی‌تغییر (`effects=1.0, consolidation=1.0, beats=0.1`).
- `sample_size` همچنان شمارشِ خام (بدونِ وزن) بماند — وزن فقط روی `velocity_per_hr` اثر می‌گذارد، نه روی authoritative (وگرنه وزنِ بالا مصنوعی authoritative می‌سازد).
- تست: `test_heart_producers.py` — چکِ نو: با ۱ CONFIRMED و ۱ effect در پنجره، velocity برابرِ `(3+1)/window` (نه `2/window`).

## رأی ۳ — کفِ periodِ حالتِ زنده: ۶۰ ثانیه

**پیاده‌سازی:**
- در seam ِ `organism.py` (بلوکِ override بعد از cardiac): `_sleep_s = max(60.0, min(900.0, _hp))` — عددِ ۳۰ فقط برای ریاضی/سایه/sim معتبر می‌ماند (`control_law.FLOOR_S` دست‌نخورده؛ ریل‌های M-HEART عوض نمی‌شوند). env-پذیر: `HEART_LIVE_FLOOR_S` پیش‌فرض `60`.
- دلیلِ ثبت‌شده: هر tick تلمتریِ کامل می‌خواند؛ کفِ ۳۰ یعنی تا ۱۰× I/O فعلی — مالک ۶۰ را انتخاب کرد (تا ۵×).
- تست: `test_heart_loop.py::t_h_organism_seam...` را به‌روز کن (رشتهٔ ساختاریِ seam حالا `max(60.0` یا `HEART_LIVE_FLOOR_S` را چک کند).

## پس از اعمال

۱) چهار فایلِ تستِ heart + سوییتِ کامل سبز (`REAL_VAULT` لازم نیست — روی درختِ زنده‌ای). ۲) یک‌بار `python -X utf8 _ops/heart/sog_math.py` اگر هنوز اجرا نشده (lock + NOTE). ۳) HANDOFF + این فایل → `status: done`. ۴) commit با `agent-checkpoint:`.

## خطوطِ قرمز (بی‌تغییر)

هیچ دستکاریِ predicateِ ۸شرطی، σ-taint، درخت‌وارهٔ پول، یا chrono/HLC. این پرامپت فقط سه knob کالیبراسیون است.
