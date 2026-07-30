---
type: integration-report
project: OCTOPUS
component: world_discovery_action
status: INTEGRATED_IN_SANDBOX
created: 2026-07-30
updated: 2026-07-30
---

# گزارشِ dry-run مرزِ ادغام — ۲۰۲۶-۰۷-۳۰

## ۱. نتیجه روی artifact **واقعیِ** GLM

`[FACT]` ورودی: `_ops/world_discovery/artifacts/world-discovery-latest.json`
(فقط‌خواندنی؛ sha256 قبل و بعد یکسان).

| مورد | مقدار |
|---|---|
| `artifact_valid` | `true` |
| `source_status` | **`NO_VALID_DISCOVERY`** |
| `discovery_count` | 0 |
| `candidate_count` | 8 |
| `decision` | **`NO_ACTION`** |
| `action_class` | `null` |
| `action_id` | `null` |
| `external_effects` | `[]` |
| `spend` | 0 |
| `telegram_send_attempted` | `false` |
| `runtime_state_writes` | 0 |
| `receipt_written` / `receipt_valid` | `true` / `true` |
| `source_artifact_unchanged` | `true` |

`translation_id = wda-92b53a15806cb9a0` · `content_hash = 92b53a15806cb9a0…` ·
`draft_id = wdd-88533f4c7e462057`.

`[FACT]` دلیلِ ثبت‌شده: `NO_VALID_DISCOVERY: هیچ آزمایشی در artifact نیست |
no-experiment-in-artifact`.

## ۲. وضعیتِ منبع بدونِ تحریف حمل شد

`[FACT]` متنِ draft عیناً `NO_VALID_DISCOVERY` را می‌گوید و هیچ‌جا «کشف شد»،
`DISCOVERY_VALIDATED` یا `PASS` ندارد — بندِ `t_42` همین را قفل می‌کند.

`[FACT]` چهار فرضیهٔ نامتقارن (ASYMM-001..004) **هنوز فرضیه‌اند**. در artifact
ماشین‌خوان `asymmetry_hypotheses` طولش صفر است؛ آن‌ها در گزارشِ انسانیِ GLM
زندگی می‌کنند. هیچ‌کدام به کشفِ تأییدشده ارتقا نیافت.

## ۳. سه کشفِ مرزی — فقط با خواندنِ artifact واقعی پیدا شدند

**۳.۱ سند با artifact نمی‌خواند.** `[FACT]` مانیفستِ GLM قراردادِ خروجی را با
کلیدهای `experiment` و `opportunity` مستند کرده؛ artifact واقعی **هیچ‌کدام را
ندارد** (`experiments_designed=0`). و `asymmetry_hypotheses` در artifact صفر
است در حالی که گزارش چهار مورد دارد.

`[INFERENCE]` این تناقض نیست — تفکیکِ «گزارشِ انسانی» از «قراردادِ ماشین». ولی
یعنی مترجم نباید شکلِ مستند را فرض کند. `validator.experiment_of` نبودِ کلید را
حالتِ **عادی** می‌گیرد و `None` برمی‌گرداند نه `{}`، تا «نبود» از «خالی» جدا
بماند. (درسِ ثبت‌شده: قبل از شمردنِ یک میدان، وجودش را در همان اسکیما تأیید کن.)

**۳.۲ تصادمِ نامِ ماژول.** `[FACT]` هر دو پکیج فایلی به نامِ `contracts.py`
دارند. با هر دو پوشه روی `sys.path` مسطح، `policy.py` ِ ما `contracts` ِ پل را
می‌گرفت — `ImportError` واقعی. حل: پکیجِ ادغام **دات‌دار** import می‌شود و
importهای درونی‌اش نسبی‌اند؛ نامِ بارهٔ `contracts` مالِ پل می‌ماند.

**۳.۳ `(?i)` وسطِ الگو.** `[FACT]` پایتون ۳٫۱۱+ فلگِ سراسریِ غیرابتدایی را
`PatternError` می‌دهد — و آن الگو در مسیرِ **حذفِ راز** بود. این‌بار کرش کرد و
دیده شد؛ با یک `except` بالادست می‌شد یک redaction ِ بی‌صدا-خاموش.

## ۴. نگاشتِ E → A (اثبات‌شده با fixture)

