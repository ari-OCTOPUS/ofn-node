# C-042 — نقص گردکردن میلی‌واحد → starvation بی‌صدا

contradiction_id: C-042
status: OPEN
owner: CORE
priority: بعد از ریاستارت
blocks_restart: false
created: 2026-08-20T11:18+10:00
implementation: **propose only** — accumulator micro-credit این جلسه پیاده نشد

## علت

`allocate_beat` استخر beat را بین ۱۱ عضو تقسیم می‌کند، سپس `LifeBudget.as_dict` توکن را `round(..., 3)` می‌کند (میلی‌واحد). سهم زیر ۰.۰۰۰۵ → **۰.۰۰۰**. هیچ رخداد MEMBER_STARVED امروز وجود ندارد.

## اعداد (دو لایه)

لایهٔ الف — همان ارقام کارت کار (بدون کسر ۲۰٪ ذخیره؛ تقسیم `pool/11`):

| cap | period_s | رنگ | pool / beat_share | سهم خام / عضو | گردشده |
|---|---:|---|---:|---:|---:|
| 30 | 30 | AMBER scale=0.5 | 0.005208 | 0.00047348 | **0.000** starvation |
| 30 | 30 | GREEN | 0.010417 | 0.000947 | 0.001 لبهٔ کف |
| 30 | ~115.72 | GREEN | 0.040181 | 0.00365 | 0.004 سالم |

لایهٔ ب — مسیر کد (`RESERVE_FLOOR_PCT=0.20` سپس `/11` سپس round 3dp) — `test_life_currency_units_safety.py` ۱۰/۱۰:

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
   در بدترین حالت بالا: هر عضو 1.3636/روز و مجموع 15.0/روز — بودجه حفظ می‌شود
4. detector: اگر سهم مؤثر یک عضو در N ضربان متوالی صفر بماند → `MEMBER_STARVED`

`life_credit` به `money_gate` / `model_router` / `cost_receipt` وصل نمی‌شود. `credits_to_aud()` fail-closed می‌ماند.

## آزاد بعدی

**C-043**
