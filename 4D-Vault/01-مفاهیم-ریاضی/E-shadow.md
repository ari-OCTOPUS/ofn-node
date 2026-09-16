---
id: e-shadow
aliases: [E_shadow, shadow visibility, سایه اطلاعاتی, E_shadow]
tags: [ریاضی, #quantitative, #anchor, #core-concept]
category: ریاضی
source: "[[برداشت_من_از_دو_فایل]]"
anchor: 0.012553
math: "½·log(σ_z²/S_b)"
related: ["[[Delta-self]]", "[[اتحاد-chain-rule]]", "[[قضیه‌ی-شناسایی]]", "[[Diaconis-Freedman]]"]
---
# [[E-shadow|E_shadow]] — سایه‌ی اطلاعاتی

> [!info] خلاصه
> چقدر «وجودِ» یک بُعدِ پنهان از بیرون قابل‌تشخیص است — بدونِ هیچ دسترسیِ ویژه. نرخِ ساختارِ زمانی که سایه لو می‌دهد.

## تعریف

$$\boxed{E_{\text{shadow}} = \frac{1}{2}\log\!\left(\frac{\sigma_z^2}{S_b}\right)}$$

که:
$$\sigma_z^2 = \frac{\lambda^2(\sigma_\zeta^2 + \sigma_d^2)}{1-\rho^2} + \sigma_\varepsilon^2$$

σ_z² = واریانسِ حاشیه‌ایِ مشاهداتِ بدونِبایاس (z = Y − b)## تفسیر

> [!abstract] خوانشِ انسانی
> این نرخِ اطلاعاتی است که **گذشته‌ی سایه** درباره‌ی آینده‌اش لو می‌دهد — تنها ردی که یک ناظرِ کاملاً بیرونی می‌تواند از **وجودِ** بُعدِ پنهان بگیرد.
>
> عدد کوچک است: تشخیصِ «آنجا چیزی هست» ذاتاً ضعیف است.

## عدد (در [[نقطه‌ی-کار]])

| کمیت | مقدار |
|---|---|
| σ_z² | 0.0141667 |
| S_b | 0.01381543 |
| **E_shadow** | **0.012553 nat/گام** |

## قضیه‌ی شناسایی

> [!important] شرطِ دیده‌شدن
> $$E_{\text{shadow}} > 0 \iff \lambda \cdot \rho \neq 0$$
>
> هم نشت لازم است (λ≠0) هم حافظه (ρ≠0).
> - ρ=0: بُعد پنهانِ **موجود ولی نامرئی** (iid دیده می‌شود)
> - λ=0: کانالِ ارتباطی **بسته** است

→ [[قضیه‌ی-شناسایی]]## نسبت‌ها

- **E_shadow ≈ [[Delta-self|Δ_self]] / 10** — «دیدنِ وجود» ۱۰ برابر سخت‌تر از «دسترسیِ درون» است
- **E_shadow < I_pred** — چون سایه ARMA(1,1) است نه Markov-۱، جمله‌ی اول سری کل حافظه را نمی‌سازد

## رابطه‌ی ادبی

> [!quote] Bialek–Nemenman–Tishby / Crutchfield–Feldman
> E_shadow = h_μ(1) − h_μ = جمله‌ی L=1 در بسطِ excess entropy.
> مرتبط با ولی **اکیداً کوچک‌تر از** predictive information ([[I-pred]]) برای λρ≠0.

→ [[Crutchfield-Feldman]]، [[Bialek-Nemenman-Tishby]]

## پلِ هندسی

سایه‌ی استاتیکِ گاوسی جذبِ نال می‌شود (β_det=0). فقط دینامیک نجات می‌دهد:
→ [[Diaconis-Freedman]]، [[قضیه‌ی-Takens]]

## منبع
- اشتقاق: [[📄 متن-کامل-نظریه]] (بخش Track-G، §۶د)
- کد: `4d_system/core/model.py` → `ModelSolution.E_shadow`