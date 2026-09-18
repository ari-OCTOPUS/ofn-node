---
type: proposal
kind: advisor_proposal
status: archived_pre_answer
requires: none_for_ex1_layers
resolution: three_layer_register_not_abcd
tags: [octopus, ex1, criterion]
updated: 2026-09-07
---

بایگانی. شروع از `CURRENT-STATUS.md`. منوی A/B/C/D انتخاب نشد. `EX1_V3_0=NOT_PASSED`. EX3 از این فایل نتیجه نمی‌شود.

# پیشنهاد اصلاح معیار EX1 — نه PASS، نه waiver

GOV_VERSION=V8 · LADDER=L2 · lane=`MP-EX1-CRITERION-20260907`

این متن `kind=advisor_proposal` است. حکم مالک نیست. EX1 اصلی را قبول نمی‌کند. EX3 را شروع نمی‌کند. فیلدی به رکوردهای ۱۹۴۲۹۸/۱۹۴۳۲۹ اضافه نمی‌کند.

سند حاکم: `C:/Users/Armin/Downloads/MEGAPROMPT-OCTOPUS-v3-EXECUTABLE-2026-09-07.md` · SHA256=`ca736a4724ddac884fd39108dc6089e907fba6f1439ba61ff71cc7681cdaa4e3`.

## حکم پیشنهادی در یک جمله

دو رکورد **وجود دارند** و چند فیلد خام‌شان **اندازه‌گیری شده** است؛ اما expect اصلی EX1 — provenance داخل خود رکورد، `reason_code`، `mint_evidence.calib_tail` روی ۱۹۴۳۲۹، و `verify_chain --from-zero` — **برآورده نیست** و با بازنویسی تاریخ هم نباید برآورده شود. تعیین تکلیف فقط با اصلاح صریح work order ممکن است.

## تضاد داخلی خودِ v3 — هر دو مقدار باز

| محل | قاعده | منبع |
|---|---|---|
| §0 | اگر اختیار مصوب و قابلیت پیاده‌شده فرق داشتند، `owner_decision` نوشته شود و **lane ادامه دهد** | همان مگاپرامپت، حدود خط ۳۶ |
| EX-1 `on_fail` | اگر expect نیاید، **کل lane متوقف** | همان مگاپرامپت، خط ۱۱۹ |

`resolution: null` · `status: open`. این lane برنده‌ای انتخاب نمی‌کند. ایجنت قبلی عملاً §0 را اجرا کرد و `on_fail` را به «تناقض باز + ادامه» ترجمه کرد. آن ترجمه **waiver پنهان** است مگر مالک یکی از سه گزینهٔ پایین را امضا کند.

## آنچه واقعاً قابل اثبات است (MEASURED)

پنجره: بازخوانی مستقل debug در `2026-09-06T23:43:44Z`–`23:43:49Z` محلی، برد `DietPi` / ۱۳۸، مسیر `/home/ari/octopus-mesh/audit/audit.jsonl`. منبع: `09-LANES/MP-DEBUG-20260907/LIVE-READBACK.json`. تطبیق با رسید اول: `09-LANES/MP-EXEC-EX1-EX2-20260907/EX1-VERIFICATION-RECEIPT.json`.

### رکورد ۱۹۴۲۹۸

هر دو رسید روی این مجموعه توافق دارند:

- `seq=194298` و شمارهٔ خط همان است
- `event=standing_go_halted`
- `reason=calibration_error_ge_0.5` (کلید `reason`، نه `reason_code`)
- `calib_tail=["unresolved","confirmed","unresolved"]`
- `raw_line_sha256=2622cf331684990b4254a061f3e2985859ae23f8a4c6f7e3346047a4c996cf82` (فقط در رسید debug)

این‌ها وجود رویداد halt و متن همان خط را ثابت می‌کنند. علت علمی halt، زنده بودن سیگنال در همان چرخه، یا صحت `calibration_error` را ثابت نمی‌کنند.

### رکورد ۱۹۴۳۲۹

هر دو رسید روی این مجموعه توافق دارند:

- `seq=194329` و شمارهٔ خط همان است
- `event=standing_go_minted`
- `reason=internal_pulse`
- `raw_line_sha256=57b89fa1bdf7d9cbac0eb991e8a50a30df4e4810ef143588988ae25359aa0acb` (فقط در رسید debug)

