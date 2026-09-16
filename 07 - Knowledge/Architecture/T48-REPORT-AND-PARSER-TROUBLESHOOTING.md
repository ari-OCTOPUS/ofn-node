---
type: knowledge
status: active
tags: [t48, parser, troubleshooting, yaml, fx-pin-receipt, report-structure]
created: 2026-08-20
updated: 2026-08-20
created_by: agent B (ZCode) — درخواست پژوهشی مالک 2026-08-20
implements: research/event_time_probe/{rba_parser,pipeline}.py · _ops/state/cortex/fx-pin-receipts.jsonl
---

# سند ۱ — ساختار گزارش‌های T48، تاکسونومی خطاهای Parser، و راهنمای عیب‌یابی YAML رسید پین

## بخش الف — ساختار گزارش فنی T48 (به‌مثابه پروتکل)

گزارش T48 یک زنجیرهٔ هفت‌حلقه‌ای است که هر حلقه باید شاهد مستقل خودش را داشته
باشد و خروجی حلقهٔ قبل را «عدد گرفته» ورودی بگیرد، نه ادعا را:

```text
RBA raw response → Parser result → FX freshness verdict → Pin receipt
→ Signed probe → Event-time record → Bitemporal gate
```

### فیلدهای استاندارد گزارش (قرارداد)

```yaml
report_id / run_id / agent_id / session_id     # هویت و بازتولیدپذیری
window:    {started_at, ended_at, timezone: Australia/Sydney, active_duration_seconds}
code:      {git_commit, parser_path, parser_sha256, schema_version}
samples:   {total_rows, legacy_rows, schema_v2_rows, provider_request_ts_rows,
            provider_server_created_rows, telegram_rows, duplicate_event_ids,
            missing_occurred_at, missing_recorded_at, clock_skew_suspected}
provider:  {n, median/stdev/min/max_delay_ms, timestamp_precision: 1s, clock_source}
telegram:  {n, median/stdev/min/max_delay_ms, timestamp_precision: 1s, clock_source: telegram_server}
bitemporal:{future_use_count, strict_query_failures, naive_future_use_count,
            read_paths_checked, decision_time_bypasses}
```

**قاعدهٔ طلایی ساختاری:** سه چیز هرگز یکی نمی‌شوند — `raw source` ≠ `parser
result` ≠ `spine record`. هر تحلیلی که این سه را ادغام کند، شاهد را با تفسیر
جایگزین می‌کند و در ممیزی قابل دفاع نیست.

## بخش ب — تاکسونومی علل رایج خطاهای Parser (با مصداق واقعی)

### ب-۱ خطاهای ساختاری ورودی

| علت | نشانه | تشخیص | درمان |
|---|---|---|---|
| BOM (U+FEFF) در ابتدای فایل | سطر اول خالی یا کلید عجیب | decode با `utf-8-sig` | تحمل + ثبت raw-hash قبل از decode |
| سطرهای metadata قبل از header | `KeyError` روی نام ستون | یافتن سطرها با برچسب، نه شماره | جستجوی برچسب‌محور (`Title`/`Units`/`Series ID`) |
| **سطرهای خالی پشت‌سرهم** | **شیفت ایندکس‌های ثابت** (مصداق امروز: `rows[9]` به‌جای Publication-date به Series-ID خورد) | تست با fixture دارای سطر خالی | هرگز شماره‌خط؛ همیشه برچسب یا جستجو |
| سطر خالی انتهایی | انتخاب «آخرین سطر» خالی | — | انتخاب با (تاریخ + Series ID)، نه `[-1]` |
| CRLF/فاصله‌های آویزان | مقدار parse نشدنی | strip قبل از تبدیل | نرمال‌سازی نقطهٔ ورود |

### ب-۲ خطاهای انتخاب و معنا

| علت | نشانه | درمان |
|---|---|---|
| انتخاب آخرین سطر به‌جای تاریخ هدف | نرخ دیروز/هفتهٔ قبل | پرس‌وجوی تاریخِ سیدنیِ موردنظر |
| سری غلط (ستون همسایه) | نرخ CNY/TWI به‌جای USD | اعتبارسنجی Series ID (`FXRUSD`) + Title + Units با هم |
| **قرارداد نقل وارونه** (USD/AUD به‌جای AUD/USD) | نرخ ≈ معکوسِ عادت (۱.۴ به‌جای ۰.۷) | قرارداد را از metadata بخوان و در رسید ثبت کن + باند معقول |
| مقدار NA/خالی در آخرین ردیف | `ValueError` یا صفر | BLOCK صریح، نه صفرگرفتن |
| تاریخِ دودار | دو مقدار متفاوت | BLOCK (ابهام = رد) |
| تاریخ آینده (نسبت به سیدنیِ الان) | دادهٔ ناممکن | BLOCK |
| تاریخ بدون timezone با UTC تفسیر شود | freshness غلط | timezone مبدأ (سیدنی) در قرارداد |

### ب-۳ خطاهای حمل/کش

| علت | نشانه | درمان |
|---|---|---|
| HTTP 200 ≠ دادهٔ تازه | تاریخ داخل dataset قدیمی | بررسی تاریخ داخل داده، جدا از status |
| HTML کش‌شده/کهنه | اختلاف HTML و CSV | `FX_SOURCE_CONFLICT` → BLOCK (منبع «مطلوب‌تر» انتخاب نشود) |
| بی‌توجهی به ETag/Last-Modified | fetchهای تکراری تشخیص‌دادنی نیستند | ثبت در بلوک source رسید |
| ** خرابی پایپ باینری** (مصداق امروز: ‏PS 5.۱ بین openssl↔sha256sum) | هش غلط/ناپایدار | فایل موقت + هش فایلی، نه پایپ |

