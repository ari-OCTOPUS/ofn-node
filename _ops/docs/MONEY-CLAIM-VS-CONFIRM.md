---
type: knowledge
status: active
created: 2026-08-12
updated: 2026-08-12
tags: [octopus, money, honesty, sot]
---

# MONEY — claim vs confirm (SoT)

> هدفِ ماه (`GOALS-OCTOPUS.md`): `attribution.claimed` از صفر.  
> **claimed ≠ درآمد.** confirm تا CSV/reconcile PARK است.

## claim()
- می‌نویسد روی ledger با `lead_id` + `amount`.
- نیاز به لید واقعی دارد (الان لید 667951 منتظر suburb/آدرس مالک).
- **جعل claim ممنوع.**

## confirm()
- فقط از مسیر reconcile بعد از CSV واریزی‌ها.
- تا PARK برداشته نشود، confirm غیرفعال است.
- هیچ گزارش نباید claimed را «پول وصول‌شده» بخواند.

## مسیر باز
1. لید `667951…` **set_aside** شد (رأی مالک ۲۰۲۶-۰۸-۱۲) — suburb/claim/send از این لید ممنوع.
2. `claimed` فقط با لید واقعی تازه.
3. confirm همچنان PARK تا CSV (جدا از این لید).

آرشیو: `state/legs/lead-set-aside/667951….json`  
منابع: `_ops/GOALS-OCTOPUS.md` · `attribution` · `VQ-ACCT-PARK`.
