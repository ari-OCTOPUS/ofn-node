---
type: evidence
status: open
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, life-currency, provenance, C-043, C-045]
---

# T14 — provenance مقدار period

verdict: **ONE_TICK_TEMPORAL_SKEW**
created: 2026-08-20T12:36+10:00
updated: 2026-08-20T12:48+10:00
implementation: diagnose only — فیکس این جلسه اجرا نشد
snapshot: `06-EVIDENCE/T14-PERIOD-PROVENANCE-2026-08-20.snapshot.json`

```yaml
verdict: ONE_TICK_TEMPORAL_SKEW
source_relation: SAME_PIPELINE_DIFFERENT_SNAPSHOT
judge_period_beat_42830: 113.61
life_currency_period_beat_42784: UNLOCATED
reconstructed_period_range: "[112.32, 113.04)"
```

## ERRATA — DIFFERENT_SOURCE گمراه‌کننده بود

حکم اولیهٔ T18/دستور #۳: `DIFFERENT_SOURCE`. مالک 2026-08-20 ACCEPT_WITH_CORRECTIONS: منبع فایل یکی است (`ORGANISM-STATE.arbiter`)؛ اختلاف **یک تیک تأخیر** است نه دو منبع جدا. `DIFFERENT_SOURCE` حذف نشد؛ منسوخ است. کانونیکال = `ONE_TICK_TEMPORAL_SKEW` / `SAME_PIPELINE_DIFFERENT_SNAPSHOT`. C-043 همچنان `SUSPECTED_VOID`.

## منبع خواندن در کد (نه cache، نه فاصلهٔ دو beat)

`life_currency.tick` → `plan()` بدون `period_s` → `_read_color()[1]`.

| چیست | کجاست | خط |
|---|---|---:|
| آرگومان اختیاری `period_s` | `allocate_beat` / `plan` | `life_currency.py` **206**, **268** |
| اگر آرگومان نیاید | `ORGANISM-STATE.json` → `arbiter.effective_period_s` | **258–265**, **272–273** |
| پیش‌فرض فقدان | `124.0` | **217**, **263**, **265** |
| cache در حافظه | **نیست** — هر tick فایل را دوباره می‌خواند | — |
| محاسبه از فاصلهٔ دو beat | **نیست** | — |
| فراخوان زنده | `organism.py` `_lc.tick(beat)` **بدون** period/color | **558–565** |
| داور همین ضربان | `pulse_arbiter.persist` **بعد از** tick ارز | **609–623** |
| فیلد `period_s` در JSON منتشرشده | **غایب** (کلیدها: schema/color/scale/beat_pool/reserve/hard_cap/members/reasons/ts/daily_cap/unit/money_path/dry_run/beat) | emit **285–294** |

پس منبع فایل یکی است (`ORGANISM-STATE.arbiter`) ولی **نسخه یکی نیست**: حساب‌داری نسخهٔ **تیک قبلی** را می‌خواند؛ داور نسخهٔ **همین تیک** را می‌نویسد.

## beat 42784 — مقدار مصرفی

روی دیسک در `life-currency-latest.json` **UNLOCATED** (بازنویسی). خود JSON حتی وقتی بود `period_s` نداشت → مقدار مصرفی به‌عنوان فیلد **UNLOCATED**.

بازسازی از فیلدهای نقل‌شدهٔ مالک (AMBER، `hard_cap=0.078`, `beat_pool=0.02`, `reserve=0.004`, `tokens=0.001`) با `round(x,3)` روی هر چهار فیلد:

`period ∈ [112.32, 113.04)`  MEASURED از حساب معکوس · snapshot

این بازه **شامل 112.76 است و شامل 113.65 نیست.**

| period | beat_share | `round(2×share,3)` | منبع |
|---:|---:|---:|---|
| 112.76 | 0.03915278 | **0.078** | arbiter-shadow beat **42780** ts 11:47:26 |
| 113.65 | 0.03946181 | **0.079** | arbiter-shadow beat **42784** ts 11:52:18 |

پس `hard_cap=0.078` در 42784 با period داورِ **همان** beat نمی‌خواند؛ با period داورِ **42780** (آخرین persist ارگانیسم قبل از جهش chrono) می‌خواند.

## سری period داور 42780–42784

منبع: `_ops/state/pulse/arbiter-shadow.jsonl` (persist هر حلقهٔ ارگانیسم، با beatِ chrono).

| beat | ts +10 | period_s | color | گام نسبت به قبلی |
|---:|---|---:|---|---|
| 42779 | 11:35:41 | 114.63 | GREEN | — |
| **42780** | 11:47:26 | **112.76** | AMBER | −1.87 s |
| 42781 | — | **UNLOCATED** | — | shadow ردیف ندارد |
| 42782 | — | **UNLOCATED** | — | |
| 42783 | — | **UNLOCATED** | — | |
| **42784** | 11:52:18 | **113.65** | AMBER | از 42780: **+0.89 s** روی ۴ شمارهٔ chrono |

گام‌های میانی ثبت نشده‌اند. فاصلهٔ زمانی 42780→42784 = ۲۹۲ ثانیه ≈ ۲–۳ خوابِ ~۱۱۳s. شمارهٔ chrono وسط خواب جلو می‌رود؛ `persist` فقط روی حلقهٔ ارگانیسم است → پرش beat در jsonl.

## حکم

**DIFFERENT_SOURCE.** نه دو فرمول گردکردن: یک فایل، دو لحظه. حساب‌داری period/color تیک قبل (اینجا: 42780 / 112.76) را خرج می‌کند؛ گزارش داور period همین beat (42784 / 113.65) را نشان می‌دهد.

حداقل تغییر (پیاده نشد): `_lc.tick` را به **بعد از** `persist` ببر و `plan(color=…, period_s=…)` را از همان snapshot همین ضربان بده؛ `period_s` را در JSON بنویس. یک منبع واحد = خروجی داورِ همین beat.

C-043 → **SUSPECTED_VOID** (ادعای rounding ناسازگار). مسئلهٔ واقعی → [[C-045]] در همین پوشه / `01-TRUTH/CONTRADICTIONS.md`.
