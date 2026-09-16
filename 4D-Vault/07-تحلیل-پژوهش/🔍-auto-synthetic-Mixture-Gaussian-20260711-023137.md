---
aliases: ["auto-synthetic-Mixture-Gaussian"]
tags: ["کشف", "auto-generated", "synthetic:Mixture-Gaussian"]
timestamp: 2026-07-11T02:31:37.188720
type: discovery
rhythm_id: None
related: ["[[Delta-self]]", "[[E-shadow]]", "[[نقطه‌ی-کار]]"]
---

# 🔍 کشف: auto-synthetic:Mixture Gaussian

> [!abstract] خلاصه
> منبع: `synthetic:Mixture Gaussian` | تشخیص‌پذیر: ✅ بله
> تاریخ: 2026-07-11 02:31

## پارامترها

| پارامتر | مقدار |
|---|---|
| ρ (rho) | `0.0531568927769498` |
| λ (lambda) | `0.5` |
| Δ_self | `0.001415` nat/گام |
| E_shadow | `0.001415` nat/گام |
| PCAI | `0.0000` |## معادلات

> [!info] مدل خطی-گاوسی — [[مدل-خطی-گاوسی]]
> $$s(t+1) = \rho \cdot s(t) + m(t) + \zeta(t)$$
> $$Y(t) = b(t) + \lambda \cdot s(t) + \varepsilon(t)$$

> [!tip] ارزش درون‌نگری — [[Delta-self]]
> $$\Delta_{self} = \frac{1}{2}\log\!\left(\frac{S_b}{S}\right) = 0.001415 \text{ nat/گام}$$

> [!tip] کشف سایه — [[E-shadow]]
> $$E_{shadow} = \frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S_b}\right) = 0.001415 \text{ nat/گام}$$

> [!important] اتحاد — [[اتحاد-chain-rule]]
> $$\frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S}\right) = E_{shadow} + \Delta_{self} = 0.002830$$

## تحلیل

🌫️ ساختار ضعیف — MI=0.0014. تقریباً iid. بُعد پنهان اگر هست، کم‌اثر است.

## ارتباطات

- این کشف در [[نقطه‌ی-کار]] با ρ=0.0531568927769498، λ=0.5 قرار داره
- قابل‌مقایسه با [[📊 جدول-لنگرها]]
- اساس ریاضی: [[DARE-معادله‌ی-ریکاتی]] و [[کف-کالمن]]

## داده‌ی خام

---
*تولیدشده توسط ایده‌یاب شخصی در 2026-07-11 02:31*