### ب-۴ سلامت بازپخش

- raw bytes **قبل از** parse هش شود؛ parser جدید روی همان artifact قابل replay
  باشد (تست: دو parse همان bytes → همان raw_sha256).
- `parser_sha256` و `git_commit` در رسید؛ تغییر parser بدون تغییر ورودی باید
  در diff دیده شود.

## بخش ج — راهنمای عیب‌یابی YAML مکانیزم ثبت رسید پین (fx-pin-receipt.v2)

ساختار مرجع: `_ops/state/cortex/fx-pin-receipts.jsonl` (append-only؛ هر خط یک
رسید). بلوک‌ها: `authority · source · parser · observation · freshness · lease ·
previous_pin · result`.

### جدول فیلدها + خطای رایج هر فیلد

| فیلد/بلوک | نوع | خطای رایج | عیب‌یابی |
|---|---|---|---|
| `schema` | str ثابت | نسخه‌گذاری فراموش شده | تغییر ساختار ⇒ نسخهٔ جدید (`v3`)؛ خواننده بر اساس schema شاخه بزند |
| `receipt_id` | hash16 | ساخته‌شده از تاریخ (دو fetch همان روز یک رسید می‌شوند) | از `sha256(raw_sha|date|rate)` — fetchهای متفاوت، رسیدهای متفاوت |
| `pin_id` | str | تداخل با receipt_id | pin_id از تاریخ؛ receipt_id از محتوا |
| `authority.payload_sha256` | hex | هش متن YAML به‌جای فایل باینری payload | هش همیشه روی bytes فایل |
| `authority.signature_verified` | bool | **YAML 1.1: ‏`yes/no/on/off` هم bool می‌شوند** | فقط `true/false` بنویس؛ ولیدیتور را روی مقادیر مجاز قفل کن |
| `source.etag/last_modified` | str? | سرور نمی‌دهد و فیلد جاافتاده | تهی مجاز («»)؛ غیبت کلید ≠ تهی — همیشه کلید را بنویس |
| `source.raw_sha256` | hex | هشِ parseشده | هش raw پیش از هر decode |
| `parser.selected_series_id` | enum | ستون درست، سری غلط | Title+Units+SeriesID سه‌گانه اعتبارسنجی |
| `observation.quote_convention` | enum | مقدار آزاد (`"usd"`، `"USD"`، `"per aud"`) | enum بسته: `USD_per_AUD` |
| `observation.rate` | float | **نقل‌قولی‌نشدن و تفسیر علمی** (`0.70` → ‏`0.7` مشکلی نیست؛ `1,4` یا `1_4`؟) | اعشار نقطه‌ای؛ ویرگول = خطا؛ `_` مجاز YAML ولی ممنوع کن |
| `freshness.verdict` | enum | مقادیر خودساخته (`ok`,`fine`) | enum بسته: `FRESH · BLOCK_FX_STALE · …` |
| `freshness.required_date` | date | فرمت‌های混合 (ISO و DD-Mon) | یک قالب در کل سیستم + timezone صریح |
| `lease.lease_id` | uuid | رسید بدون lease (نوشتن آزاد) | نبود lease = رسید نامعتبر؛ fail-closed |
| `previous_pin` | ref | حذف بعد از overwrite | append-only: تاریخ پاک نمی‌شود |

### تله‌های عمومی YAML در رسیدها

1. **Tab ممنوع** — indent فقط فاصله؛ tab = parse error.
2. **Boolهای YAML 1.1** — `yes/no/on/off/off` به‌عنوان bool؛ در رسید فقط `true/false`.
3. **تاریخ بدون نقل‌قول** — `2026-08-20` در YAML به شیء تاریخ تبدیل می‌شود؛
   اگر رشته می‌خواهی نقل‌قول بزن و قالب را ولیدیت کن.
4. **کلید تکراری** — YAML آخری را برمی‌دارد و سکوت می‌کند؛ ولیدیتور
   duplicate-key بگذار.
5. **Null پنهان** — `key:` (بدون مقدار) ≠ `key: ""`؛ برای فیلدهای اختیاری
   تفکیک معنا دار است («سرور نداد» ≠ «نپرسیدیم»).
6. **BOM در YAML** — بعضی parserها سطر اول را خراب می‌کنند؛ utf-8 ساده.
7. **مقیاس اعداد** — `rate: 0.7080` و `rate_usd_to_aud: 1.4124` در یک رسید =
   واحدهای مختلف؛ نام فیلد باید واحد را حمل کند (همین‌طور کردیم).
8. **secret در YAML** — هیچ‌گاه؛ رسید شاهد عمومی است.

### چک‌لیست عیب‌یابی سریع (وقتی رسید رد شد)

```text
۱) receipt_id بازتولید کن — با raw_sha/date/rate می‌خواند؟
۲) raw_sha256 فایل فعلی را بگیر — با source.raw_sha256 یکی است؟ (نه ⇒ منبع عوض شده، رسید مال artifact دیگری است)
۳) authority.signature_verified واقعاً بعد از verify نوشته شده یا پیش‌دستی؟
۴) freshness.observed_date با required_date (سیدنی) مقایسه — نه UTC.
۵) lease در بازهٔ زمانی freshness فعال بود؟
۶) enumها همه در فهرست بسته؟
۷) جستجوی duplicate-key در کل رکورد.
```
