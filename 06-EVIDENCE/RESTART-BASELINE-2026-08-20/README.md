# Restart baseline freeze — 2026-08-20T11:18+10:00

ثبت **پیش از** اولین رخداد ریاستارت. ماشین: SNAPSHOT.json

| فیلد | مقدار | path / method | ts | grade |
|---|---|---|---|---|
| beat | **42770** | ORGANISM-STATE.json | 11:17:34 | MEASURED |
| daily_cap زنده | **1000.0** | life-currency-latest.json | 11:16:07 | MEASURED |
| yaml cap | 30.0 | budgets.yaml | read 11:18 | MEASURED |
| period داور | **114.01** s | arbiter.effective_period_s | 11:17:34 | MEASURED |
| arbiter | GREEN · consensus · n_present=3 · n_braking=0 | ORGANISM-STATE | 11:17:34 | MEASURED |
| coherence | 0.951 (beat برچسب 42747) | OCTOPUS/CURRENT-TRUTH.md generated 01:05:42Z | vs live 42770 | **STALE_LABEL** |
| سهم ۱۱ عضو | همه **0.096** · min=0.096 · صفر نیست | life-currency-latest.json | 11:16:07 | MEASURED |
| UNIT در JSON زنده | فیلد غایب | همان فایل | 11:16:07 | OBSERVED |
| mtime | 2026-08-20T11:16:07+10 · 1470 B | Get-Item | 11:18 | MEASURED |
| تست | **10 passed** in 3.50s | `_ops/tests/test_life_currency_units_safety.py` | 11:18 | VERIFIED_BY_TESTS |
| PIDs | organism 10028 · cortex 19352 · center 20816 · gateway 15440 · live 26008 | Win32_Process | 11:18 | OBSERVED |

ABORT gates: arbiter RED = false · tests green = true → ریاستارت مجاز.
