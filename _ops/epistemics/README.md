# `_ops/epistemics` — off-loop scaffold (relative, FUNCTIONAL self/whole awareness)

**این چیست:** لایهٔ «آگاهی» به‌شکلِ read-only — پنج سیگنالِ کارکردی دربارهٔ *خودِ* سیستم
(`self_reference`/SOG) و *کلِ* سیستم (`levels`/L_G، `channel`/DPI، `identifiability`/N_eff)،
به‌علاوهٔ یک گزارهٔ شرطیِ `method`. این همان معنای **functional/relative** از «آگاهی» است
که توافق کردیم — **نه** phenomenal consciousness، و هیچ متریکِ این‌جا آن را اثبات یا ادعا نمی‌کند.

## امنیت به‌صورتِ ساختاری (safety by construction)
- **read-only.** هرگز روی ledgerِ مالی نمی‌نویسد. روی استریمِ hash-chainِ مستقلِ خودش می‌نویسد:
  `_ops/epistemics/epi-ledger.jsonl`.
- **off-loop.** `run_offloop.py` مستقل است و `organism.py` را **import نمی‌کند**.
- هر متریک `confidence` + `sample_size` دارد؛ تا رسیدن به دادهٔ کافی `authoritative=False`.
  تخمینِ MI/perplexity روی نمونهٔ کم گمراه‌کننده است — flagها همین را می‌گویند.
- **idempotency** در `emit.py` (dedup_key) تا اجرای دوباره رکوردِ تکراری ننویسد.

## ❌ هرگز (تا زمانِ درست)
> ⚠️ **به‌روزرسانی 2026-07-17 (truth-map P12):** بندِ «هنوز وصل نکن» تاریخی است —
> مالک در unlockِ 2026-07-11 فلگ را روشن کرد و در runtime `wire_epistemics=true` است
> (وصل از `wiring.epistemics_beat`، هر ۷۲۰ beat، advisory-only). بندِ «به اعدادش
> اعتماد نکن» همچنان معتبر است: upstreamها (reconcile/fitness) هنوز خاموش/خالی‌اند.
- **هنوز به loop وصلش نکن.** وایرینگ = **Phase 5**، پشتِ `OCTOPUS_WIRE_EPISTEMICS`
  (پیش‌فرض off)، و فقط **بعد از Phase 1–3**.
- **به اعدادش اعتماد نکن** تا Phase 1–3 داده‌های upstream را پر کنند (outbox، fitness،
  telemetry، reconcile). الان از منابعِ خالی/شکسته می‌خواند → اعداد بی‌معنا.

## کارِ GLM قبل از این‌که این مفید شود
1. هر مسیرِ `readers.py` را با repoی زنده verify/اصلاح کن (`[CLAIM]`ها).
2. فیلدهای دادهٔ واقعی را به ورودیِ متریک‌ها map کن (TODOها در `run_offloop.py`).
3. `MIN_SAMPLES` در `contracts.py` را کالیبره کن.
4. تا Phase 5 off-loop نگهش دار؛ `organism.py`/`wiring.py` را موازیِ کارِ فعلی‌ات ویرایش نکن
   (این scaffold greenfield است، پس تصادمی ندارد).
