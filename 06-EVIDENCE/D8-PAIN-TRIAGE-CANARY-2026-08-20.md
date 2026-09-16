# D8 — pain-triage: CANARY · 2026-08-20T00:28+10:00

LAW-06 · R10 · MEGA-DISCOVERY-v1 · این سشن مولد قابلیت نبود

## حکم

**CANARY** — نه VERIFIED، نه VOID.

قابلیت روی دیسک است، replay هش می‌خواند، ولی PROMOTE را همان موتور زایش صادر کرده و رسید sandbox با خروج ۱ سازگار نیست. T2 کاندید می‌ماند تا داور خانوادهٔ متفاوت (یا حداقل سشن غیرمولد + رفع تناقض sandbox) عبور دهد.

## آنچه هست (LAW-23)

| چیز | شاهد |
|---|---|
| identity | pain-triage |
| capability_id | `b0dea5128a34aa95` |
| births.jsonl | `_ops/state/organogenesis/births.jsonl` · 1 row · verdict PROMOTE · ts_iso 2026-08-19T23:53:50 |
| receipt_hash | `71799dc069ad6cc981cdfc17` |
| replay | `OrganogenesisEngine.replay` 2026-08-20T00:28+10 → replay_ok true · hash بازتولید شد |
| card | `_ops/state/organogenesis/cards/b0dea5128a34aa95.json` |
| page | `07 - Knowledge/organism-pages/b0dea5128a34aa95-CARD.md` |
| code | `_ops/legs/pain_triage.py` |
| tests | `_ops/tests/test_pain_triage.py` (5) — نوشتهٔ همان فاز ۷ FINISH-ALL |
| grade روی رسید تولد | MEASURED (هرگز VERIFIED نبود) |

## چرا CANARY نه VERIFIED

1. **LAW-06:** `engine.py` پس از shadow: `verdict = "PROMOTE" if sh["shadow_ok"] else "ITERATE"`. مولد = قاضی.
2. **sandbox متناقض:** `ok: true` و `exit_code: 1`. `lab/runner.py` برای هر اجرای غیرمسدود `ok=True` می‌گذارد، حتی شکست. مسیر تولد با خروج ۱ ادامه یافت.
3. **کد از قبل روی دیسک بود:** `__main__` فایل `legs/pain_triage.py` را می‌خواند و بعد «تولد» می‌کند. زایش = مراسم روی کد ازپیش‌نوشته، نه تولد مستقل.
4. **گیت تازگی allow=True برای NOVELTY_CANDIDATE** حتی بدون فیلدهای LEARNABLE. درس Heuresis (بدیع AND یادگرفتنی) در مسیر تولد enforce نشده.
5. این سشن می‌تواند ممیز غیرمولد باشد، اما خانوادهٔ مدلِ داورِ مستقل برای خودِ قابلیت ثبت نشده است.

## آنچه کشته شد

فرضیهٔ «pain-triage VERIFIED / قابلیت زندهٔ معیار T2» — کشته. جانشین: CANARY + overlay append-only.

فرضیهٔ «sandbox ok یعنی کاندید سبز است» — کشته (exit=1).

## overlay (births.jsonl بازنویسی نشد)

`_ops/state/organogenesis/D8-CANARY-b0dea5128a34aa95.json`
