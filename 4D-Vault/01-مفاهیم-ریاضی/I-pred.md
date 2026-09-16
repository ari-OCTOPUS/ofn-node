---
id: i-pred
aliases: [I_pred, predictive information, excess entropy, اطلاعات پیش‌بینی]
tags: [ریاضی, #quantitative, #anchor]
math: "½·Σ_{L≥0} log(S_L/S_b)"
anchor: 0.0144179
ratio: 1.149
related: ["[[E-shadow]]", "[[اتحاد-chain-rule]]", "[[Bialek-Nemenman-Tishby]]"]
---
# [[I-pred|I_pred]] — اطلاعاتِ پیش‌بینی‌گر

> [!info] خلاصه
> کلِ اطلاعاتی که گذشته درباره‌ی آینده دارد — excess entropy یا predictive information (Bialek et al. 2001).

## تعریف

$$\boxed{I_{\text{pred}} = \frac{1}{2}\sum_{L \geq 0}\log\!\left(\frac{S_L}{S_b}\right)}$$

با تکرارِ [[DARE-معادله‌ی-ریکاتی|Riccati]]:
$$P_{L+1} = \frac{\rho^2 P_L \sigma_\varepsilon^2}{S_L} + (\sigma_\zeta^2 + \sigma_d^2), \quad P_0 = \text{Var}(s)$$## رابطه‌ی سلسله‌مراتبی

> [!important] E_shadow ⊂ I_pred
> جمله‌ی اولِ سری (L=0) **دقیقاً** [[E-shadow]] است:
> $$I_{\text{pred}} = \underbrace{E_{\text{shadow}}}_{L=0} + \underbrace{0.001622 + 0.000214 + \dots}_{L \geq 1}$$
>
> چون سایه‌ی ما ARMA(1,1) است (نه Markov-۱)، برای λρ≠0 همیشه **E_shadow < I_pred**.

## عدد (در [[نقطه‌ی-کار]])

| جمله | مقدار (nat) |
|---|---|
| L=0 (= E_shadow) | 0.012553 |
| L=1 | 0.001622 |
| L=2 | 0.000214 |
| L=3 | 0.000029 |
| ... | ... |
| **مجموع** | **0.0144179** |

نسبت: I_pred / E_shadow = **1.149×**

نرخِ decayِ سری: φ'² = 0.13098## تفاوت با E_shadow

| ویژگی | E_shadow | I_pred |
|---|---|---|
| تعریف | ½log(σ_z²/S_b) | ½Σlog(S_L/S_b) |
| جمله‌ها | فقط L=0 | همه‌ی L≥0 |
| معادل | h_μ(1) − h_μ | excess entropy کامل |
| عضوِ اتحاد | ✓ [[اتحاد-chain-rule]] | ✗ (بیرونِ اتحاد) |

> [!warning] یکی‌گرفتن ممنوع
> E_shadow ≠ I_pred. در lit-pass قفل شود.

## منبع
- [[Bialek-Nemenman-Tishby]] (2001)
- [[Crutchfield-Feldman]] (قابِ excess entropy)
- اشتقاق: [[📄 متن-کامل-نظریه]] (بخش Track-G، G0.5)
- کد: `4d_system/core/metrics.py` → `compute_I_pred()`