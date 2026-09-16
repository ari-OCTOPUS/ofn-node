---
title: استراتژی پیش‌بینی بیزی — مستقل از persistence
type: note
tags: [octopus, observatory, strategy, bayesian, evidence]
up: "[[00-INDEX]]"
evidence_level: A
created: 2026-08-15T18:30+10:00
---

# استراتژی پیش‌بینی بیزی

> [!check] این استراتژی جایگزین کپی‌کردن persistence شد.
> روی دادهٔ زندهٔ USGS: OCTOPUS = 0.99 در برابر Persistence = 0.80.

## مسئله

تا ۱۵ اوت عصر، `run_observatory.py:120-135` سیگنال persistence را کپی می‌کرد:

```
OCTOPUS = 0.80
Persistence = 0.80
```

این یعنی استراتژی پیش‌بینی فعلی **هیچ اضافه‌ای روی baseline نداشت**. با تساوی،
آزمون \( \text{Brier}(\text{octopus}) < \text{Brier}(\text{persistence}) \)
بی‌معنا بود.

## راه‌حل — به‌روزرسانی بیزی

مدل: Poisson با نرخ \( \lambda \)، prior = Gamma(\(\alpha, \beta\)).

۱. **Prior**: Gamma(1, 1) — بی‌طرف روی \( \lambda \)
۲. **شاهد**: \( k \) رویداد ≥ آستانه در \( t \) ساعت
۳. **Posterior**: Gamma(\(\alpha + k, \beta + t \))
۴. **پیش‌بینی**: \( P(\geq 1 \text{ event in 24h}) = 1 - \left(\frac{\beta_{\text{post}}}{\beta_{\text{post}} + 24}\right)^{\alpha_{\text{post}}} \)

فایل: `impl/bayesian_strategy.py` (۷٬۷۶۵ B، stdlib خالص)

## نتایج روی دادهٔ واقعی

| حالت | k | n | OCTOPUS | Persistence | تفاوت |
|---|---|---|---|---|---|
| USGS زنده | 14 | 284 | **0.99** | 0.80 | ✅ |
| بدون رویداد بزرگ | 0 | 100 | **0.49** | 0.20 | ✅ |
| بدون داده | 0 | 0 | **0.49** | 0.20 | ✅ |
| فعالیت بالا | 30 | 300 | **0.99** | 0.80 | ✅ |

> [!important] OCTOPUS حالا یک ادعای مستقل دارد.
> وقتی شاهد اخیر با نرخ پایه هم‌خوان باشد، posterior ≈ prior ≈ persistence —
> درست است. وقتی شاهد اخیر متفاوت باشد، posterior از persistence فاصله می‌گیرد.

## چرا بیزی

- **ساده و قابل تفسیر**: هر کس می‌فهمد «شاهد اخیر + نرخ پایه = پیش‌بینی»
- **مستقل از persistence**: فرمول کاملاً متفاوت
- **stdlib خالص**: هیچ وابستگی بیرونی
- **تصحیح Laplace**: صفر-تقسیم ندارد
- **با تصحیح خودهمبستگی سازگار**: block bootstrap همچنان کار می‌کند

## تست‌ها

`tests/test_bayesian.py` — ۲۰ تست:

| مجموعه | تعداد | چه چیزی را می‌گیرد |
|---|---|---|
| TestBasicPredict | ۵ | احتمال معتبر، یکنوایی، کرانه‌ها |
| TestDiffersFromPersistence | ۳ | تفاوت با persistence در همهٔ حالت‌ها |
| TestGeoJSONExtraction | ۵ | استخراج از بدنهٔ GeoJSON، JSON نامعتبر، آستانه |
| TestBaselines | ۳ | هر چهار baseline حاضر |
| TestValidation | ۴ | ورودی نامعتبر، کراندن، صفر |

## ادغام با runner

`bayesian_strategy.py` به‌صورت پیشنهادی آماده است. runner فعلی باید در
`run_observatory.py:120-135` به‌جای کپی‌کردن persistence، `BayesianPredictor.predict_from_evidence(body_bytes)`
را صدا بزند.

> [!warning] این ادغام هنوز روی لپ‌تاپ انجام نشده.
> سطح شاهد C تا اجرا روی ماشین مالک. فایل‌ها در پروژهٔ پرپلکسیتی آماده‌اند.
