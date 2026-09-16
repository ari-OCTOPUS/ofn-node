---
id: dare
aliases: [DARE, Riccati, معادله ریکاتی, Discrete Algebraic Riccati Equation]
tags: [ریاضی, #quantitative, #anchor]
category: ریاضی
math: "λ²P² + [σ_ε²(1−ρ²) − σ_ζ²λ²]P − σ_ζ²σ_ε² = 0"
anchor_P: 0.00325184
related: ["[[کف-کالمن]]", "[[E-shadow]]", "[[Delta-self]]"]
---
# [[DARE-معادله‌ی-ریکاتی|DARE]] — معادله‌ی ریکاتیِ گسسته

> [!info] خلاصه
> حلِ بسته‌فرم برای حدِ steady-state خطای کالمن در یک مدل خطی-گاوسی. قلبِ همه‌ی محاسباتِ پروژه.## تعریف

معادله‌ی اسکالر:
$$P = \frac{\rho^2 P \sigma_\varepsilon^2}{\lambda^2 P + \sigma_\varepsilon^2} + \sigma_\zeta^2$$

این یک معادله‌ی درجه‌ی دو در P است. ریشه‌ی مثبت (بسته‌فرم):

$$\boxed{P = \frac{(\sigma_\zeta^2\lambda^2 - \sigma_\varepsilon^2(1-\rho^2)) + \sqrt{(\sigma_\varepsilon^2(1-\rho^2) - \sigma_\zeta^2\lambda^2)^2 + 4\lambda^2\sigma_\zeta^2\sigma_\varepsilon^2}}{2\lambda^2}}$$

## حدِ λ→0

فرمول 0/0 است. حدش:
$$P \to \frac{\sigma_\zeta^2}{1-\rho^2}$$
> [!warning] گاردِ عددی الزامی
> در کد باید این حد به‌صورتِ صریح هندل شود، وگرنه تقسیم بر صفر.

## عدد (در [[نقطه‌ی-کار]])

| کمیت | مقدار | منبع |
|---|---|---|
| P (informed) | **0.00325184** | [[📊 جدول-لنگرها]] |
| P_blind | **0.01526172** | با σ_ζ'² = σ_ζ² + σ_d² |## بازتولیدپذیری

> [!check] ۳ مسیر مستقل
> 1. بسته‌فرم تحلیلی
> 2. Fixed-point iteration (rel err < 7e−13 روی ۳۰۰ draw)
> 3. Monte-Carlo (T=1.2M، seed=123)

## ارتباطات

- راه می‌دهد به [[کف-کالمن]] (S = λ²P + σ_ε²)
- پایه‌ی [[E-shadow]] و [[Delta-self]]
- در [[مدل-خطی-گاوسی]] تعریف می‌شود

## منبع
- کد: [[📄 متن-کامل-4py]] (توابع `P_closed`, `P_iter`)
- متن: [[📄 متن-کامل-handoff]] §۳