---
aliases: ["auto-synthetic-ARMA-1-1-"]
tags: ["کشف", "auto-generated", "synthetic:ARMA(1", "1)"]
timestamp: 2026-07-11T02:32:17.320284
type: discovery
rhythm_id: None
related: ["[[Delta-self]]", "[[E-shadow]]", "[[نقطه‌ی-کار]]"]
---

# 🔍 کشف: auto-synthetic:ARMA(1,1)

> [!abstract] خلاصه
> منبع: `synthetic:ARMA(1,1)` | تشخیص‌پذیر: ✅ بله
> تاریخ: 2026-07-11 02:32

## پارامترها

| پارامتر | مقدار |
|---|---|
| ρ (rho) | `0.648778842919414` |
| λ (lambda) | `0.5` |
| Δ_self | `0.273152` nat/گام |
| E_shadow | `0.273152` nat/گام |
| PCAI | `0.0000` |## معادلات

> [!info] مدل خطی-گاوسی — [[مدل-خطی-گاوسی]]
> $$s(t+1) = \rho \cdot s(t) + m(t) + \zeta(t)$$
> $$Y(t) = b(t) + \lambda \cdot s(t) + \varepsilon(t)$$

> [!tip] ارزش درون‌نگری — [[Delta-self]]
> $$\Delta_{self} = \frac{1}{2}\log\!\left(\frac{S_b}{S}\right) = 0.273152 \text{ nat/گام}$$

> [!tip] کشف سایه — [[E-shadow]]
> $$E_{shadow} = \frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S_b}\right) = 0.273152 \text{ nat/گام}$$

> [!important] اتحاد — [[اتحاد-chain-rule]]
> $$\frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S}\right) = E_{shadow} + \Delta_{self} = 0.546304$$

## تحلیل

🔥 ساختار قوی — MI=0.2732, ρ=0.649. بُعد پنهان واضح است. حافظه‌ی بلندمدت محتمل.

## ارتباطات

- این کشف در [[نقطه‌ی-کار]] با ρ=0.648778842919414، λ=0.5 قرار داره
- قابل‌مقایسه با [[📊 جدول-لنگرها]]
- اساس ریاضی: [[DARE-معادله‌ی-ریکاتی]] و [[کف-کالمن]]

## داده‌ی خام

---
*تولیدشده توسط ایده‌یاب شخصی در 2026-07-11 02:32*