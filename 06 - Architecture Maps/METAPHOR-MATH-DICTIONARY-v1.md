---
type: reference
status: active
tags: [octopus, math, metaphor]
created: 2026-07-24
updated: 2026-08-05
---
# 📐 دیکشنریِ استعاره → ریاضی (v1)
> ۲۰۲۶-۰۷-۲۴ · هر استعاره = کمیت + فرمول + منبعِ داده + آستانه. برچسب [hypothesis] = فرمولِ پیشنهادیِ من؛ [FACT] = کدِ موجود.

| استعاره | کمیت | فرمول | منبعِ داده | آستانه‌ی هشدار | برچسب |
|---|---|---|---|---|---|
| **سایه (shadow)** | آنچه از حالتِ نهفته‌ی ارگانیسم به آینده‌اش می‌گذرد | `E_shadow_proxy = −½·log(1−ρ̂²)` روی سریِ شمارشِ رویداد/دقیقه | `_ops/state/events.jsonl` → `synapse/sense.py` | > ۳× میانه‌ی ۷روز [hypothesis] | [FACT: core/metrics.py::fit_shadow_parameters] |
| **خود/دیگری (Δ_self)** | ارزشِ دسترسیِ اول‌شخص نسبت به ناظرِ بیرونی | canonical: `Δ_self=0.122520`؛ پروکسیِ ارگانیسم: `temporal_mi(تنوعِ عامل‌ها) − temporal_mi(شمارشِ خام)` | events.jsonl (دو سری) → sense.py | < ۰ ⇒ سیگنالِ نشتِ مرزِ هویت [hypothesis] | canonical [FACT: core/model.py]؛ پروکسی [hypothesis] |
| **قلب (cpm)** | انحرافِ ضربان از باندِ setpoint | `overshoot = max(cpm) − ceiling` · `settling_time` | `ORGANISM-STATE.json.beat` + heart state | بیرون از باندِ ۶٫۴۰–۱۹٫۱۹ [EST از مگاپرامپت] | [hypothesis] |
| **ژنوم (genome)** | فاصله از قانون + اصالتِ لنگرها | `distance_from_genome` (guardian) + `anchor_hash = sha256(E_shadow\|Δ_self\|identity)` | `genome-system/ledger` + b6 schema | هر تغییرِ لنگر = جهش = توقف (ساختاری) | [FACT: guardian + schema] |
| **خواب/رویا** | کیفیتِ محاسبه‌ی آفلاین | `dream_q = similarity(output, anchor) − λ·latency_delta` | `4d_system/llm/shadow_compare.py` outputs | dream_q < میانه‌ی ۷روز − ۲σ [hypothesis] | [hypothesis] |
| **رشد** | سرعتِ گشایشِ سلول‌های تازه‌ی رفتار | `open_score = 2.0·new_cells + 0.5·improved` + شمارِ `capabilities.json` | `4d_system/outputs/self_evolved/` | رشدِ صفر در ۳۰ روز ⇒ مرورِ معماری [hypothesis] | [FACT-0717: self_evolve.py] |
| **بقا (SURV-1)** | fitnessِ واقعیِ هر اندام | `SURV1 = درآمدِ CONFIRMED/ATTRIBUTED ÷ هزینه‌ی محاسبه × 1.2` | `_ops/budget/budgets.yaml` + ledger | < ۱ برای N اپوک ⇒ بررسیِ انقراض (فقط انسانی، INV-10) | [FACT-0717: nbb_cp/fitness.py] |
| **سه‌قلبی (clock coherence)** | انسجامِ زمانیِ سه منبعِ ساعت | `drift = maxᵢⱼ |tᵢ − tⱼ|` روی (heart, cortex, daemon) | `ORGANISM-STATE.chrono.hlc` + daemon | > ۲۵۰ms ⇒ هشدارِ عصبی [hypothesis] | [hypothesis] |
| **درد (nociceptor)** | سیگنالِ محافظتیِ ترکیبی | `pain = w₁·anomaly + w₂·σ_cancer + w₃·budget_pressure` | `_ops/neural/nociceptor.py` + `ORGANISM-STATE.pressure` | pain > setpoint ⇒ protective redirect | [FACT: nociceptor.py موجود؛ فرمول [inferred]] |
| **متابولیسم (بودجه)** | فشارِ هزینه نسبت به سقف | `spend_velocity = d(spend)/dt` · `remaining = 30 − month.aud` | `ORGANISM-STATE.month` (امروز: AU$0.0319) | hard-cap AU$30 (ساختاری، INV-1) | [FACT: state زنده] |
| **اشتعال (ignition/WTA)** | حاشیه‌ی برنده در رقابتِ جهانیِ workspace | `margin = score(top1) − score(top2)` + پهنای broadcast | `_ops/cortex/` ignition logs | margin≈۰ ⇒ دودلی/تصمیمِ ضعیف [hypothesis] | [FACT: ignition موجود؛ metric [hypothesis]] |
| **خواب‌زمستانی (dormancy)** | درستیِ مرگِ امن | `T_kill→DORMANT` + شمارِ گذارها | heart FSM + events.jsonl | kill→DORMANT در هر state، در زمانِ کران‌دار (chaos test) | [FACT: Heart Design v1 §۵] |

