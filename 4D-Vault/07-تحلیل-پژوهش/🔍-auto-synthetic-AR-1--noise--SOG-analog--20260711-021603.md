---
aliases: ["auto-synthetic-AR-1--noise--SOG-analog-"]
tags: ["کشف", "auto-generated", "synthetic:AR(1)+noise-(SOG-analog)"]
timestamp: 2026-07-11T02:16:03.835686
type: discovery
rhythm_id: 504
related: ["[[Delta-self]]", "[[E-shadow]]", "[[نقطه‌ی-کار]]"]
---

# 🔍 کشف: auto-synthetic:AR(1)+noise (SOG analog)

> [!abstract] خلاصه
> منبع: `synthetic:AR(1)+noise (SOG analog)` | تشخیص‌پذیر: ✅ بله
> تاریخ: 2026-07-11 02:16

## پارامترها

| پارامتر | مقدار |
|---|---|
| ρ (rho) | `0.12391872090311583` |
| λ (lambda) | `0.5` |
| Δ_self | `0.007737` nat/گام |
| E_shadow | `0.007737` nat/گام |
| PCAI | `0.0000` |## معادلات

> [!info] مدل خطی-گاوسی — [[مدل-خطی-گاوسی]]
> $$s(t+1) = \rho \cdot s(t) + m(t) + \zeta(t)$$
> $$Y(t) = b(t) + \lambda \cdot s(t) + \varepsilon(t)$$

> [!tip] ارزش درون‌نگری — [[Delta-self]]
> $$\Delta_{self} = \frac{1}{2}\log\!\left(\frac{S_b}{S}\right) = 0.007737 \text{ nat/گام}$$

> [!tip] کشف سایه — [[E-shadow]]
> $$E_{shadow} = \frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S_b}\right) = 0.007737 \text{ nat/گام}$$

> [!important] اتحاد — [[اتحاد-chain-rule]]
> $$\frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S}\right) = E_{shadow} + \Delta_{self} = 0.015475$$

## تحلیل

🌫️ ساختار ضعیف — MI=0.0077. تقریباً iid. بُعد پنهان اگر هست، کم‌اثر است.

## ارتباطات

- این کشف در [[نقطه‌ی-کار]] با ρ=0.12391872090311583، λ=0.5 قرار داره
- قابل‌مقایسه با [[📊 جدول-لنگرها]]
- اساس ریاضی: [[DARE-معادله‌ی-ریکاتی]] و [[کف-کالمن]]

## داده‌ی خام

---
*تولیدشده توسط ایده‌یاب شخصی در 2026-07-11 02:16*