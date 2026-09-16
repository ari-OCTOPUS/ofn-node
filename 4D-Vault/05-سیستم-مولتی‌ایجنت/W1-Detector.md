---
id: w1-detector
aliases: [W1, Detector, آشکارساز سایه]
tags: [سیستم, agent]
model: GLM
related: ["[[E-shadow]]", "[[قضیه‌ی-شناسایی]]", "[[W2-Analyst]]"]
---
# 🔍 [[W1-Detector|W1]] — Detector

> [!info] آشکارسازِ سایه‌ی بُعدِ پنهان
> [[E-shadow|E_shadow]] و [[Delta-self|Δ_self]] را روی سریِ زمانیِ واقعی محاسبه می‌کند. می‌پرسد: آیا نشانه‌ی بُعدِ پنهان هست؟

## مأموریت

- محاسبه‌ی temporal MI و lag-1 autocorrelation روی داده‌ی خام
- تخمینِ ρ و signal_fraction
- مقایسه‌ی E_shadow تجربی با لنگرِ ۰.۰۱۲۵۵۳
- طبقه‌بندی: آیا [[قضیه‌ی-شناسایی]] (λρ≠0) برقرار است؟

## ورودی

- سریِ زمانی (numpy array)
- برچسبِ منبع

## خروجی

| کمیت | تفسیر |
|---|---|
| temporal_mi | نرخِ ساختارِ زمانی |
| rho_hat | ρ تخمینی |
| E_shadow_proxy | تخمینِ سایه |
| detectable | بله/خیر |## کد
`4d_system/agents/detector.py` → `DetectorAgent`