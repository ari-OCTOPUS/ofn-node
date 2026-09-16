"""
core/nonlinear_mi.py — B12: تخمین‌گرِ MI غیرخطی (مکملِ تخمین‌گرِ خطی-گاوسی).

چرا: تخمین‌گرِ فعلی (temporal_mi = -½ln(1-ρ²)) فقط وابستگیِ **خطی** را می‌بیند.
سری‌ای مثل logistic map ساختارِ قطعیِ قوی دارد ولی خودهمبستگیِ خطی‌اش ≈۰ است —
نقطهٔ کورِ علمی. این ماژول MI(x_t; x_{t+lag}) را با هیستوگرامِ هم‌احتمال
(quantile bins — مقاوم به دُمِ سنگین) تخمین می‌زند و هر وابستگی‌ای
(خطی یا غیرخطی) را می‌بیند.

طراحی: numpy خالص، بدونِ وابستگیِ جدید، قطعی (بدونِ تصادف).
استفاده: پشتِ فلگ NONLINEAR_MI=1 در detector — کلیدِ additive «mi_nonlinear»
به findings اضافه می‌شود؛ فلگ خاموش = هیچ تغییری.
"""
from __future__ import annotations

import numpy as np


def _quantile_bins(x: np.ndarray, bins: int) -> np.ndarray:
    """گسسته‌سازیِ هم‌احتمال — هر باند تقریباً به یک اندازه نمونه دارد.

    برای توزیع‌های دُم‌سنگین از باندهای هم‌عرض بسیار پایدارتر است.
    خروجی: اندیسِ باندِ هر نمونه در بازه‌ی [0, bins-1].
    """
    # rank-transform: مقاوم به مقیاس و monotone transforms
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(len(x))
    return np.minimum((ranks * bins) // max(len(x), 1), bins - 1).astype(np.int64)


def binned_mi_lag(series: np.ndarray, lag: int = 1, bins: int = 16) -> float:
    """MI(x_t; x_{t+lag}) با تخمین‌گرِ plug-in روی باندهای هم‌احتمال [nat].

    گاردها: سریِ کوتاه/ثابت → ۰. مقدار همیشه ≥ ۰ برگردانده می‌شود.
    سوگیریِ مثبتِ plug-in با اصلاحِ Miller–Madow کاهش می‌یابد
    (تقریبِ (K_xy - K_x - K_y + 1) / 2N).
    """
    x = np.asarray(series, dtype=float).ravel()
    x = x[np.isfinite(x)]
    n = x.size - lag
    if n < 10 * bins or np.std(x) < 1e-15:
        return 0.0

    a = _quantile_bins(x[:-lag], bins)
    b = _quantile_bins(x[lag:], bins)

    joint = np.zeros((bins, bins), dtype=np.float64)
    np.add.at(joint, (a, b), 1.0)
    joint /= n

    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)

    nz = joint > 0
    mi = float(np.sum(joint[nz] * np.log(joint[nz] / (px @ py)[nz])))

    # اصلاحِ سوگیریِ Miller–Madow
    k_xy = int(nz.sum())
    k_x = int((px > 0).sum())
    k_y = int((py > 0).sum())
    mi -= (k_xy - k_x - k_y + 1) / (2.0 * n)

    return max(mi, 0.0)


def gaussian_mi_lag1(series: np.ndarray) -> float:
    """MI خطی-گاوسیِ لَگ-۱: -½ln(1-ρ²) — همان چیزی که تخمین‌گرِ فعلی می‌بیند."""
    x = np.asarray(series, dtype=float).ravel()
    x = x[np.isfinite(x)]
    if x.size < 20 or np.std(x) < 1e-15:
        return 0.0
    rho = float(np.corrcoef(x[:-1], x[1:])[0, 1])
    rho = min(max(rho, -0.999999), 0.999999)
    return -0.5 * float(np.log(1.0 - rho * rho))


def nonlinear_gain(series: np.ndarray, bins: int = 16) -> dict:
    """چقدر ساختار از چشمِ تخمین‌گرِ خطی پنهان است؟

    خروجی: {mi_nonlinear, mi_linear, gain} — gain بزرگ یعنی وابستگیِ
    غیرخطیِ قابل‌توجه (مثل آشوبِ قطعی) که مدلِ خطی نمی‌بیند.
    """
    mi_nl = binned_mi_lag(series, lag=1, bins=bins)
    mi_lin = gaussian_mi_lag1(series)
    return {
        "mi_nonlinear": round(mi_nl, 6),
        "mi_linear": round(mi_lin, 6),
        "gain": round(max(mi_nl - mi_lin, 0.0), 6),
    }


if __name__ == "__main__":
    rng = np.random.default_rng(42)

    iid = rng.normal(0, 1, 20000)

    ar = np.zeros(20000)
    noise = rng.normal(0, 0.1, 20000)
    for t in range(1, 20000):
        ar[t] = 0.7 * ar[t - 1] + noise[t]

    lg = np.zeros(20000)
    lg[0] = 0.5
    for t in range(19999):
        lg[t + 1] = 3.9 * lg[t] * (1 - lg[t])

    for name, s in [("Gaussian iid", iid), ("AR(1) ρ=0.7", ar), ("Logistic map", lg)]:
        print(f"{name:15s} {nonlinear_gain(s)}")
