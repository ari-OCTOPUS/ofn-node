# مشتق‌سازی `daily_cap → beat_pool` + واحد — 2026-08-20

grade: MEASURED (فرمول + شاهد زنده) · paid re-run: none · FX fetch: none

## حکم واحد

`global.life_currency_daily_cap` در `budgets.yaml` واحدش **`life_credit` است، نه AUD.**

شاهد قراردادی: `_ops/owner-verdicts.yaml` → `wire_life_currency.note`:
«صفر مسیرِ پول؛ فقط حسابداریِ داخلیِ سهم‌ها.»

کد (پس از این جلسه): `_ops/heart/life_currency.py` ثابت‌های `UNIT="life_credit"` و `MONEY_PATH=False`؛ `credits_to_aud()` همیشه `RuntimeError("life_credit_is_not_aud")`.

## فرمول (کد، نه حدس)

از `allocate_beat` در `_ops/heart/life_currency.py`:

```
beats_per_day = 86400 / period_s
beat_share    = daily_cap / beats_per_day
hard_cap      = DAILY_BUDGET_HARD_CAP_X * beat_share   # 2.0
pool          = min(beat_share * abs(scale), hard_cap)  # GREEN scale=1 → pool = beat_share
beat_pool     = round(pool, 3)
reserve       = round(pool * 0.20, 3)
```

`DAILY_BUDGET_HARD_CAP_X=2` سقفِ یک ضربان است، **نه** دو برابر کردنِ استخرِ GREEN. روی GREEN، `pool = beat_share` و `hard_cap = 2 × beat_share` اعمال نمی‌شود مگر `scale > 1`.

`period_s` از `ORGANISM-STATE.json` → `arbiter.effective_period_s` می‌آید (آلوستاتیک)، نه ۳۰ ثانیهٔ ثابت.

## رسید عددی — شاهد زنده beat 42165

| فرض | period_s | daily_cap | beat_share | beat_pool گردشده | با شاهد زنده؟ |
|---|---:|---:|---:|---:|---|
| زنده (GATE-0 arbiter) | **107.69** | 1000 | 1.24641 | **1.246** | بله — `life-currency-latest.json` beat 42165 |
| فرض نادرست ۳۰ثانیه | 30 | 1000 | 0.34722 | 0.347 | خیر — این همان ۰.۳۴۷/۰.۲۷۸ مالک است |
| پس از rollback | 107.69 | **30** | 0.03739 | 0.037 | پیش‌بینی؛ تا ضربان بعدی |

۲۰٪ ذخیره روی GREEN از **استخرِ beat** کم می‌شود (`reserve = 0.20 × beat_pool`)، نه از سقف روزانه پیش از تقسیم. بنابراین `1.246 × 0.80 = 0.997` قابل‌توزیع است، نه `0.278`.

drift بعدی: فایل زنده پیش از rollback `beat_pool=1.335` بود → `period_s ≈ 115.3` (آلوستاتیک)، همان فرمول. زندهٔ 10:26+10: beat 42728 · `effective_period_s=115.72` · هنوز `daily_cap=1000` در JSON (cache پروسه).

## Dry-run استخر ۳۰ — پیش از ریاستارت (مالک 10:24)

نسبت نامی ۱۰۰۰/۳۰ = **۳۳.۳۳**. `round(..., 3)` نسبت نمایشی را کمی عوض می‌کند (۱.۲۴۶/۰.۰۳۷ ≈ ۳۳.۶۸).

`CALL_COST=10` ⇒ حتی در cap=1000 هم `calls=0` برای هر ۱۱ عضو (سهم ≈۰.۰۹۱ < ۱۰). کوچک‌شدن استخر **قطع تماس پولی از این ماژول** نیست — آن تماس‌ها مسیر `money_gate`اند و نباید گره بخورند. ریسک واقعی: granularity توکن (`round(..., 3)` = میلی‌واحد) و گرسنگی بی‌صدای AMBER.

کف داور: `CARDIAC_RESTING_FLOOR_S=30` · سقف `CARDIAC_MAX_PERIOD_S=900`. `allocate_beat` جداگانه `period=max(1.0, …)` دارد.

