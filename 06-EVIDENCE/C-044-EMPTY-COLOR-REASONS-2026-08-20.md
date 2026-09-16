# C-044 — reasons خالی روی تغییر رنگ داور

contradiction_id: C-044
status: OPEN
owner: CORE
related: C-043 · C-045
created: 2026-08-20T12:22+10:00
updated: 2026-08-20T12:36+10:00

## ادعا

گذار رنگ باید در `reasons` ماشین‌خوان توضیح داده شود — **برای هر گذار** (GREEN↔AMBER↔RED↔WARMUP)، نه فقط RED.

## دو مقدار

- value_a: `life-currency-latest.json` `"reasons": []` همزمان با color؛ `arbiter-shadow.jsonl` فیلد reasons ندارد.
- value_b: `allocate_beat` موفق عمداً `reasons: []` (`life_currency.py:247`). `arbitrate` فقط اگر `color == "RED"` دلیل رنگ append می‌کند (`pulse_arbiter.py:243–244`). `persist` jsonl فقط `ts, beat, period, driver, color, wire_open` می‌نویسد (`:443–446`) — reasons drop.

`arbiter-latest.json` برای GREEN هم `reasons` دوره/اجماع دارد (رانندهٔ period، نه علت رنگ). آن متن جایگزین گذار رنگ نیست.

## گسترش دستور #۳

خواسته: reasons برای **هر** گذار رنگ پر شود. فیکس پیاده نشد.

طراحی پیشنهادی (اجرا=۰): در `arbitrate` بعد از تعیین color، اگر color ≠ previous_color (از latest روی دیسک یا آرگومان)، append مثل `color GREEN→AMBER because rhythm.hrv=0.0 window_n=1`. jsonl همان فیلد را نگه دارد. life-currency reasons جدا بماند (شکست استخر) مگر اینکه color را از داور همین beat بگیرد (C-045).

## حکم

OPEN · telemetry defect · فیکس نشد.
