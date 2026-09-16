---
id: full-4py
aliases: [4.py, متن کامل 4py, کد مرجع]
tags: [پیوست, #reference, #code]
related: ["[[DARE-معادله‌ی-ریکاتی]]", "[[📊 جدول-لنگرها]]", "[[MOC-ریاضی]]"]
---
# 📄 متن کامل — 4.py

> [!info] کدِ مرجعِ پروژه
> این کد منبعِ حقیقتِ عددیِ همه‌ی محاسبات است. در `4D/4.py` قرار دارد و در `4d_system/core/model.py` به‌صورتِ ماژولار بازنویسی شده.

```python
# Stage-B independent verification: (1) [[DARE-معادله‌ی-ریکاتی|DARE]] closed-form vs iteration,
# [[نقطه‌ی-کار|operating point]], grid, anchors, corrected power; (2) Monte-Carlo confirmation.
# Seed=123, T=1.2e6, burn=4000.
import numpy as npdef P_closed(rho, lam, se2, sz2):
    if lam == 0.0:
        return sz2/(1.0-rho*rho)
    c = se2*(1.0-rho*rho)
    return ((sz2*lam*lam - c) + np.sqrt((c - sz2*lam*lam)**2 + 4.0*lam*lam*sz2*se2))/(2.0*lam*lam)

def P_iter(rho, lam, se2, sz2, iters=8000, P0=1.0):
    P = P0
    for _ in range(iters):
        P = rho*rho*(P*se2)/(lam*lam*P+se2) + sz2
    return P# 1) closed form vs fixed-point iteration of the DARE on random draws
rng = np.random.default_rng(7)
worst = 0.0
for _ in range(300):
    rho = rng.uniform(0.0, 0.98); lam = rng.uniform(1e-3, 3.0)
    se2 = rng.uniform(1e-4, 1.0); sz2 = rng.uniform(1e-4, 1.0)
    pc = P_closed(rho, lam, se2, sz2); pi = P_iter(rho, lam, se2, sz2)
    worst = max(worst, abs(pc-pi)/pc)
print("DARE closed-form vs iteration, max rel err (300 random draws):", worst)# 2) operating point
rho, lam = 0.5, 0.5
se2, sz2, sd2 = 0.01, 0.0025, 0.01
P  = P_closed(rho, lam, se2, sz2);      S  = lam*lam*P  + se2; K  = P*lam/S
Pb = P_closed(rho, lam, se2, sz2+sd2);  Sb = lam*lam*Pb + se2; Kb = Pb*lam/Sb
D  = 0.5*np.log(Sb/S)
print(f"P ={P:.8f}   S ={S:.8f}   K ={K:.6f}")
print(f"Pb={Pb:.8f}   Sb={Sb:.8f}   Kb={Kb:.6f}")
print(f"Sb/S={Sb/S:.6f}   Delta_self={D:.6f} nats")

# ... (باقی کد: MC verification، grid sweep، autocov)
# نسخه‌ی ماژولار: 4d_system/core/model.py
```

> [!tip] نسخه‌ی ماژولار
> کدِ ماژولار و قابلِ import در `4d_system/core/model.py` بازنویسی شده و
> همه‌ی لنگرها با rel err < 1e-۵ بازتولید شده‌اند.## خروجی‌ی کانونی

| کمیت | مقدار |
|---|---|
| P | 0.00325184 |
| S | 0.01081296 |
| [[Delta-self|Δ_self]] | 0.122520 |
| DARE closed vs iter | max rel err 7.2e−13 |

→ [[📊 جدول-لنگرها]]