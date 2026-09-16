---
type: evidence
status: open
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, evidence, retention, C-046]
---

# طراحی نگه‌داری شواهد per-beat (پیاده نشد)

contradiction_id: **C-046**
created: 2026-08-20T12:36+10:00
implementation: **design only**

## علت UNLOCATED شدن beat 42784

`life_currency.emit` با `os.replace` روی `_ops/state/pulse/life-currency-latest.json` می‌نویسد (`life_currency.py` 291–294). هر ضربان شاهد قبلی را نابود می‌کند. هر نوت که به beat خاص ارجاع دهد، بعد از یک تیک دیگر فایل را از دست می‌دهد.

همین الگو: `ORGANISM-STATE.json`، `arbiter-latest.json`، `identities-latest.json`.

## طرح (اجرا=۰)

Append-only، نه جای `latest`:

1. jsonl: `_ops/state/pulse/history/life-currency.jsonl` — یک رکورد فشرده در هر emit موفق (بدون indent).
2. اختیاری: کپی نقطه‌ای `life-currency-<beat>.json` فقط اگر `OCTOPUS_LC_BEAT_SNAPSHOT=1` (حجم بیشتر).

`latest` برای داشبورد می‌ماند. تاریخچه جدا است.

## سیاست نگه‌داری پیشنهادی

| لایه | مدت | عمل |
|---|---|---|
| hot jsonl | ۱۴ روز | فایل روزانه `life-currency-YYYY-MM-DD.jsonl` |
| warm | روز ۱۵–۹۰ | gzip هفتگی |
| cap | ۲۰۰ MB کل history ارز | اگر رد شد، قدیمی‌ترین week را دور بریز بعد از gzip روی cold |
| چرخش | نیمه شب محلی +10 | rename روز |

## تخمین حجم

شاهد اندازه: `life-currency-latest.json` = **1515 B** indent=1 · mtime 2026-08-20T12:32:31 · snapshot T14.

jsonl بدون indent ≈ **۸۰۰–۹۰۰ B**/رکورد (تخمین؛ UNVERIFIED تا یک رکورد واقعی نوشته شود). محاسبهٔ زیر با **1515 B** (بدبینانه، همان قالب فعلی):

| period | ضربان/روز `86400/p` | در روز | ۱۴ روز | ۳۰ روز |
|---:|---:|---:|---:|---:|
| 113 s | 764.6 | **1.16 MB** | 16.2 MB | 34.8 MB |
| 30 s | 2880 | **4.16 MB** | 58.2 MB | 125 MB |

با jsonl فشردهٔ ~850 B: حدود **۰.۶۵×** این اعداد. gzip هفتگی معمولاً ۴–۸× کوچک‌تر (UNVERIFIED تا نمونه).

## قاعدهٔ دستی تا پیاده‌سازی

هر عددی که در نوت شاهد می‌شود **همان لحظه** در `*.snapshot.json` کنار همان نوت کپی می‌شود. این جلسه: `T14-PERIOD-PROVENANCE-2026-08-20.snapshot.json`.

C-046: «عدم نگه‌داری شواهد per-beat».
