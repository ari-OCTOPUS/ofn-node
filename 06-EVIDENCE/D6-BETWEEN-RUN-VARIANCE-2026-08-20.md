# D6 — ابطال STABLE + واریانس بین‌اجرایی — 2026-08-20

این سند **باطل می‌کند** ادعای `CONSISTENT/STABLE` به‌عنوان حقیقت واحد.
ابزار canonical روی دیسک هست؛ **D6 بسته نیست.**

paid K=9 این جلسه: **اجرا نشد** (R7 + بودجهٔ قبلی ۲۰/۳۰ مصرف شده + مالک: واحد daily_cap پیش از هر اجرای دیگر).
ablation چهاربازویی: **شروع نشد.**

## دو نتیجه که نباید یکی‌شان چیده شود

| اجرا | RS_AB | RS_BA | برچسبِ ثبت‌شده | فایل روی دیسک |
|---|---:|---:|---|---|
| دیشب (ادعای مالک ~۲۳:۲۸) | ۱.۰ | **۰.۵۶ (۵/۹)** | RANDOMNESS_UNRESOLVED | **UNLOCATED** — هیچ `pilot-k9-result` با ۵/۹ پیدا نشد |
| نزدیک‌ترین شاهد UNRESOLVED | ۱.۰ | **۰.۶ (۳/۵)** | RANDOMNESS_UNRESOLVED | `F:/backup-island/shared/ledger/judge-reliability-p1.json` · K=**۵** · لیبل `POSITION_SWAP_PILOT` (۱۲:۵۹Z ≈ ۲۲:۵۹ +۱۰) |
| امروز ۰۰:۱۱ | ۱.۰ | **۱.۰ (۹/۹)** | CONSISTENT/STABLE | `_ops/state/pipeline/pilot-k9-result-20260820T001141.json` |

Fisher دقیق دوطرفه ۵/۹ در برابر ۹/۹: **p=۰.۰۸۲۴**. یک‌طرفه همان جدول: **p=۰.۰۴۱۲**. جهت باید پیش از اجرا قفل شود؛ پیش‌ثبت سه‌بذر جهت را دوطرفه قفل کرد. ۳/۵ در برابر ۹/۹ دوطرفه: **p=۰.۱۱۰**.

حکم علمی جاری: **`BETWEEN_RUN_VARIANCE`** — نه `STABLE`.

## ابزار عوض شده ⇒ مقایسه VOID (D6 / R16)

canonical `_ops/measure/swap_consistency.py` (`rs_min=0.9`, `alpha=0.005`, `k_min=9`):

- `classify_swap(9,9,9,9)` → CONSISTENT / gate STABLE
- `classify_swap(9,9,5,9)` → **SECOND_POSITION_BIAS** / gate `INSTABILITY_SIGNIFICANT` (rs_ba≈۰.۵۵۶ < ۰.۹) — **نه** RANDOMNESS_UNRESOLVED
- `classify_swap(5,5,3,5)` → **RANDOMNESS_UNRESOLVED** (K<۹)

پس برچسب UNRESOLVED روی دیسک با **K=۵** می‌خواند، نه با K=۹ canonical. اگر اجرای دیشب K=۹ بود و UNRESOLVED نام گرفت، آن هارنس canonical نبود.

اجرای ۰۰:۱۱: «frozen live4 harness + judge_choice_v3 + single-token fallback» (`phase-gates` k9-pilot). جزیره آستانهٔ متفاوت دارد (`rs_min=0.8`, `alpha=0.05`).

**مقایسهٔ این دو = VOID.** هیچ‌کدام تنها منبع حقیقت نیست.

جفت‌ها هم یکی ثابت نشد: جزیره `p1-pilot`؛ ۰۰:۱۱ shaهای `6aa23c0c` / `171defa9` (متن جفت ذخیره نشده — همان جفت قابل بازداوری نیست).

## جملهٔ ابطال‌شده

«فرضیهٔ artifact نمونهٔ کوچک ابطال شد» **نادرست** است.

آن نقد دربارهٔ **RS_AB** بود. RS_AB در هر دو روایت **۱.۰** است → آن نقد **تأیید** شد نه ابطال. آنچه عوض شد **RS_BA** است.

انتخاب اجرای دوم و اعلام پایداری = cherry-pick. `phase-gates.jsonl` خط `k9-pilot` و `02-DECISIONS/ACTIVATION-REPORT-2026-08-20.md` §۳ این جمله را دارند — این overlay آن‌ها را **باطل** می‌کند، بازنویسی تاریخ نمی‌کند.

محدودیت اجرای ۰۰:۱۱ (از قبل): ۹ فراخوان AB یک `text_sha`؛ ۹ BA یک `text_sha` دیگر — شبه‌تکرار، نه ۹ داوری مستقل. Wilson ۹/۹ = [۰.۷۰۰۸, ۱.۰]؛ کران پایین < `rs_min=0.9`.

## VOID — ادغام ممنوع

| برچسب | نسبت | فاصله | نقش |
|---|---|---|---|
| `VOID_PREFIX` | ۸/۵۹ = ۱۳.۶٪ | Wilson ۹۵٪ **۷.۰٪–۲۴.۵٪** `[0.0703, 0.2454]` | بایگانی؛ پیش از اصلاح ابزار |
| `VOID_POSTFIX` | ۰/۴۰ | Wilson دوطرفه `[0, 0.0876]`؛ کران بالای یک‌طرفهٔ ۹۵٪ **≈۷.۲٪** | پس از اصلاح؛ underpowered برای «بهبود» |

P(۰ VOID در ۲۰ | ۱۳.۶٪) = **۵.۴۲٪**. P(۰ در ۴۰) = **۰.۲۹٪**.

ادغام PREFIX+POSTFIX ممنوع (cross-instrument). ادعای «VOID بهبود یافت» still underpowered.

سایزینگ ablation روی ۱۵۶/۱۸۴ برای **۳۰ جفت معتبر** می‌ماند (نه آزمون نصف‌شدن VOID). توان نصف‌شدن ۱۳.۶٪→۶.۸٪ ≈۳۰۷/بازو — [[../02-DECISIONS/PRE-REG-K9-THREE-SEED-2026-08-20]]. ادعای بهبود VOID ممنوع.

## D6 هنوز باز است

بسته می‌شود فقط با: یک هارنس + همین canonical · بقیه retired (جزیره از قبل بنر دارد) · سپس K=۹ **سه بار با seed متفاوت**. اگر RS_BA پایدار نبود → حکم `BETWEEN_RUN_VARIANCE` می‌ماند.

این جلسه آن سه اجرا را **نکرد**: بودجهٔ k9 = ۲۰/۳۰ مصرف‌شده؛ سقف جدید پیش‌ثبت و امضا نشده؛ مالک اجرای دیگر را تا روشن‌شدن واحد daily_cap بست.

پروتکل وقتی بودجه بیاید: [[../02-DECISIONS/PRE-REG-K9-THREE-SEED-2026-08-20]] (UNSIGNED). seedهای A/B/C قفل؛ جهت Fisher دوطرفه؛ متن جفت ذخیره شود؛ بدون چیدن یک اجرا.
