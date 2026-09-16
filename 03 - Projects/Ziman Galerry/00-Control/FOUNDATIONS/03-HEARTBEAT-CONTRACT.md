# ۰۳ — قراردادِ ضربان (heartbeat contract)

تعریفِ دقیقِ اینکه هر ضربانِ اُرگانیسم، پای زیمان چه محاسبه می‌کند و چه برمی‌گرداند — طوری
که **با فلگِ خاموش، رفتار بایت‌به‌بایت مثلِ امروز** بماند (صفر regression).

## مسیرِ ضربان (امروز، واقعی)
هر tickِ اُرگانیسم:
```
wiring.ziman_beat(leg, beat, doctor)      # پشتِ OCTOPUS_WIRE_ZIMAN
  ├─ اول: اگر STOP_ORGANISM یا opslib.halted() → None  (کیل‌سوییچِ مطلق)
  └─ leg.tick() → { ok, status, proposals_delta, proposals_total }
```
> نکتهٔ گراند: در `wiring.py` دو تعریفِ `ziman_beat` هست؛ تعریفِ **فعال** ۳-آرگومانی است
> (`leg, beat, doctor`) که اول STOP/HALT را چک می‌کند. تعریفِ ۲-آرگومانیِ قدیمی مرده است و
> در فاز P1 باید حذف شود (رجوع `08-CONFLICTS-AND-GAPS.md`).

## افزودهٔ طراحی: بلوکِ `ziman.beat.v1`
با فلگِ `OCTOPUS_WIRE_ZIMAN_MATRIX` (پیش‌فرض خاموش)، `tick()` **علاوه‌بر** کلیدهای امروز
(دست‌نخورده)، یک بلوک اضافه می‌کند:
```
ziman.beat.v1 = {
  schema: "ziman.beat.v1", beat, ts,
  self_model_digest: <ziman_self.v1 فشرده — نگاه کن 01-SELF-MODEL>,
  steering: {focus, paused, boosts[], mutes[], source, banner:"focus=X paused=N guardrails=M"},
  candidates: [ candidate.v1 با signals{goal_fit,impact,readiness,novelty,cost,risk_penalty},
                priority, reasons[], truth_flags[], vetoed_by|null, rank ],
  funnel: {cold, warm, proposed, won, proposals_this_beat},
  top: {kind, priority, reasons[], one_line_fa},
  surfaced: bool,
  emitted_proposals: [ <= ZIMAN_MAX_PROPOSALS_PER_BEAT عدد ZIM-DEC ref، dedup با content-hash ],
  damping: {shadow_on, protective_mode, pain_level, budget_ok},
  market: {top_idea|null, freshness_age_days},   # کش‌شده؛ فقط هر N ضربان بازمحاسبه
  propose_only: true, outward_execution: false
}
```

## قواعدِ سختِ قرارداد
1. **STOP/HALT اول**: هر مسیر قبل از هر کاری کیل‌سوییچ را چک می‌کند؛ بعدش هیچ.
2. **فلگ‌خاموش = هم‌ارزِ بایتی**: اگر `OCTOPUS_WIRE_ZIMAN_MATRIX` خاموش باشد، `tick()` دقیقاً
   همان چهار کلیدِ امروز را می‌دهد و بس. یک تست باید این هم‌ارزی را تضمین کند.
3. **fail-soft**: هر استثنا در ساختِ بلوکِ ماتریس → بلوک حذف می‌شود، پا نمی‌شکند، اُرگانیسم
   نمی‌میرد (اصلِ «یک limb نباید ارگانیسم را بکشد»).
4. **تقریباً رایگان**: مدلِ خود و فایل‌های هدایت با mtime-cache خوانده می‌شوند؛ هوشِ بازار فقط
   هر `CHRONO_ZIMAN_MARKET_EVERY_N_BEATS` بازمحاسبه می‌شود، نه هر ضربان.
5. **صفر خروجیِ بیرونی**: این مسیر هیچ ارسال/انتشار/خرج ندارد؛ فقط محاسبه و نوشتنِ state.

## کجا نوشته می‌شود
`wiring` بلوک را در `state/ORGANISM-STATE.ziman` می‌نویسد (کلیدِ موجود، افزایشی). دایجستِ
تلگرام (`leg.telegram_digest()` و پلِ غنیِ control-brain پشتِ `OCTOPUS_WIRE_ZIMAN_RICH`)
از همین بلوک، `top` و `banner` را نشان می‌دهد. `/status` هم همین را ترجمه می‌کند.

## آهنگ (cadence)
هر `CHRONO_ZIMAN_EVERY_N_BEATS` ضربان یک‌بار (پیش‌فرضِ محافظه‌کار — مثلاً روزانه/چند‌ساعته،
عددش در env). زیمان کارِ inventory/marketing intelligence است، نه intakeِ لحظه‌ایِ پول؛ پس
لازم نیست هر ثانیه بتپد.

## چرا این «شناختِ خود همگام با ضربان» است
هر ضربان: مدلِ خود بازساخته می‌شود (کجای راهم) → نیّتِ مالک خوانده می‌شود (چه می‌خواهد) →
ماتریس امتیاز می‌دهد (بعدی چیست) → بهترین به مالک می‌رسد. این دقیقاً «self-knowledge synced
to heartbeat, entering the calculation matrix» است — عملی و قابلِ‌ردیابی.