| cap | period_s | رنگ | beat_pool | reserve | n | tokens/عضو گردشده | calls | معنی |
|---|---:|---|---:|---:|---:|---:|---:|---|
| 1000 | 107.69 | GREEN | 1.246 | 0.249 | 11 | 0.091 | 0 | شاهد زنده beat 42165 |
| 30 | 30 (کف) | GREEN | 0.010 | 0.002 | 11 | **0.001** | 0 | روی کف granularity |
| 30 | 30 (کف) | **AMBER** | 0.005 | 0.001 | 11 | **0.000** | 0 | **starvation بی‌صدا** |
| 30 | 107.69 | GREEN | 0.037 | 0.007 | 11 | 0.003 | 0 | پیش‌بینی پس از ریاستارت اگر period همان بماند |
| 30 | 115.72 (زندهٔ اکنون) | GREEN | 0.040 | 0.008 | 11 | 0.003 | 0 | period فعلی داور |
| 30 | 900 (سقف) | GREEN | 0.312 | 0.062 | 11 | 0.023 | 0 | استخر بزرگ‌تر، هنوز calls=0 |
| 30 | 1.0 (min کد، داور نباید) | GREEN | 0.000 | 0.000 | 11 | 0.000 | 0 | گرد کردن به صفر کامل |

بدترین حالت **واقعی** داور: کف ۳۰ثانیه × AMBER → همهٔ اعضا ۰.۰۰۰. بدترین حالت **کد** اگر period=1 رد شود: استخر ۰.۰۰۰.

Σ توکن گردشده می‌تواند از distributable خام بیشتر شود (۱۱×۰.۰۰۱=۰.۰۱۱ در برابر ≈۰.۰۰۸ در کف GREEN) — ناوردی گردکردن، جدا از واحد پول.

تست: `_ops/tests/test_life_currency_units_safety.py` — **۱۰ passed** (شامل کف ۳۰s و AMBER صفر).

### Baseline ریاستارت (LIVE-2 pattern) — اجرا نشده

قبل از اولین رخداد پس از ریاستارت، این‌ها را با sha256 در `06-EVIDENCE/RESTART-BASELINE-CAP30-2026-08-20/` فریز کن (کپی، نه حذف):

- `_ops/state/pulse/life-currency-latest.json`
- `_ops/state/cardiac-budget.json`
- `_ops/state/ORGANISM-STATE.json` (beat / started / arbiter)
- `_ops/budget/budgets.yaml` (فقط برای اثبات `life_currency_daily_cap: 30.0`)
- PIDهای organism/cortex/center/gateway/live

پس از ریاستارت: اولین `life-currency-latest.json` باید `daily_cap=30` و `unit=life_credit` باشد (فیلد unit پس از reload ماژول). اگر هنوز ۱۰۰۰ بود → cache/yaml خوانده نشد؛ halt گزارش، نه ادامهٔ آزمایش.

ریاستارت این جلسه انجام نشد.

## Fisher جهت و توان VOID (ثبت مالک 10:24)

بازمحاسبهٔ مستقل مالک با اعداد این رسید یکی است. دو قفل اضافه:

1. Fisher ۵/۹ در برابر ۹/۹: دوطرفه **p=۰.۰۸۲۴** · یک‌طرفه **p=۰.۰۴۱۲**. یک‌طرفه از ۰.۰۵ عبور می‌کند. جهت باید **پیش از اجرا** pre-register شود. پیش‌ثبت K=9 سه‌بذر جهت را **دوطرفه** قفل کرد. آن مقایسهٔ تاریخی confirmatory نیست (ابزار/K متفاوت = VOID).
2. سایزینگ ablation **۱۵۶/۱۸۴** برای ۳۰ جفت معتبر با نرخ VOID است، نه برای آزمون نصف‌شدن VOID. توان ۸۰٪ / α=۰.۰۵ دوطرفه، دو نمونه: n≈**۳۰۷** در هر گروه برای ۱۳.۶٪→۶.۸٪؛ n≈**۱۳۳** برای افت به ۴٪؛ n≈**۱۰۲** برای ۳٪. پس ۱۸۴ اگر به‌عنوان n آزمون نرخ خوانده شود فقط اثر بزرگ (حدود ۴٪) را می‌گیرد، نه نصف‌شدن. ادعای «VOID بهبود یافت» همچنان underpowered.

## سقف‌های پولی روی دیسک (جدا از life_credit)

این‌ها **مسیر پول**اند و `life_currency` به آن‌ها import ندارد:

