---
aliases: ["auto-synthetic-Logistic-map--chaos-"]
tags: ["کشف", "auto-generated", "synthetic:Logistic-map-(chaos)"]
timestamp: 2026-07-11T02:43:07.492564
type: discovery
rhythm_id: None
related: ["[[Delta-self]]", "[[E-shadow]]", "[[نقطه‌ی-کار]]"]
---

# 🔍 کشف: auto-synthetic:Logistic map (chaos)

> [!abstract] خلاصه
> منبع: `synthetic:Logistic map (chaos)` | تشخیص‌پذیر: ✅ بله
> تاریخ: 2026-07-11 02:43

## پارامترها

| پارامتر | مقدار |
|---|---|
| ρ (rho) | `-0.5065894356584248` |
| λ (lambda) | `0.5` |
| Δ_self | `0.148283` nat/گام |
| E_shadow | `0.148283` nat/گام |
| PCAI | `0.0000` |## معادلات

> [!info] مدل خطی-گاوسی — [[مدل-خطی-گاوسی]]
> $$s(t+1) = \rho \cdot s(t) + m(t) + \zeta(t)$$
> $$Y(t) = b(t) + \lambda \cdot s(t) + \varepsilon(t)$$

> [!tip] ارزش درون‌نگری — [[Delta-self]]
> $$\Delta_{self} = \frac{1}{2}\log\!\left(\frac{S_b}{S}\right) = 0.148283 \text{ nat/گام}$$

> [!tip] کشف سایه — [[E-shadow]]
> $$E_{shadow} = \frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S_b}\right) = 0.148283 \text{ nat/گام}$$

> [!important] اتحاد — [[اتحاد-chain-rule]]
> $$\frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S}\right) = E_{shadow} + \Delta_{self} = 0.296565$$

## تحلیل

🔥 ساختار قوی — MI=0.1483, ρ=-0.507. بُعد پنهان واضح است. حافظه‌ی بلندمدت محتمل.

## ارتباطات

- این کشف در [[نقطه‌ی-کار]] با ρ=-0.5065894356584248، λ=0.5 قرار داره
- قابل‌مقایسه با [[📊 جدول-لنگرها]]
- اساس ریاضی: [[DARE-معادله‌ی-ریکاتی]] و [[کف-کالمن]]

## داده‌ی خام

---
*تولیدشده توسط ایده‌یاب شخصی در 2026-07-11 02:43*