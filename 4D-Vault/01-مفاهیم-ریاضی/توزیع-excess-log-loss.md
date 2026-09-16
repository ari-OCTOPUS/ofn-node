---
id: excess-distribution
aliases: [توزیع excess, Var(ex), paired variance-ratio]
tags: [ریاضی, #quantitative, #anchor]
math: "Var(ex_t) = 1 − S/S_b"
anchor_var_ex: 0.217327
anchor_var_eff: 0.208232
related: ["[[کف-کالمن]]", "[[Delta-self]]"]
---
# توزیعِ Excess Log-Loss

> [!info] پراکندگیِ اضافه‌خطا
> هر گام، excess log-loss یک متغیرِ تصادفی است. توزیعِ آن برای محاسبه‌ی power (بودجه‌ی N) لازم است.

## تعریف

$$ex_t = \frac{1}{2}\log\!\left(\frac{S_b}{S}\right) + \frac{\nu_b^2}{2S_b} - \frac{\nu^2}{2S}$$

که ν و ν_b innovationهای informed و blind هستند.

## واریانس

> [!important] جفتِ variance-ratio (نه noncentral χ²)
>
> $$\boxed{\text{Var}(ex_t) = 1 - \frac{S}{S_b} = 1 - e^{-2\Delta_{\text{self}}}}$$
>
> مقدار: **0.217327**## همبستگیِ سریالی

فرضِ iid **غلط** است. autocovariance منفی است:

$$\text{autocov}(k) = -\frac{(\lambda\rho(K-K_b))^2 \cdot a^{2(k-1)} \cdot S}{2S_b} < 0$$

که a = ρ(1 − λK_b) = 0.361914

این باعث می‌شود Var_eff از Var(ex) کمتر باشد:

| کمیت | مقدار |
|---|---|
| Var(ex) | 0.217327 |
| Σ autocov | −0.004548 |
| **Var_eff** | **0.208232** |

## بودجه‌ی N (power)

$$N = \text{Var}_{\text{eff}} \cdot \left(\frac{z}{\tau}\right)^2$$

| τ | z | N |
|---|---|---|
| 0.02 | 3 | **4,685 گام** |
| Δ_self | 3 | **~125 گام** |

> [!caution] باگ #۱۶
> فرمولِ power مرحله‌ی A (½+2E) به‌طورِ مستقیم به Stage-B منتقل نمی‌شود. توزیعِ متفاوت: noncentral χ² به‌جای paired variance-ratio.
> → [[باگ‌لجر]] #۱۶## ارتباطات

- مشتق از [[کف-کالمن]] و [[Delta-self]]
- کاربرد: محاسبه‌ی بودجه‌ی آزمایش در [[W0-Verifier]]

## منبع
- [[📄 متن-کامل-handoff]] §۴.۲
- کد: `4d_system/core/model.py` → `ModelSolution.Var_eff`
- Monte-Carlo: `4d_system/core/simulator.py`