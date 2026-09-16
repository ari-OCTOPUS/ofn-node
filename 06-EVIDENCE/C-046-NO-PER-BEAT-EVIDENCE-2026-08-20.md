# C-046 — عدم نگه‌داری شواهد per-beat

contradiction_id: C-046
status: OPEN
owner: CORE
related: C-043 · C-045
created: 2026-08-20T12:36+10:00
implementation: design only

## ادعا

شاهد عددی ارجاع‌شده به یک beat باید بعد از ضربان‌های بعدی قابل بازیابی باشد.

## دو مقدار

- value_a: `life-currency-latest.json` برای beat 42784 (نقل در دستور #۲)
- value_b: همان مسیر حالا beat زندهٔ دیگر است؛ 42784 **UNLOCATED**

علت: `os.replace` روی یک فایل (`life_currency.py:291–294`).

طرح نگه‌داری: [[EVIDENCE-RETENTION-DESIGN-2026-08-20]]. پیاده نشد. قاعدهٔ دستی: `*.snapshot.json` کنار نوت.

## حکم

OPEN.