| سقف | مقدار | منبع | وضعیت |
|---|---|---|---|
| ماهانه | 30 AUD | `budgets.yaml` `global.cap_monthly` | روی دیسک |
| human_gate | 20 AUD | `money_gate.HUMAN_GATE_AUD_HARD` + yaml | روی دیسک |
| آزمایش روزانه | 30 AUD | label `EXPERIMENT_DAILY_CAP_AUD` (LEARNING-FIRST-BUDGET-EXPANSION-01؛ قبلی ۱۵) | لیبل |
| hard stop آزمایش | 24 AUD | label `EXPERIMENT_HARD_STOP_AUD` | لیبل |
| per-call | 1 AUD | label `PER_CALL_CAP_AUD` | لیبل |
| ablation پیشنهادی | 2 AUD کل آزمایش | `02-DECISIONS/PRE-REG-ABLATION-FOUR-ARM-2026-08-20.md` | **UNSIGNED** |

عدد «۲ AUD در روز» به‌عنوان سقف روزانهٔ زنده روی دیسک **پیدا نشد**. نزدیک‌ترین ۲ AUD = سقف پیشنهادی ablation (کل آزمایش، نه روزانه). اگر ۲ AUD/روز حکم مالک است، باید جدا به `money_gate` / لیبل برود — این جلسه سقف پولی را عوض نکرد (R7).

## چرا `1000` خطرناک بود حتی اگر واحد life_credit باشد

اگر **هرگز** سیم تبدیل `life_credit→AUD` ساخته شود، `1000` یعنی ۱۰۰۰ AUD/روز — نقض هر سقف بالا. تا وقتی مسیر تبدیل صفر است، عدد یک شمارندهٔ داخلی است. ایمنیِ ادعا‌شده = **نبودِ مسیر + fail-closed `credits_to_aud` + rollback مقدار**، نه ایمان به واحد.

## Rollback (مالک‌فرمان، این جلسه)

`budgets.yaml` `life_currency_daily_cap`: **1000.0 → 30.0**

صادق: ۳۰ همان فیxture آفلاین B1 نیست (`test_life_currency_b1.py` از ۴۲ / ۵۰۰ / ۱۰۰۰ استفاده می‌کند). ۳۰ فرمان مالک در پیام تناقض‌هاست.

۳۰ life_credit اگر ۱:۱ AUD خوانده شود هنوز از ۲ AUD/روز بیشتر است. rollback اندازه را کم می‌کند؛ **جلوگیری از خرج پولی** از مسیر تبدیل نیامده می‌آید.

`cardiac-budget.json` همچنان کلید `daily_cap` ندارد. `daily_pool()` اول cardiac را از دیسک می‌خواند، بعد `load_budgets()` که **در-پروسس cache** می‌شود (`opslib._budgets_cache`). پس rollback روی دیسک است؛ پروسهٔ زندهٔ organism تا ریاستارت (یا `load_budgets(force=True)`) همان ۱۰۰۰ را نگه می‌دارد. این جلسه ریاستارت نشد.

فیلد `unit` در JSON زنده تا بارگذاری مجدد ماژول ظاهر نمی‌شود.

## تست ایمنی

`_ops/tests/test_life_currency_units_safety.py` — **۱۰ passed**.

ثابت می‌کند: مشتق ۱۰۰۰@۱۰۷.۶۹→۱.۲۴۶ · فرض ۳۰ثانیه ۱.۲۴۶ نمی‌دهد · `credits_to_aud` می‌ترکد · نبود import به مسیر پول · cap=۳۰ در کف ۳۰s به میلی‌واحد می‌رسد · AMBER@۳۰s توکن صفر · calls در هر دو سقف زیر CALL_COST صفر می‌ماند.

محدودیت تست: نبودِ import امروز را قفل می‌کند؛ سیم‌کشی تازه تست را قرمز می‌کند. ادعای «تا ابد ناممکن» ریاضی نیست. مسیر پول جدا بماند: سقف‌های زندهٔ AUD (۳۰ ماهانه، ۲۰ human_gate، ۲۴ hard stop، ۱ per-call) با بودجهٔ کلی ابزار در قاب خودشان مدیریت می‌شوند؛ `life_credit` به `money_gate` یا `model_router` گره نمی‌خورد.
