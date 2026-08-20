# C-044 — reasons خالی روی تغییر رنگ داور

contradiction_id: C-044
status: OPEN
owner: CORE
related: C-043
created: 2026-08-20T12:22+10:00

## ادعا

گذار رنگ GREEN→AMBER (beat 42780/42784) باید در `reasons` ماشین‌خوان توضیح داده شود.

## دو مقدار

- value_a: `life-currency-latest.json` `"reasons": []` همزمان با color=AMBER؛ `arbiter-shadow.jsonl` اصلاً فیلد reasons ندارد.
- value_b: `allocate_beat` موفق عمداً `reasons: []` می‌گذارد (`life_currency.py:247`). `arbitrate` فقط برای RED دلیل رنگ می‌نویسد (`pulse_arbiter.py:243–244`). `persist` jsonl reasons را drop می‌کند (`:443–446`).

## likely

هر دو. خالی بودن در مسیر تخصیص **طراحی شده** است (دلایل شکست استخر، نه علیت رنگ). خالی بودن روی **تغییر رنگ** طراحی برای توضیح رنگ نیست — نقص تله‌متری. شاهد علیت AMBER از کد ریتم آمد نه از reasons.

## حکم

OPEN · telemetry defect · فیکس نشد.