## قواعد
1. هر کمیتِ جدید باید همین‌جا ثبت شود پیش از استفاده (no silent metric).
2. آستانه‌ها [hypothesis]‌اند تا وقتی روی داده‌ی واقعی کالیبره شوند — اولین کالیبراسیون با smallest_test و ثبتِ نتیجه (حتی ابطال → موزه‌ی فرضیه‌ها).
3. هیچ متریک self-reported بدونِ ناظرِ بیرونی معتبر نیست (INV-8).

## نام‌های برخوردی (۲۰۲۶-۰۸-۰۵)

> این جدول برای **کمیت** نیست — برای وقتی که یک اسمِ استعاره‌ای بیش از یک
> «چیزِ واقعی» را صدا می‌زند و اشتباه‌گرفتنشان یک تشخیصِ غلط ساخته (نقشهٔ
> [[../07 - Knowledge/شناخت-اختاپوس/12-BRAIN-HEART-CONTROL-PANEL-MAP-2026-08-05|12-BRAIN-HEART-MAP]]، همان شب یک بار واقعاً افتاد: G3/G4).

| نام | مصداقِ ۱ | مصداقِ ۲ | چطور اشتباه گرفته شد |
|---|---|---|---|
| **doctor** | جریانِ تلگرامِ `hold_policy`/`surface_policy` (کارتِ ارسالی) | زیرسیستمِ `cortex/stress.py::_doctor_stress()` — تعدادِ RFC ِ معطل، `pending/6.0` | ۱۲-BRAIN-HEART-MAP اول فرض کرد `in_fear:["doctor"]` یعنی «کارتِ تلگرامِ doctor نرسیده»؛ در واقع یعنی «RFC ِ doctor معطل مانده» — دو ماژولِ کاملاً بی‌ربط |
| **heart** (به‌عنوانِ داده) | چهار تولیدکنندهٔ ریتم: `cardiac.py`، `heart/control_law.py`، `chrono_rhythm/rhythm.py`، پیس‌میکرِ chrono — آشتی‌شده در `heart/pulse_arbiter.py` | `cortex/stress.py::_heart_stress()` که در واقع `replication-latest.json.sigma` (نسبتِ تکثیر) را می‌خواند، نه `heart/` را | کلیدِ خودِ کد `sigma_is_replication_ratio: True` دارد — مستندِ خودشناسی است، ولی نامش هنوز «heart» گمراه‌کننده است |
| **brain** | پروسهٔ `cortex/cortex.py` (پورتِ ۸۷۷۲، زنده و تیک‌زن) | سیستمِ ۴D (`4d_system/brain/daemon.py` + `self_evolved/`) که تا ۲۰۲۶-۰۸-۰۵ تنها منبعِ `/api/ops/brain` بود | کنترل‌پنل ماه‌ها «مغز» را نشان می‌داد بی‌آنکه بداند کدام مغز — رفعِ G1 حالا هر دو را جدا نشان می‌دهد |
| **brain** (بازهم) | `cockpit_brain.py` — اسکجول‌تسکِ ۵دقیقه‌ای، ناظرِ کاکپیت | `brain_worker.py`/`brain_core.py` — پیش‌نویسِ propose-only، هرگز سیم‌کشی نشده (صفر صداکنندهٔ تولیدی) | نامِ فایل تنها سرنخ نیست؛ باید `OCTOPUS-flags.cmd` و صداکننده‌های واقعی چک شود، نه فقط `grep brain` |
