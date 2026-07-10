---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, control-law, simulation]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/M-HEART-SOG-Pacemaker-BUILD-PROMPT]]"
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P4 — control-law قلب (velocity-first) + شبیه‌سازیِ closed-loop

> gate خروج: **SIM-PASS** (Gate-B M-HEART): همهٔ گیت‌های closed-loop سبز ∧ loop-gain `G<1` ∧ (`e_shadow_locked` ∨ excluded صادقانه) ∧ I_pred بیرونِ هر authorization. پیش‌نیاز: HH-P0..P3.

## مأموریت

بازنگریِ control-lawِ M-HEART برای طراحیِ hybrid: **period از velocity ظاهر می‌شود؛ SOG فقط باندِ هدف می‌دهد**. سپس اثباتِ closed-loop در sim ($0، bounded، بدونِ pin روی ریل‌ها).

## control-law (Living-Beat بازنگری‌شده — قانونِ نهایی)

```text
sig        = health(σ از replication-latest؛ missing/stale/σ>target → period=MAX، fail-closed)
             + چکِ taint (ریویو): اجزای درونی (spawn_approved/parents) موجود و سازگار
             (σ=approved/parents) و producer∉{doctor,heart}؛ هر نقض → period=MAX.
             ⚠ همهٔ verdictهای σ **ترمینال‌اند (return فوری)** — clampِ پایین هرگز آنها را بازنویسی نمی‌کند.
Δ_live     = producers.delta_self_live()      # هرگز 0.122520 منجمد؛ provenance-checked
ceil_live  = producers.delta_self_ceiling()   # از primitiveها
if Δ_live > ceil_live·(1+DRIFT_EPS): drift-flag + period=MAX + STOP-advice   # ضدِ جعلِ شتاب
g_learn    = clamp(Δ_live/ceil_live, 0, 1)                    # یادگیریِ فعال → باندِ هدف بالاتر
band       = setpoint.viable_band (Doctor/SOG) شیفت‌یافته با g_learn (سقفِ شیفت: +50%)
err        = (velocity_now − band_mid)/max(band_width, ε)     # خطای نرمالِ throughput
period_raw = BASE_PERIOD_S · exp(k_p · err)                   # زیرِ باند → تندتر؛ بالای باند → کندتر
period_raw ·= cpi_guard(cpi)      ≥1.0                        # تورم → شتاب ممنوع (فقط کُندی)
period_raw ·= budget_pressure(BeatBudget.remaining) ≥1.0      # بودجهٔ ضربان → کُندی monotone
period     = clamp(period_raw, max(BIO_RESTING_FLOOR_S, floor_sigma), BIO_MAX_PERIOD_S)
w_shadow: فقط اگر e_shadow_locked → جملهٔ استراحتِ k_slow·g_rest واردِ توان می‌شود؛ وگرنه ۰
خروجی: HeartSignal(beat_seq, period_s, sigma_now, baro_factor) + HeartTelemetry — هرگز spend
```

ثابت‌ها: `BASE=60, FLOOR=30, MAX=900` (از cardiac.py) · `k_p≈0.7, k_slow≈0.7, DRIFT_EPS≈0.02` — **مقدارِ نهایی را sim تعیین می‌کند نه حدس**. σ فقط کُند/متوقف می‌کند، هرگز شتاب (تقارنِ accelerator/brake: هر دو external/read-only).

## تحویل‌دادنی‌ها

1. **`_ops/heart/control_law.py`** — `heart_step(inputs: dict, setpoint: HeartParams) → (HeartSignal, telemetry: dict)`؛ pure function (بدونِ I/O؛ ورودی‌ها تزریق می‌شوند) + `gather_inputs()` جدا (I/O از state-fileها، read-only، fail-closed به MAX).
2. **`_ops/heart/sim_heart.py`** — plantِ closed-loop: `activity(t+1)=f(period)` (تندتر → پردازشِ بیشتر → velocity↑ → err↓ → period آرام) + سناریوها:
   - S1 backlog-burst: همگرایی به باند بدونِ نوسانِ واگرا؛ S2 quiet: میل به کُندی/استراحت (گاردِ بی‌ثمری — نه pin روی کف)؛ S3 noisy-CPI: میانگینِ period در سناریوی CPI-بالا ≥ سناریوی CPI-صفر (شتابِ تورمی ممنوع)؛ S4 runaway (Δ_live جعلی > سقف): drift-flag + MAX؛ S5 σ>target + σ غایب/کهنه: ترمزِ MAX در همان گام؛ S6 budget-depleted: period↑ monotone؛ **S7 taint-canary** (σ بدونِ اجزا/ناسازگار/producer=doctor → MAX)؛ **S8 بازگشت به استراحت** بعد از خشک‌شدنِ burst؛ **S9 بهرهٔ حلقهٔ Δ** (لگِ `Δ→band→err→period→v→Δ` که ریویو حذفش را fake-green خواند — حساسیتِ عددیِ estimator × مشتق‌های زنجیره).
   - **loop-gain**: `G_total = G_velocity + G_delta < 1` — هر دو لگ عددی حولِ نقطهٔ کار؛ FAIL اگر `G_total≥1` یا period در steady-state روی ریلِ 30/900 pin شود (مگر سناریوی ترمز که MAX عمدی است). invarianceِ فرکانسِ تصمیم (نمونه‌گیریِ ساعت-ثابت) در تستِ producers پوشش داده می‌شود و در گزارش ارجاع می‌خورد.
   - گزارش → `_ops/state/sim/HEART-SIM-REPORT.json` (per-gate، un-collapsible، `sim_pass: true|false`) + `ledger_note("HEART_SIM", …)`.
3. **تست** (`_ops/tests/test_heart_control.py`): همهٔ سناریوها + گیت‌ها + ساختاری (control_law هیچ importی از organ_gate/money/allocate ندارد؛ هیچ literalِ anchor؛ خروجی هرگز فیلدِ spend/grant ندارد) + ثبت در run_all.

## خطوطِ قرمز

sim-first مطلق: این پرامپت هیچ‌چیزِ زنده وایر نمی‌کند · $0 · هیچ دستکاریِ chrono/HLC · fail-closed (هر ورودیِ غایب/کهنه → MAX) · گیتِ سبز بدونِ owner-ack برای exclusionها render نمی‌شود (`e_shadow_excluded:true` باید صریح در گزارش بیاید).
