# ECONOMY (ماشینی)

> machine-generated · grade=MEASURED · منبع: `_ops/state/pulse/sim-fixed/` + `02-DECISIONS/PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19.md`

## حالت: شبیهسازی (تخصیصِ زنده هنوز صفر است — سیمکشی B1 در انتظار رأی مالک)

| اندام | وضعیت | credit | دفاع |
|---|---|---:|---:|
| organism | ACTIVE | 10.0 | 0 |
| work_pump | RETIRED | 0.0 | 1 |

**خزانهها:** SURVIVAL=17.0 · MAINTENANCE=0.0 · DISCOVERY=0.0 · HUMAN_VALUE=0.0

## ناورداها (آزمایششده)

- SURVIVAL → DISCOVERY ممنوع (رسید رد)
- خودگزارشی = صفر credit (ضدبازی)
- budget_after هرگز منفی نمیشود
- RETIRE = حذف نیست (هویت/دفاع/شواهد میمانند)
- replay از ردیفهای append-only: بازسازی قطعی

## بدهی B1 (اعمالنشده)

`PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19.md` — cardiac-budget.json باید daily_cap بنویسد؛ تا رأی مالک، صفر تخصیصِ زنده در LIFE-CURRENCY-SPEC ثبت است.
