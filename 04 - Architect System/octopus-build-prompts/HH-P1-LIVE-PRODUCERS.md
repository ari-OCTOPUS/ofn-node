---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, producers, velocity, gate0]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
  - "[[04 - Architect System/octopus-build-prompts/M-HEART-SOG-Pacemaker-BUILD-PROMPT]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P1 — producerهای زندهٔ Gate-0: velocity_meter · internal_cpi · delta_self_estimator

> gate خروج: **live-producers-exist** — سه سنجهٔ زنده، read-only، $0، با provenanceِ خارجی. بدونِ اینها «ضربانِ emergent» توهم است (نقدِ محوریِ M-HEART) و production برای همیشه بلاک می‌ماند.

## مأموریت

سه سنجهٔ زنده که «توان‌عبورِ واقعیِ شناخت» را از رویدادهای ثبت‌شده توسط بازیگرانِ دیگر (نه خودِ قلب) می‌خوانند. تقارنِ accelerator/brake: شتاب‌دهنده (Δ_self) همان انضباطِ provenance را می‌گیرد که ترمز (σ).

## منابعِ دادهٔ واقعی (نقشهٔ تأییدشدهٔ 2026-07-10)

- **CONFIRMED**: `opslib.genome_ledger()` رویدادهای `event_type=="MONEY_ATTRIBUTION"` با `payload.state∈{CONFIRMED,ATTRIBUTED}` و `rec["ts"]` (نویسندهٔ واقعی: `attribution.confirm` از reconcile-job). الان ۰ رویداد → fail-soft.
- **مصرفِ effect**: chrono.db (`opslib.STATE_DIR/chrono.db`) جدولِ `gated_effect status='settled'` **یا** NOTEهای `EFFECT_SETTLED` در ledger. الان chrono.db غایب → fail-soft.
- **چرخه‌های consolidation**: `_ops/neural/consolidation.json` — آرایهٔ JSON با `cycle:int` + `timestamp:float` (موجود و پُر — بهترین سیگنالِ فعلی).
- **beat**: جدولِ `heartbeat.wall_ts` در chrono.db (fail-soft).
- **الگوی معماری**: پکیجِ `_ops/epistemics/` (contracts.make_metric با `authoritative` گیت‌شده به sample_size؛ readers فقط‌خواندنیِ fail-soft؛ compute_all → state-file). ریاضیِ blind/informed از قبل موجود: `epistemics/metrics.py: self_reference(err_self, err_other)`.

## تحویل‌دادنی‌ها — `_ops/heart/producers.py` (stdlib-only)

1. **`velocity_meter(window_hours=24, now=None) → dict`** — throughput per hour از چهار منبعِ بالا: `{velocity_per_hr, components:{confirmed, effects, consolidation, beats}, sample_size, authoritative, provenance:[...], ts}`. وزن‌ها config-پذیر (پیش‌فرض مساوی روی مؤلفه‌های موجود)؛ منبعِ غایب → از شمارش حذف و در provenance علامت.
2. **`internal_cpi(window_hours=72) → dict`** — «تورمِ واسط» = نویز/بی‌ثباتیِ سیگنالِ ارزش: پراکندگیِ نرمالِ فاصله‌ها/مقادیرِ رویدادهای MONEY_ATTRIBUTION + نرخِ CONFLICT/unmatched از `reconcile-latest.json` + `suspect_zero_total` از `telemetry-latest.json` (نرمال به 0..1). `{cpi_0_1, components, sample_size, authoritative, ts}`. دادهٔ ناکافی → `cpi=None, authoritative=False` (نه صفرِ دروغ).
3. **`delta_self_estimator(min_samples=48) → dict`** — Δ_selfِ زنده به فرمِ SOG (**proxyِ صادق، نه P_closed کانونی — برچسبِ `estimator: proxy` در خروجی**): روی جریانِ append-onlyِ نمونه‌های velocity (`_ops/state/pulse/velocity-stream.jsonl`)، دو پیش‌بینِ یک‌گامی: **blind** (AR(1) فقط از خودِ سری) و **informed** (همان + **فقط کوواریت‌های برون‌زاد/بالادستی: confirmed، effects، hour**). `delta_self_live=½log(max(S_b,ε)/max(S,ε))` کف صفر؛ `ceiling_live=کرانِ اطلاعِ کل ½log(Var(v)/S)+حاشیه`؛ `authoritative=False` تا `sample_size≥min_samples` — **Gate-0 تا آن موقع صادقانه بسته می‌ماند.**
   - **دو گاردِ ضدِ سرطان (ریویوی خصمانه، CRITICAL):** (الف) کوواریت‌های پایین‌دستِ حلقهٔ کنترل (`beat`، `effects_pending`، `cycle`) **ممنوع** — وگرنه `Δ↑→ضربان↑→کوواریت→S↓→Δ↑` = reward-hacking؛ (ب) نمونه‌گیری به **ساعتِ ثابتِ دیواری** گره می‌خورد (`should_sample`، `HEART_SAMPLE_INTERVAL_S=3600`) نه به ضربان — decision-frequency invariance (ضربانِ تندتر نمونه/authoritativeِ زودتر نمی‌سازد).
   - محدودیتِ صادقانهٔ v1: استریم را خودِ همین ماژول append می‌کند (writer مستقل نیست) — هر نمونه شمارش‌های منبعش را حمل می‌کند تا از ledger قابلِ‌ممیزی باشد؛ جداسازیِ کاملِ writer (آینهٔ واقعیِ `selfmodel_state`) کارِ فازِ بعد و پیش‌شرطِ activationِ مالک.
4. **`append_velocity_sample(sample) / read_stream()`** — استریمِ append-only (opslib.append_jsonl) + **`compute_all(write=True) → dict`** که سه سنجه را جمع و با LockedJson در `_ops/state/pulse/heart-signals-latest.json` می‌نویسد.
5. **تست** `_ops/tests/test_heart_producers.py`: منابعِ غایب → fail-soft و authoritative=False؛ با fixtureی رویدادِ مصنوعی در mini-vault (harness) → شمارشِ درست؛ سریِ ساختگی که informed واقعاً کمک می‌کند → `delta_self_live>0`؛ سریِ i.i.d → `≈0`؛ ساختاری: هیچ importی از organ_gate/money_gate؛ هیچ متدِ نوشتن جز stream/state خودش.

## خطوطِ قرمز

read-only نسبت به همهٔ منابع (فقط stream و state-fileِ خودش را می‌نویسد — هرگز ledger پول، هرگز chrono.db) · هیچ self-grading: ورودی فقط رویدادهای ثبت‌شده توسط reconcile/effector-gate/consolidation/pacemaker · دادهٔ کم = authoritative:false صادقانه · $0 · stdlib-only · نامِ M-HEART برای producer (`selfmodel_state`) با `delta_self_estimator` این پکیج برآورده می‌شود (مستند کن).
