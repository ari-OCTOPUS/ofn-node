---
aliases: ["auto-physical-Damped-oscillator"]
tags: ["کشف", "auto-generated", "physical:Damped-oscillator"]
timestamp: 2026-07-11T09:19:39.189465
type: discovery
rhythm_id: 1286
related: ["[[Delta-self]]", "[[E-shadow]]", "[[نقطه‌ی-کار]]"]
---

# 🔍 کشف: auto-physical:Damped oscillator

> [!abstract] خلاصه
> منبع: `physical:Damped oscillator` | تشخیص‌پذیر: ✅ بله
> تاریخ: 2026-07-11 09:19

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
> $$\frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S}\right) = E_{shadow} + \Delta_{self} = 3.228926$$## تحلیل

این الگو یک «نوسان میرا» (Damped Oscillator) است که در آن دامنه نوسانات به طور نمایی در طول زمان کاهش می‌یابد. ضریب همبستگی بسیار بالا (۰.۹۸) و مقدار قابل‌توجه اطلاعات متقابل، نشان‌دهنده تطابق دقیق و روابط قوی بین متغیرهای این مدل فیزیکی است.

## ارتباطات

- این کشف در [[نقطه‌ی-کار]] با ρ=0.98، λ=0.5 قرار داره
- قابل‌مقایسه با [[📊 جدول-لنگرها]]
- اساس ریاضی: [[DARE-معادله‌ی-ریکاتی]] و [[کف-کالمن]]

## داده‌ی خام

---
*تولیدشده توسط ایده‌یاب شخصی در 2026-07-11 09:19*