---
type: knowledge
kind: discovery-ledger
status: active
updated: 2026-08-16
created: 2026-08-16
created_by: agent (continuous-improve A+C+F)
audience: owner
tags: [octopus, continuous-improve, sog, money-gate, selfheal, vote-cards]
evidence: "[[../06-EVIDENCE/IMPROVE-ACF-2026-08-16|IMPROVE-ACF]]"
next_free_contradiction: C-031
---

# DISCOVERY — Continuous Improve A+C+F (2026-08-16)

> پنجرهٔ اولِ خودبهبودی دائمی (فرمان مستقیم مالک). TCB دست نخورد. پوش نشد.

## عدد

| قبل | بعد |
|---|---|
| ۵ مسیر DARE در sog_math با ZeroDivision | ۰ ترکیدگی؛ canonical P همان |
| `money_gate.check(-1)` = allow | deny `amount-not-a-spend` |
| ۰/۸۳ رویداد selfheal با فیلد `ok` | قرارداد نو + تست False→ok=False |

## کارت‌های رأی

### [VOTE A] گارد DARE در TCB core + امضای مجدد
```
الان: 4d_system/core/model.py::P_closed(ρ=1, λ=0) هنوز ZeroDivisionError
      check_invariants روی این ورودی anchors_ok=False می‌شود
پیشنهاد: همان گارد _ops/heart/sog_math (nan + بدون استثنا) داخل core + generate_trust_boundary + امضا
اگر تأیید: additive در TCB؛ بدون فلگ تازه
ریسکِ بی‌عمل: دو نسخهٔ ریاضی واگرا می‌مانند (ارگانیسم امن، مغز 4d شکننده)
نه: بازنویسی مدل یا شل‌کردن لنگرها
```

### [VOTE B] I_pred را وارد run_self_test کن
```
الان: settings.ANCHORS.I_pred=0.0144179 با compute_I_pred می‌خواند (rel 1.7e-6)
      ولی run_self_test و verifier.SETTINGS_ANCHORS آن را چک نمی‌کنند (import مرده)
پیشنهاد: additive keys در core.model.ANCHORS + استفاده از SETTINGS_ANCHORS در verifier
اگر تأیید: TCB core+config+tests → امضا
نه: فلگ NONLINEAR_MI
```
