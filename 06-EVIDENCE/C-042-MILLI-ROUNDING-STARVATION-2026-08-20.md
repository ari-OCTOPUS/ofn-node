# C-042 — نقص گردکردن میلی‌واحد → starvation بی‌صدا

contradiction_id: C-042
status: REPRODUCED_OFFLINE
owner: CORE
priority: بعد از ریاستارت
blocks_restart: false
created: 2026-08-20T11:18+10:00
errata: 2026-08-20T12:10+10:00 — دستور مالک #۲ T7
implementation: **propose only** — accumulator micro-credit این جلسه پیاده نشد
t12: pytest `test_life_currency_floor_rounding.py` 5 passed + `test_life_currency_units_safety.py` 10 passed = 15 passed in 0.83s (2026-08-20T12:25+10, offline)

## علت

`allocate_beat` استخر beat را بین ۱۱ عضو تقسیم می‌کند، سپس `LifeBudget.as_dict` توکن را `round(..., 3)` می‌کند (میلی‌واحد). سهم زیر ۰.۰۰۰۵ → **۰.۰۰۰**. هیچ رخداد MEMBER_STARVED امروز وجود ندارد.

## فرمول صحیح (مالک #۲)

```
beat_share = cap / (86400 / period)
hard_cap   = 2 × beat_share
pool       = min(beat_share × scale, hard_cap)
reserve    = pool × 0.20
per_member = (pool − reserve) / 11
```

جدول مرجع ۱۱ عضو — این اعداد حاکم‌اند:

| state | period | scale | pool | reserve | per_member | rounded |
|---|---:|---:|---:|---:|---:|---:|
| cap1000 GREEN | 114.01 | 1.0 | 1.319560 | 0.263912 | 0.095968 | 0.096 |
| cap30 GREEN | 114.00 | 1.0 | 0.039583 | 0.007917 | 0.002879 | 0.003 |
| cap30 AMBER | 113.65 | 0.5 | 0.019731 | 0.003946 | 0.001435 | 0.001 |
| cap30 GREEN floor | 30.00 | 1.0 | 0.010417 | 0.002083 | 0.000758 | 0.001 |
| cap30 AMBER floor | 30.00 | 0.5 | 0.005208 | 0.001042 | 0.000379 | **0.000** |

Daily conservation worst case: each member 1.0920 · members sum 12.0067 · reserve 3.0 · total 15.0 = cap×scale.

## ERRATA (اعداد غلط را حذف نکن)

منبع خطا: **جدول مرجع دستور مالک #۱** (لایهٔ الف کارت کار). علت: **نادیده گرفتن ۲۰٪ ذخیره در تقسیم**.

| claim غلط (مالک #۱ / نوت اولیه) | مقدار غلط | مقدار صحیح (مالک #۲) |
|---|---:|---:|
| worst-case share (cap30 AMBER floor) | 0.00047348 | **0.000379** |
| per-member / day در بدترین حالت | 1.3636 | **1.0920** |

اشتقاق غلط (حفظ‌شده): `pool/11` بدون کسر `RESERVE_FLOOR_PCT=0.20` → `0.005208/11=0.00047345≈0.00047348`. صحیح: `(pool−reserve)/11 = 0.005208×0.80/11 = 0.000379`. سهم روزانهٔ غلط `0.00047348 × (86400/30) = 1.3636`؛ صحیح `0.000379 × 2880 = 1.0915≈1.0920`.

لایهٔ الف اولیه (غلط — بدون کسر ۲۰٪؛ `pool/11`):

| cap | period_s | رنگ | pool / beat_share | سهم خام / عضو | گردشده |
|---|---:|---|---:|---:|---:|
| 30 | 30 | AMBER scale=0.5 | 0.005208 | 0.00047348 | **0.000** starvation |
| 30 | 30 | GREEN | 0.010417 | 0.000947 | 0.001 لبهٔ کف |
| 30 | ~115.72 | GREEN | 0.040181 | 0.00365 | 0.004 سالم |

لایهٔ ب اولیه (مسیر کد — `RESERVE_FLOOR_PCT=0.20` سپس `/11` سپس round 3dp) — این لایه با فرمول صحیح هم‌خوان است؛ فقط جدول مرجع مالک #۱ غلط بود:

| cap | period_s | رنگ | beat_pool گردشده | tokens/عضو گردشده |
|---|---:|---|---:|---:|
| 30 | 30 | AMBER | 0.005 | **0.000** |
| 30 | 30 | GREEN | 0.010 | 0.001 |
| 30 | 107.69 | GREEN | 0.037 | 0.003 |
| 30 | 115.72 | GREEN | 0.040 | 0.003 |

بدترین حالت واقعی داور = کف ۳۰s × AMBER در **هر دو لایه** به صفر می‌رسد. این تیکت ریاستارت را قفل نمی‌کند.

## راه‌حل پیشنهادی (اجرا=0)

1. حسابداری داخلی صحیح: `1 life_credit = 1_000_000 µc`
2. `carry_ledger` per member: باقی‌ماندهٔ تقسیم در ضربان بعد پرداخت شود
3. invariant روزانه: مجموع پرداخت‌ها == cap × scale  
   در بدترین حالت بالا: هر عضو **1.0920**/روز و مجموع 15.0/روز — بودجه حفظ می‌شود (نه 1.3636)
4. detector: اگر سهم مؤثر یک عضو در N ضربان متوالی صفر بماند → `MEMBER_STARVED`

`life_credit` به `money_gate` / `model_router` / `cost_receipt` وصل نمی‌شود. `credits_to_aud()` fail-closed می‌ماند.

## آزاد بعدی (پس از T8)

پس از ثبت C-043 در همین دستور؛ اگر T10 تناقض خالی‌بودن reasons باز کند → C-044.
