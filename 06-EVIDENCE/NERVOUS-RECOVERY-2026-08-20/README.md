---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, nervous-recovery]
---

# Nervous-System Recovery — 2026-08-20

GitHub public `owner/repo`: **UNLOCATED**. Remote واقعی: `germline E:/germline/octopus.git`. Commit ادعایی Agent دیگر **`7a66352` روی همین درخت محلی هست** (HEAD آن جلسه WAVE0_PARTIAL) — merge از GitHub انجام نشد چون مبدأ عمومی پیدا نشد.

## چه ساخته شد (ریل A، امشب)

لایهٔ مرکزی ایزوله: `_ops/nervous_recovery/`

```
Scanner receipts
  → Evidence Normalizer (receipt_v2, test_discovery, capability_parser)
  → Reality Governor (wave0_governor)  → WAVE0_PARTIAL, wave1_unlocked=false
  → Repair Planner (DAG, applies_patches=false)
  → Verifier (test_nervous_recovery.py 8/8)
```

Capability Immune System: ۱۰ حس `EFFECTORS` با parse ساختاری AST (قبلاً regex → ۰). بدون receipt زنده همه **DORMANT** نه VERIFIED.

## گیت‌های Wave 0 (این لحظه)

منبع: `WAVE0-GATES.json`

| Gate | اکنون | آستانه | pass |
|---|---|---|---|
| Receipt attribution | 0.3378 (50/148 امروز) | ≥0.95 | false |
| Test registry | 636/790 · gap=160 | gap=0 | false (CI predicate true) |
| Memory continuity | 1 cycle سالم | ≥10 متوالی | false |
| Capability inventory | parse n=10 | parse>0 | **true** |

حکم: **WAVE0_PARTIAL**. Wave 1 / حافظهٔ خواندنی **قفل**.

ریستارت daemon/live/cortex امشب انجام نشد (نیاز به رأی مالک پس از تزریق task_id).

## ریل B / C

پیاده نشد. یافته‌ها در `CANDIDATE-FINDINGS.md` به‌صورت **کاندید** (C-048..C-053 ثبت حقیقت نشدند).

## تست

`python -X utf8 _ops/tests/test_nervous_recovery.py` → **8 passed**. در `run_all.py` ثبت نشد (WORKLOCK).