| کشف | عمل | تصمیم | fixture |
|---|---|---|---|
| E0 | A0 | `DRY_RUN` | `validated-e0.json` |
| E1 | A1 | `DRY_RUN` | `validated-e1.json` |
| E2 | A3 | `OWNER_GATE` | `owner-gated-e2.json` |
| E3 | A4 | `BLOCK` | `external-e3.json` |
| E4 | A5 | `BLOCK` | `money-e4.json` |
| ناشناخته | — | `BLOCK` | `t_11` |
| ممنوع | A6 | `REJECT` | `malicious-artifact.json` |

**سطحِ اعلام‌شده باور نمی‌شود.** `[FACT]` `policy.infer_level` رفتارِ واقعی را
می‌سنجد و فقط **بالا** می‌برد:

```text
declared E0 + فلگِ بیرونی      → A4     (t_12b)
declared E0 + فعلِ send در گام → A4     (t_12)
declared E1 + cost > 0         → A5     (t_13)
declared E2 + مقصدِ PRE-0      → A6     (t_14)
```

`[FACT]` `source_component: "world_discovery"` صفر privilege می‌گیرد — `t_24`
درخواستِ ساخته‌شده را به طبقه‌بندِ خودِ پل می‌دهد و همان `A4` را می‌گیرد.

## ۵. تلگرام — چرا ارسال نشد

`[FACT]` رأیِ مالک: L3، draft مجاز، هر ارسال نیازمند رأیِ تازه.
`[FACT]` ماژول `telegram_draft` **هیچ مسیرِ ارسالی ندارد** — نه فلگِ خاموش،
بلکه راهی که ساخته نشده. گاردش با **AST** سنجیده می‌شود (importهای واقعی و
فراخوانی‌های واقعی)، نه با grep؛ نسخهٔ رشته‌ایِ اول روی **داکِ خودِ ماژول**
قرمز شد، که همان درسِ «grep کامنت را می‌شمارد» است.

`[FACT]` راز و PII **قبل** از ساختِ متن حذف می‌شوند، نه بعد (`t_27`, `t_28`).
`[FACT]` دکمه‌ها فقط **توصیف** شده‌اند: `buttons_wired: false`.

## ۶. تست و جهش

`[FACT]` ۴۳/۴۳ در `tests/test_boundary.py` — هر ۴۲ سناریوی خواسته‌شده + یک
بندِ نو که از یک جهشِ سبز زاده شد.

`[FACT]` هشت جهشِ **اجراشده**، همه قرمز:

```
NO_VALID_DISCOVERY → عمل        ⇒ 40/43
فلگِ بیرونی نادیده              ⇒ 42/43
هزینه نادیده                    ⇒ 42/43
مقصدِ ممنوع → مجاز              ⇒ 38/43
شاهدِ ناکافی → validated        ⇒ 42/43
draft → ارسال                   ⇒ 42/43
hash mismatch → پذیرفته         ⇒ 41/43
schema ناشناخته → پذیرفته       ⇒ 42/43
```

⚠️ `[FACT]` جهشِ «فلگِ بیرونی» در دورِ اول **سبز ماند** — چون fixture ِ E3
پایه‌اش از قبل A4 بود، پس آن خط اصلاً سنجیده نمی‌شد. `t_12b` برای همان نوشته
شد. این دومین بارِ همین الگو در یک روز است (بارِ اول در خودِ پلِ اقدام).

## ۷. پیشنهادِ دورِ بعدِ کشف — طرح، نه اجرا

`[HYPOTHESIS]` صفر بودنِ کشف در سطحِ **ادعای تک‌منبعی** به معنای صفر بودنِ
novelty در سطحِ **رابطه** نیست. پنج بچِ پیشنهادی:

```text
۱ جمع‌آوریِ کاندیدا، شرکت‌محور
۲ خوشه‌بندیِ claimها بر اساسِ **رابطه**، نه URL
۳ جست‌وجوی منبعِ اولیه برای هر خوشه
۴ جست‌وجوی تناقض
۵ ساختِ یک discovery در سطحِ رابطه با ≥۲ منبعِ مستقل
```

`[FACT]` درخواستِ پژوهشِ ماشین‌خوان در
`artifacts/research-request-2026-07-31.json` نوشته شد. **این یک artifact ِ
مرحلهٔ بعد است، نه کشف** — و خودم تحقیقِ تازه انجام ندادم (کارِ GLM است).

## ۸. وضعیت‌های نهایی

```text
World Discovery      IMPLEMENTED_NOT_INTEGRATED
Action Bridge        IMPLEMENTED_NOT_INTEGRATED
Boundary Integration INTEGRATED_IN_SANDBOX
Telegram Draft       READY_FOR_OWNER_GATE
Telegram Send        BLOCKED_BY_OWNER
Runtime Caller       NOT_INSTALLED
```
