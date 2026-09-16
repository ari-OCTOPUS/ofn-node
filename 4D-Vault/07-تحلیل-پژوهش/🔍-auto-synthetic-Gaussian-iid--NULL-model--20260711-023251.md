---
aliases: ["auto-synthetic-Gaussian-iid--NULL-model-"]
tags: ["کشف", "auto-generated", "synthetic:Gaussian-iid-(NULL-model)"]
timestamp: 2026-07-11T02:32:51.458136
type: discovery
rhythm_id: 661
related: ["[[Delta-self]]", "[[E-shadow]]", "[[نقطه‌ی-کار]]"]
---

# 🔍 کشف: auto-synthetic:Gaussian iid (NULL model)

> [!abstract] خلاصه
> منبع: `synthetic:Gaussian iid (NULL model)` | تشخیص‌پذیر: ✅ بله
> تاریخ: 2026-07-11 02:32

## پارامترها

| پارامتر | مقدار |
|---|---|
| ρ (rho) | `0.05234602480030412` |
| λ (lambda) | `0.5` |
| Δ_self | `0.001372` nat/گام |
| E_shadow | `0.001372` nat/گام |
| PCAI | `0.0000` |## معادلات

> [!info] مدل خطی-گاوسی — [[مدل-خطی-گاوسی]]
> $$s(t+1) = \rho \cdot s(t) + m(t) + \zeta(t)$$
> $$Y(t) = b(t) + \lambda \cdot s(t) + \varepsilon(t)$$

> [!tip] ارزش درون‌نگری — [[Delta-self]]
> $$\Delta_{self} = \frac{1}{2}\log\!\left(\frac{S_b}{S}\right) = 0.001372 \text{ nat/گام}$$

> [!tip] کشف سایه — [[E-shadow]]
> $$E_{shadow} = \frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S_b}\right) = 0.001372 \text{ nat/گام}$$

> [!important] اتحاد — [[اتحاد-chain-rule]]
> $$\frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S}\right) = E_{shadow} + \Delta_{self} = 0.002744$$

## تحلیل

🌫️ ساختار ضعیف — MI=0.0014. تقریباً iid. بُعد پنهان اگر هست، کم‌اثر است.

## ارتباطات

- این کشف در [[نقطه‌ی-کار]] با ρ=0.05234602480030412، λ=0.5 قرار داره
- قابل‌مقایسه با [[📊 جدول-لنگرها]]
- اساس ریاضی: [[DARE-معادله‌ی-ریکاتی]] و [[کف-کالمن]]

## داده‌ی خام

---
*تولیدشده توسط ایده‌یاب شخصی در 2026-07-11 02:32*