`owner_go_id=STANDING-GO-INTERNAL-CYCLES-2026-09-06-03` در ردیف رسید اول هست؛ در `safe_fields` رسید debug نیست. این lane بایت خط را دوباره decode نکرد. وضعیت این کلید: **اندازه‌گیری‌شده در رسید اول / در این lane بازاستخراج‌نشده** — نه غایب اعلام می‌شود، نه نادیده.

§۱.۱ مگاپرامپت می‌گفت همین seq «با `mint_evidence.calib_tail`». هر دو رسید می‌گویند کلید `mint_evidence` در ردیف خام نیست. تناقض EX1-C1 همچنان `status: open`.

### ساختار دفتر، نه اصالت تاریخ

| مشاهده | مقدار | منبع | حد ادعا |
|---|---|---|---|
| پیشوند تاریخی | ۳۰٬۰۴۷٬۳۲۰ بایت / ۱۹۵٬۰۹۷ رکورد / SHA256 `029afbb1…09c` | هر دو رسید | برابر اثرانگشت قبلی؛ نه اصالت پیش از آن |
| snapshot تازه | ۳۰٬۲۴۵٬۸۵۲ بایت / ۱۹۶٬۴۶۲ رکورد / SHA256 `0fa64552…38b2` | LIVE-READBACK | صحت ساختاری همان بایت‌های خوانده‌شده |
| parse error / گسست seq روی بایت مشاهده‌شده | ۰ / ۰ | LIVE-READBACK | یکنواختی شماره؛ نه hash-chain |
| `audit_append`های دیده‌شده | `flock` و `fsync` دارند؛ `sha256`/`prev_hash` ندارند | LIVE-READBACK `writer_source` | قرارداد پیاده‌شده ≠ ابزار خواسته‌شده |
| `python -m tools.verify_chain --from-zero` | در درخت‌های اسکن‌شده نیست (E0) | EX1-VERIFICATION-RECEIPT EX1-C3 | جایگزین seq-monotonic ابزار مفقود نیست |

سه فیلد `loaded_source_revision` / `consumer_path` / `read_receipt_id` در **فایل رسید خواننده** وجود دارند. expect اصلی آن‌ها را **داخل هر رکورد** خواسته. جانشینی سطح رسید به‌جای فیلد خام، همان خطای پذیرش قبلی است.

## آنچه برای این دو seq برای همیشه UNKNOWN می‌ماند

بازنویسی ردیف تاریخی در v3 ممنوع است. پس این‌ها از روی همان بایت‌ها قابل بازیابی نیستند:

1. `loaded_source_revision` فرایندی که آن تصمیم را نوشت — نه HEAD فعلی دیسک، نه revision خوانندهٔ بعدی
2. `consumer_path` همان تصمیم
3. `read_receipt_id` همان خواندن تصمیم
4. کلید `reason_code` (متن `reason` جایگزین کد نیست)
5. `mint_evidence` و `mint_evidence.calib_tail` روی ۱۹۴۳۲۹
6. زنجیرهٔ رمزی prev-hash بین رکوردها
7. دست‌نخوردگی payload با حفظ `seq`
8. اصالت دفتر پیش از اولین fingerprint ثبت‌شده
9. اینکه halt ۲۲:۱۵ از سیگنال زندهٔ همان چرخه بود یا از tail ترمیم‌شده (O-2) — این سؤال EX3 است، نه چیزی که EX1 روی این دو خط ثابت کند
10. revision بارشده در RAM سرویس امروز

هر ادعای «EX1 PASS» که یکی از این‌ها را پر کند، یا تاریخ را دستکاری کرده یا معیار را بی‌تصویب عوض کرده است.

## آنچه از این به بعد باید سر همان تصمیم نوشته شود

این فهرست **قرارداد آینده** است، نه backfill.

حداقل روی **هر رکورد تصمیم جدید**، نه فقط روی فایل رسید خواننده:

| فیلد | نقش | یادداشت |
|---|---|---|
| `loaded_source_revision` | کدی که تصمیم را ساخت | HEAD بعدی یا هش snapshot خواننده کافی نیست |
| `consumer_path` | کدام مصرف‌کننده تصمیم را گرفت | |
| `read_receipt_id` | کدام خواندن پایدار مبنای تصمیم بود | |
| `reason_code` | کد ماشین‌خوان خروج/توقف/mint | جدا از متن `reason` |
| `mint_evidence` برای هر mint واجدشرط | از جمله snapshot `calib_tail` | بدون آن، mint فقط رویداد است نه شاهد eligibility |
| وقتی قرارداد EX3 تصویب و پیاده شد | `event_time` · `record_time` · `as_of` · `scope` · `supersedes` · `read_snapshot` | روی رکوردهای قدیمی جعل نشود |

