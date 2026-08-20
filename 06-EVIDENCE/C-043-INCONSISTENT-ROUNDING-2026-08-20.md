# C-043 — گردکردن ناسازگار فیلدهای life-currency

contradiction_id: C-043
status: OPEN
owner: CORE
related: C-042
created: 2026-08-20T12:12+10:00
implementation: diagnose only — فیکس این جلسه اجرا نشد

## شاهد

ادعای نشست قبل (accepted fact دستور مالک #۲):
`_ops/state/pulse/life-currency-latest.json` beat **42784** · `hard_cap=0.078` ولی `2×0.039462=0.078924` → `round(..., 3)` باید **0.079** باشد. فیلدهای دیگر با round-3dp خام می‌خوانند: `beat_pool=0.02` · `reserve=0.004` · `tokens=0.001`.

بازتولید این جلسه:

| مورد | مقدار | path / method | ts | grade |
|---|---|---|---|---|
| period داور beat 42784 | 113.65 | `_ops/state/pulse/arbiter-shadow.jsonl` | 2026-08-20T11:52:18 | MEASURED |
| JSON زنده فعلی | beat **42792** · `hard_cap=0.079` · AMBER→بعداً GREEN | `_ops/state/pulse/life-currency-latest.json` | 2026-08-20T12:00:32 | MEASURED (فایل latest؛ beat 42784 **UNLOCATED** — بازنویسی شده) |
| `allocate_beat("AMBER", 30, 113.65)` | beat_pool=0.02 reserve=0.004 **hard_cap=0.079** tokens=0.001 | `_ops/heart/life_currency.py` offline | 2026-08-20T12:12+10 | VERIFIED_BY_CODE |
| ترکیب جایگزین `2×round(beat_share,3)` | `2×0.039=0.078` | همان raw share 0.0394618 | 12:12+10 | MEASURED |
| beat 42780 period 112.76 | `round(2×0.03915278,3)=0.078` | arbiter-shadow + allocate_beat | 11:47:26 | MEASURED |

پس: فایل beat 42784 روی دیسک **UNLOCATED**. مسیر کد فعلی برای period=113.65 مقدار **0.079** می‌نویسد نه 0.078. عدد 0.078 از دو مسیر جدا می‌آید: (الف) `2×round(share,3)` نه `round(2×share,3)`؛ (ب) period کمی پایین‌تر (112.76 در اولین ضربان بعد ریاستارت).

## مسیر گردکردن هر فیلد (diagnose؛ فیکس=0)

منبع واحد: `_ops/heart/life_currency.py`.

| فیلد | raw | تابع گردکردن | خط |
|---|---|---|---:|
| `scale` | `color_scale(color)` GREEN=1 / AMBER=0.5 / RED=-1 | گرد نمی‌شود | 168–177, 215 |
| `beat_share` | `cap / (86400/period)` | گرد نمی‌شود (محلی) | 222–223 |
| `hard_cap` raw | `DAILY_BUDGET_HARD_CAP_X * beat_share` (=2×share) | — | 224 |
| `pool` raw | `min(beat_share * abs(scale), hard_cap)` | — | 227 |
| `reserve` raw | `pool * RESERVE_FLOOR_PCT` (0.20) | — | 228 |
| `share` / tokens raw | `(pool-reserve)/len(names)` | — | 238 |
| `beat_pool` published | `round(pool, 3)` | `round` بانکرز پایتون | **246** (موفق) · **232** (distributable≤0) |
| `reserve` published | `round(reserve, 3)` | همان | **246** / **232** |
| `hard_cap` published | `round(hard_cap, 3)` یعنی `round(2×beat_share, 3)` نه `2×round(beat_share,3)` | همان | **247** / **233** |
| `members.*.tokens` | `LifeBudget.tokens = share` | `round(self.tokens, 3)` در `as_dict` | **123** فراخوان از **241–244** |
| `members.*.risk_pool` | `share * RISK_WEIGHTS[A2]` (2.0) | `round(self.risk_pool, 3)` | **124** |
| `members.*.calls` | `int(share // CALL_COST)` CALL_COST=10 | `int` (کف) نه round-3dp | **123–124** و **242** |
| `daily_cap` | `daily_pool()` / `_f` | گرد نمی‌شود | **202**, `plan` **278** |
| `BudgetTransfer.tokens` | مسیر مبادله جدا | `round(self.tokens, 3)` | **140** (در latest.json اعضا نیست) |

هیچ فیلدی از فیلد گردشدهٔ دیگری مشتق نمی‌شود. هر کدام `round(raw_خود, 3)` مستقل است. بنابراین:

```
round(2 × beat_share, 3)  ≠  2 × round(beat_share, 3)
# 0.0789236 → 0.079          # 2 × 0.039 = 0.078
```

`beat_pool`/`reserve`/`tokens` برای AMBER@113.65 با round خام می‌خوانند (0.02 / 0.004 / 0.001). `hard_cap` اگر از share گردشده بازسازی شود 0.078 می‌شود، در حالی که کد `round(2×raw)` را می‌نویسد.

فیکس پیشنهاد می‌شود (اجرا نشد): یک سیاست واحد — یا همه از Decimal quantize، یا hard_cap = 2×beat_pool گردشده وقتی scale=1، و در JSON خام+گردشده هر دو.

## حکم

OPEN · مربوط به C-042 (همان round-3dp) ولی باگ جدا: **ناسازگاری ترکیب فیلدها** نه فقط starvation کف.
