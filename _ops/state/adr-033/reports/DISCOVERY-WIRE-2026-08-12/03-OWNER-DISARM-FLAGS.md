---
type: evidence
status: active
created: 2026-08-12
updated: 2026-08-12
tags: [octopus, owner-vote, flags, disarm]
---

# OWNER VOTE — Disarm dark/poison + reverse money no-boundary (2026-08-12)

> **SUPERSEDED 2026-08-12 same day** by OWNER VOTE #2 — see `05-HIGH-RISK-REARM.md`.
> این فایل فقط audit trail است؛ دوباره اعمال نکن.

> رأی مالک در چت (قدیمی): «alll i want alllll of it» برای  
> `RUNNER_APPLY / SEED_* / PROFILE=1 / SMTP_*=1 / MONEY no-boundary` → **=0**  
> فاز ۴ (پول/لید) عمداً اجرا نشد.

## تغییرات (last-wins در انتهای `OCTOPUS-flags.cmd`)

| Flag | قبل | بعد |
|---|---|---|
| `OCTOPUS_WIRE_RUNNER_APPLY` | 1 | **0** |
| `OCTOPUS_WIRE_SEED_ASSEMBLER` | 1 | **0** |
| `OCTOPUS_WIRE_EVOLUTION_GATE` | 1 | **0** |
| `OCTOPUS_WIRE_REDTEAM` | 1 | **0** |
| `OCTOPUS_PROFILE` | 1 (سمّ) | **0** |
| `OCTOPUS_SMTP_FROM/HOST/PORT/USER` | 1 (سمّ) | **خالی** |
| `OCTOPUS_WIRE_VALUE_LEDGER` | 1 | **0** |
| `OCTOPUS_ENFORCE_MONEY_FSM` | 1 | **0** |
| `OCTOPUS_INITIATIVE_UNCAPPED` | 1 | **0** |
| `_ops/state/LIVE-ENABLED.flag` | موجود | **حذف** |

## اثر مورد انتظار
- فلگ‌های یتیم/unsched دیگر ادعا نمی‌کنند مسلح‌اند بدون caller
- SMTP دیگر host=`1` به mail resolver نمی‌دهد
- PROFILE دیگر paper-full auto-arm را با مقدار نامعتبر قفل نمی‌کند (۰ هم auto-arm نمی‌کند — اگر `live`/`paper-full` خواستی رأی جدا)
- مسیر پول no-boundary برمی‌گردد به hold امن‌تر

## نیاز به restart
پروسه‌هایی که env را از flags.cmd هنگام boot می‌گیرند باید restart شوند (gateway + ideally organism/cortex).

## RECONCILE AGI
گزینهٔ **C** (ادعای AGI در رفتار) **اجرا نشد** — ضد invariant صداقت. وضعیت فعلی = **A** (هدف claimed؛ آرزو فقط بافت). اگر C می‌خواهی صریح بگو.
