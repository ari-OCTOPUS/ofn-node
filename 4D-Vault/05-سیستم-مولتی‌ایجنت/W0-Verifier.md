---
id: w0-verifier
aliases: [W0, Verifier, راستی‌آزمای عددی]
tags: [سیستم, agent]
model: GLM
related: ["[[gate-و-pipeline]]", "[[📊 جدول-لنگرها]]", "[[DARE-معادله‌ی-ریکاتی]]"]
---
# ✅ W0 — [[W0-Verifier|Verifier]] (Gate)

> [!info] بازتولیدِ سومِ فرمول‌ها + سویپِ کاملِ گرید
> این ایجنت **gate** است. اگر FAIL کند، کل pipeline متوقف می‌شود.

## مأموریت

۱. حلِ [[DARE-معادله‌ی-ریکاتی]] هم بسته‌فرم هم iterative
۲. جدولِ کامل P، S، کفِ nat، [[Delta-self]]، N برای گرید λ×σ_ζ
۳. MC با seedِ **خودش** (گزارشش کند): تأیید [[توزیع-excess-log-loss]]
۴. هر لنگرِ [[📊 جدول-لنگرها]] را PASS/FAIL بزند

## استقلال

> [!warning] W0 کدِ مرجع را **نمی‌بیند**
> فقط spec ریاضی + مقادیرِ هدف + tolerance. پیاده‌سازی از صفر.
> کپیِ seed=123 نقضِ استقلال است.## Acceptance

همه‌ی لنگرها در tolerance؛ MC در ۳σ نظریه.

## کد
`4d_system/agents/verifier.py` → `VerifierAgent`