قفل/cap لحظهٔ تصمیم (C3) باید در `read_snapshot` همان تصمیم باشد. خواندن lock امروز برای تصمیم دیروز کافی نیست.

## سه گزینه — تصویب جدا از این متن است

### A — STRICT_STOP

expect اصلی دست‌نخورده می‌ماند. EX1 = پذیرفته‌نشده. EX3 تا EX7 شروع نمی‌شوند. دو رکورد به‌عنوان شاهد جزئی MEASURED در پرونده می‌مانند. هیچ PASS ساخته نمی‌شود.

هزینه: گام‌های بعدی تا ابد روی این دو seq قفل می‌مانند، چون فیلدهای غایب دیگر به وجود نمی‌آیند مگر با کار ممنوع (بازنویسی تاریخ).

### B — SPLIT_CRITERION (پیشنهاد مشاور)

work order به دو معیار شکافته شود:

- **EX1-H (تاریخی):** فقط مجموعهٔ قابل‌دانستن بالا + تطبیق prefix + یکنواختی seq روی بایت مشاهده‌شده. برچسب: `MEASURED_PARTIAL` / `ORIGINAL_EXPECT_NOT_MET`.
- **EX1-F (آینده):** هر تصمیم جدید بدون فیلدهای جدول بالا `INVALID_FOR_DECISION` است، حتی اگر رویدادش در دفتر بنشیند.

EX3 فقط **بعد از تصویب این شکاف** و فقط روی همان knowable set، با `TAIL_ORDER_SENSITIVE=true`، بدون ساختن timestamp یا provenance جعلی. این گزینه expect اصلی را PASS نمی‌کند؛ آن را برای دادهٔ legacy **عوض** می‌کند.

### C — RECEIPT_SUBSTITUTE_WAIVER (توصیه نمی‌شود)

فیلدهای رسید خواننده و آزمون seq-monotonic به‌جای expect اصلی بنشینند. این همان کاری است که گزارش اول عملاً کرد. اگر مالک بخواهد، برچسب باید `WAIVER` باشد نه `PASS`. این lane آن را پیشنهاد نمی‌کند.

### D — NEW_BASELINE_PAIR

EX1 از این دو seq تاریخی جدا شود و به دو رکورد **جدید** وصل شود که فیلدهای اجباری را واقعاً دارند. ۱۹۴۲۹۸/۱۹۴۳۲۹ به‌عنوان `MEASURED_PARTIAL` می‌مانند. این گزینه با C یکی نیست. یک پیش‌نویس موازی همان پوشه، «C» را برای همین معنی به کار برده؛ آن تعارض برچسب `status: open` است.

## تعارض سندی باز در همین lane

| منبع | معنی گزینهٔ سوم |
|---|---|
| این فایل + `OWNER-QUESTION.md` (پس از تفکیک) | C = waiver رسیدخوان؛ D = جفت baseline تازه |
| `07-HANDOFF/EX1-CRITERION-OWNER-QUESTION-2026-09-07.md` | C = new baseline pair |

`resolution: null`. مالک باید حرف (A/B/C/D) را با همین تعریف‌ها بگوید، نه با شمارهٔ مبهم.

## آنچه این پیشنهاد اجازه نمی‌دهد

- شروع EX3 پیش از جواب مالک
- merge/rebase روی تبار منشعب ۱۳۸ `a1f0fa80` در برابر merge PR224 `b8340d0e` (۲ ahead / ۷ behind / merge-base `1b53773a` — منبع `SOURCE-COMPARISON.json`)
- commit/push/deploy candidate در `F:/wt-debug-mp-ex1-ex2-20260907`
- تغییر جهت مولد EX2 بدون مصوبهٔ جدا
- تمدید standing GO، خرید، پیام، restart، بازکردن گیت

## سؤال مالک

متن کوتاه و قابل‌جواب در `OWNER-QUESTION.md` و `07-HANDOFF/EX1-CRITERION-AMENDMENT-2026-09-07.md`. تا جواب نیاید، حالت پیش‌فرض عملیاتی این lane همان **توقف EX3** است — بدون اینکه §0 را به‌تنهایی برنده اعلام کنیم.
