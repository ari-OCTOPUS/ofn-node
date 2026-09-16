# RUNBOOK — پین روزانهٔ FX از RBA (F11.1) — بعد از انتشار ~۱۶:۳۰ local

ایجاد: 2026-09-08 · لِین FAULT-LLMLEARN-20260908 · مجوز: رویهٔ اجراشدهٔ رأی مالک FX-1
(OWNER-APPROVALS-2026-09-07.md) — «ایجنت: نوشتنِ fx_record تازه با receipt_id +
owner_pin_id … + یک فراخوانی آزمایشی paid با رسید. سقفِ روزانهٔ AU$30 دست‌نخورده.»

## چرا روزانه؟
گارد F18 (`cost_receipt.fx_pinned_fresh`) پین را ۲۴ ساعت از `fx_timestamp_utc`
می‌سنجه؛ سریِ RBA F11.1 هر روزِ کاری ~۱۶:۳۰ local منتشر می‌شود. Anchorِ درست =
**۰۶:۰۰Z روزِ داده** (نرخِ ۴بعدازظهر AEST). با این anchor، پینِ به‌موقعِ هر روز
تا فردای آن ساعت تازه می‌ماند و شکافِ روزانه حداکثر ~۳۰ دقیقه (۱۶:۰۰→۱۶:۳۰) است.
**هیچ‌وقت تاریخ را جعل نکن؛ اگر ردیفِ امروز هنوز منتشر نشده، صبر کن.**
 («No auto-refresh» — این ران‌بوکِ دستی است، نه خودکار.)

## مراحل (۵ دقیقه)
1. **دریافت**: `curl -sS -m 30 -A "Mozilla/5.0" "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv" -o _ops/state/wedge/rba-f111-fetch-<YYYYMMDD>.csv`
2. **چک**: آخرین ردیفِ غیرخالی باید تاریخِ امروز (یا آخرین روزِ کاری) باشد؛ ستونِ دوم = AUD/USD (مثل 0.7209). اگر تاریخ قدیمی است → انتشار نشده؛ بعداً دوباره.
3. **محاسبه**: `fx_usd_to_aud = round(1/AUD_USD, 5)` (معکوس؛ مثال: 1/0.7209 = 1.38716).
4. **بکاپ**: `cp _ops/cortex/pricing_pinned.json _ops/cortex/pricing_pinned.json.bak-fxpin-<YYYYMMDD>`
5. **نوشتن**: در `pricing_pinned.json` فقط این‌ها را عوض کن:
   - `_comment` (توضیحِ کوتاه + تاریخ)
   - `fx_usd_to_aud`
   - `fx_record`: `fx_source_id`, `fx_timestamp_utc` = **«<روزِ داده>T06:00:00Z»**, `fx_rate_usd_to_aud`, `FX_SOURCE_VALUE`, `owner_pin_id` = `FX-PIN-<YYYYMMDD>-01`, `receipt_id` = sha256 فایلِ CSV خام، حرفِ اول تا ۱۶ کاراکتر.
   فایلِ CSVِ مرحلهٔ ۱ همان شاهد است؛ نگهش دار.
6. **سانس**: در شل `OCTOPUS_PAID_COGNITION=1` + `OCTOPUS_RUN_ID=R-fxpin-verify-<date>` + لودِ `.env`
   (الگوی مستند در OWNER-APPROVALS؛ فقط شلِ ایجنت، نه دیمن) و یک فراخوانی:
   `model_router.ask("deep", "Answer with the single word OPERATIONAL if you can read this.", system="Reply in English, one word.", max_tokens=256, tier="primary")`
   مدل thinking است → `max_tokens ≥ 200` الزامی. رسید = ردیفِ ok در
   `paid-calls.jsonl` + trace در `cost-receipts.jsonl`.
7. **ثبت**: یک receipt JSON در لِینِ خودت + خط در LANE-REPORT.

## خطاها
- پین ننوشتی و ساعت ۱۶:۰۰ گذشت → مسیر paid بسته می‌شود (fail-closed، بی‌خطر؛
  ارگانیسم روی مغز محلی می‌ماند). فردا جبران کن؛ تاریخِ عقب ننویس.
- sha ردیف‌ها mismatch → CSV ناقص؛ دوباره بگیر.
