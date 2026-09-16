---
type: evidence
status: open
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, warmup, C-044, C-045]
---

# T17 — ناسازگاری درون-ضربانی + طراحی warm-up

created: 2026-08-20T12:36+10:00
implementation: design only — فیکس و ریاستارت این جلسه اجرا نشد

## حکم درون-ضربانی: نقص ترتیب، نه قرارداد دو-رنگ

شاهد:

| فایل | beat | ts +10 | color / سهم |
|---|---:|---|---|
| `life-currency-latest.post.json` | **42780** | 11:47:25 | GREEN · tokens **0.003** · scale 1.0 · hard_cap 0.08 |
| `arbiter-shadow.jsonl` | **42780** | 11:47:26 | **AMBER** · period 112.76 |

یک شمارهٔ beat، دو رنگ. علت: `organism.py` ارز را **قبل** از `rhythm_beat` و `arbiter.persist` صدا می‌زند (558–565 سپس 586–623). حساب‌داری با رنگ/period باقی‌مانده روی دیسک (پیش‌ریاستارت GREEN ~114s → سهم 0.003) بسته می‌شود؛ بعد داور AMBER می‌نویسد.

این «رنگ وسط ضربان عوض شود ولی حساب‌داری با رنگ قبلی ببندد» **طراحی مستند برای دو خروجی همزمان نیست** — ترتیب فراخوانی است. مرتبط با C-045.

## طراحی warm-up (پیاده نشد)

دو گزینهٔ سازگار؛ یکی کافی است:

**الف — حالت سوم `WARMUP` / `UNKNOWN`**

- اگر `len(_beat_times) < hrv_window` (الان maxlen=20، برای HRV حداقل ۲ نمونه — `rhythm.py:198–206`) رنگ ریتم = `WARMUP` نه AMBER از `hrv=0.0`.
- داور `WARMUP` را در worst-color پایین‌تر از AMBER بگذارد یا جدا نگه دارد تا آشتی AMBER کاذب نسازد.
- reasons: `rhythm window_n=1/<N> → WARMUP` (گسترش C-044).

**ب — persist کردن deque**

- نوشتن `_beat_times` روی `_ops/state/pulse/rhythm-window.json` در پایان تیک؛ خواندن در `__init__`. ریاستارت تاریخ را نمی‌کشد.
- هزینه: فایل کوچک؛ خطر پنجرهٔ کهنه اگر clock بپرد — با boot_id مقایسه شود.

## سیاست بودجه در warm-up

پیشنهاد: **محافظه‌کارانه، نه نامی، نه معلق کامل.**

| سیاست | scale | ریسک |
|---|---|---|
| نامی (GREEN) | 1.0 | همان bug 42780: سهم کامل روی رنگ دروغ |
| معلق (صفر) | 0 | starvation شبیه C-042؛ اعضا 0.000 |
| **محافظه‌کارانه** | 0.5 مثل AMBER ولی برچسب WARMUP | سقف نصف؛ دروغ GREEN نمی‌گوید؛ کف ۳۰s هنوز round به 0.000 می‌شود (C-042) |

تا accumulator نباشد، WARMUP+کف ۳۰s همان starvation را دارد — باید در reasons بیاید نه پنهان.

C-044 به‌روزرسانی شد: reasons برای هر گذار رنگ.
