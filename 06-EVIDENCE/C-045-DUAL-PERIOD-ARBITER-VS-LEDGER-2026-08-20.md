# C-045 — Life currency consumes previous-tick judge period without provenance

contradiction_id: C-045
status: OPEN
canonical_verdict: ONE_TICK_TEMPORAL_SKEW
source_relation: SAME_PIPELINE_DIFFERENT_SNAPSHOT
owner: CORE
related: C-043 SUSPECTED_VOID · C-044 · C-046
created: 2026-08-20T12:36+10:00
updated: 2026-08-20T12:48+10:00
implementation: diagnose only
path_frozen: این فایل همان C-045 است (بین C-044 و C-046). نام مسیر حفظ شد تا لینک‌ها نشکند.

عنوان کهنه «period دوگانه» = ERRATA. مسئله دو pipeline جدا نیست؛ حساب‌داری period داورِ **تیک قبل** را بدون ثبت `period_s` در JSON خرج می‌کند.

## ادعا

برای یک beat، `life_currency` و داور باید یک `effective_period_s` و یک رنگ مصرف کنند.

## دو مقدار (beat 42784)

- value_a (داور همین beat): period **113.65** · AMBER · `_ops/state/pulse/arbiter-shadow.jsonl` ts 11:52:18
- value_b (حساب‌داری، بازسازی): period ∈ **[112.32, 113.04)** · `hard_cap=0.078` نقل‌شده؛ منطبق با period **112.76** از beat **42780**

منبع کد: `_read_color` از `ORGANISM-STATE.json` **قبل از** `persist` همین حلقه (`organism.py:558–565` سپس `:609–623`).

## likely

value_b = تیک قبلی؛ value_a = تیک فعلی. C-043 به عنوان rounding **SUSPECTED_VOID**.

حداقل فیکس (اجرا نشد): tick ارز بعد از persist + پاس دادن period/color همین snapshot.

## حکم

OPEN · **ONE_TICK_TEMPORAL_SKEW** · `SAME_PIPELINE_DIFFERENT_SNAPSHOT`.
ERRATA: برچسب `DIFFERENT_SOURCE` گمراه‌کننده بود (حفظ شد، منسوخ).
فیکس نشد.
