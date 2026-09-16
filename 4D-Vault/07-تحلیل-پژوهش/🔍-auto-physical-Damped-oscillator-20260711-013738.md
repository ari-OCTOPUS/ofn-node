---
aliases: ["auto-physical-Damped-oscillator"]
tags: ["کشف", "auto-generated", "physical:Damped-oscillator"]
timestamp: 2026-07-11T01:37:38.128636
type: discovery
rhythm_id: 49
related: ["[[Delta-self]]", "[[E-shadow]]", "[[نقطه‌ی-کار]]"]
---

# 🔍 کشف: auto-physical:Damped oscillator

> [!abstract] خلاصه
> منبع: `physical:Damped oscillator` | تشخیص‌پذیر: ✅ بله
> تاریخ: 2026-07-11 01:37

## پارامترها

| پارامتر | مقدار |
|---|---|
| ρ (rho) | `0.98` |
| λ (lambda) | `0.5` |
| Δ_self | `1.614463` nat/گام |
| E_shadow | `1.614463` nat/گام |
| PCAI | `0.0000` |## معادلات

> [!info] مدل خطی-گاوسی — [[مدل-خطی-گاوسی]]
> $$s(t+1) = \rho \cdot s(t) + m(t) + \zeta(t)$$
> $$Y(t) = b(t) + \lambda \cdot s(t) + \varepsilon(t)$$

> [!tip] ارزش درون‌نگری — [[Delta-self]]
> $$\Delta_{self} = \frac{1}{2}\log\!\left(\frac{S_b}{S}\right) = 1.614463 \text{ nat/گام}$$

> [!tip] کشف سایه — [[E-shadow]]
> $$E_{shadow} = \frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S_b}\right) = 1.614463 \text{ nat/گام}$$

> [!important] اتحاد — [[اتحاد-chain-rule]]
> $$\frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S}\right) = E_{shadow} + \Delta_{self} = 3.228926$$

## تحلیل

این الگو مربوط به یک نوسانگر میرا (Damped oscillator) است که نشان‌دهنده موجی متناوب با دامنه کاهشی در طول زمان می‌باشد. همبستگی بسیار بالا ($0.980$) بیانگر ساختار منظم و قابل پیش‌بینی این سیگنال است.## ارتباطات

- این کشف در [[نقطه‌ی-کار]] با ρ=0.98، λ=0.5 قرار داره
- قابل‌مقایسه با [[📊 جدول-لنگرها]]
- اساس ریاضی: [[DARE-معادله‌ی-ریکاتی]] و [[کف-کالمن]]

## داده‌ی خام

---
*تولیدشده توسط ایده‌یاب شخصی در 2026-07-11 01:37*