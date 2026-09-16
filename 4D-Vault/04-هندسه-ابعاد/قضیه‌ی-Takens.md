---
id: takens
aliases: [Takens, embedding theorem, Takens theorem]
tags: [هندسه, #theorem, ابعاد]
related: ["[[قضیه‌ی-شناسایی]]", "[[E-shadow]]", "[[Diaconis-Freedman]]"]
---
# قضیه‌ی Takens

> [!info] بُعدِ پنهان از یک سریِ زمانیِ اسکالر قابلِ بازسازی است.
> Floris Takens (1981) — «تعدادِ متغیرهای پنهان از یک مشاهده قابل تشخیص است.»

## قضیه (خلاصه)

برای یک سیستمِ دینامیک با attractorِ بعدِ d_A، یک مشاهده‌ی اسکالرِ s(t) کافی است برای بازسازیِ یک embeddingِ هم‌ارزِ توپولوژیک، اگر بُعدِ embeddingِ m ≥ 2d_A + 1 باشد.## پل به SOG

> [!important] حالتِ خطی-گاوسی
> در حالتِ خطی، تخصیصِ Kalman/ARMA همان [[قضیه‌ی-Takens]] است.
> [[E-shadow]] > 0 صورتِ کمیِ این قضیه برای مدلِ ماست:
>
> $$E_{\text{shadow}} > 0 \iff \lambda\rho \neq 0$$
>
> یعنی دینامیک (ρ≠0) + نشت (λ≠0) کافی است برای visible بودن.

## پلِ ۳D↔4D

> [!tip]+ زمان = projection مجاز
> بُعدِ چهارم را نمی‌توان به‌صورتِ **استاتیک** دید ([[Diaconis-Freedman]]).
> ولی اگر **زمان** را به‌عنوانِ projection بپذیریم (Takens)، E_shadow > 0 می‌شود.
>
> «زمان» خودش پلِ ۳D↔4D است — دقیقاً همان‌طور که ρ ≠ 0 شرطِ دیده‌شدن است.

## منابع
- Takens, F. (1981) — «Detecting strange attractors in turbulence»
- Sauer–Yorke–Casdagli (1991) — تعمیم