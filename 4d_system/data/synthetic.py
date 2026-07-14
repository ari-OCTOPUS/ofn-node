"""
data/synthetic.py — Synthetic data generators for benchmarking.

These produce controlled time series with KNOWN hidden structure,
so we can verify the detection pipeline before running on real data.
"""
from __future__ import annotations

import numpy as np


def gaussian_iid(n: int = 10000, sigma: float = 1.0,
                 seed: int | None = None) -> np.ndarray:
    """Pure noise — the NULL model. Should show E_shadow ≈ 0."""
    rng = np.random.default_rng(seed)
    return rng.normal(0, sigma, n)


def ar1(n: int = 10000, rho: float = 0.7, sigma: float = 0.1,
        seed: int | None = None) -> np.ndarray:
    """
    AR(1): s(t) = ρ·s(t−1) + noise.
    Has temporal structure → E_shadow > 0 (if ρ≠0).
    """
    rng = np.random.default_rng(seed)
    s = np.zeros(n)
    noise = rng.normal(0, sigma, n)
    for t in range(1, n):
        s[t] = rho * s[t-1] + noise[t]
    return s


def ar1_plus_noise(n: int = 10000, rho: float = 0.7,
                   signal_sigma: float = 0.1, noise_sigma: float = 0.3,
                   seed: int | None = None) -> np.ndarray:
    """
    AR(1) signal observed through noise — closest analog to the SOG model.
    Y(t) = s(t) + ε(t) where s is AR(1).
    """
    s = ar1(n, rho, signal_sigma, seed)
    # ε(t) باید مستقل از نوآوری‌های AR(1) باشد. قبلاً default_rng(seed) اینجا و
    # داخلِ ar1 دو generator هم‌جریان می‌ساخت → obs_noise دقیقاً همان استریمِ
    # نرمالِ نوآوری‌ها (با مقیاسِ دیگر) بود؛ یعنی همبستگیِ کاملِ سیگنال-نویز،
    # نقضِ صریحِ مدلِ Y(t)=s(t)+ε(t). با spawn_key استریمِ مستقلِ قطعی می‌سازیم.
    noise_rng = np.random.default_rng(
        None if seed is None else np.random.SeedSequence(seed, spawn_key=(1,)))
    obs_noise = noise_rng.normal(0, noise_sigma, n)
    return s + obs_noise


def arma11(n: int = 10000, rho: float = 0.5, theta: float = 0.3,
           sigma: float = 0.1, seed: int | None = None) -> np.ndarray:
    """
    ARMA(1,1): exactly the structure of the SOG shadow z(t).
    z(t) = ρ·z(t−1) + η(t) + θ·η(t−1).
    """
    rng = np.random.default_rng(seed)
    eta = rng.normal(0, sigma, n)
    z = np.zeros(n)
    for t in range(1, n):
        z[t] = rho * z[t-1] + eta[t] + theta * eta[t-1]
    return z


def mixture_gaussian(n: int = 10000, seed: int | None = None) -> np.ndarray:
    """
    Heavy-tailed (non-Gaussian) data. Tests whether non-Gaussianity
    alone can mimic hidden-dimension signatures.
    """
    rng = np.random.default_rng(seed)
    comp = rng.choice([0, 1], size=n, p=[0.7, 0.3])
    return np.where(comp == 0,
                    rng.normal(0, 0.5, n),
                    rng.normal(0, 2.0, n))


def logistic_map(n: int = 10000, r: float = 3.9,
                 x0: float = 0.5) -> np.ndarray:
    """
    Deterministic chaos: x(t+1) = r·x(t)·(1−x(t)).
    Has structure but is non-linear and non-Gaussian.
    Tests the limits of linear shadow detection.
    """
    x = np.zeros(n)
    x[0] = x0
    for t in range(n - 1):
        x[t+1] = r * x[t] * (1 - x[t])
    return x


# Catalog for the UI dropdown
CATALOG = {
    "Gaussian iid (NULL model)":    {"fn": gaussian_iid,    "desc": "پایه‌ی نویز — انتظار E_shadow≈0"},
    "AR(1) ρ=0.7":                  {"fn": lambda n, s: ar1(n, 0.7, seed=s), "desc": "حافظه قوی — E_shadow>0"},
    "AR(1)+noise (SOG analog)":     {"fn": lambda n, s: ar1_plus_noise(n, 0.7, seed=s), "desc": "نزدیک‌ترین به مدل SOG"},
    "ARMA(1,1)":                    {"fn": lambda n, s: arma11(n, seed=s), "desc": "ساختار دقیق سایه‌ی SOG"},
    "Mixture Gaussian":             {"fn": lambda n, s: mixture_gaussian(n, seed=s), "desc": "غیرگوسی — تست کاذب"},
    "Logistic map (chaos)":         {"fn": lambda n, s: logistic_map(n), "desc": "آشوب قطعی"},
}


def generate(name: str, n: int = 10000, seed: int = 42) -> np.ndarray:
    """Generate by catalog name."""
    entry = CATALOG[name]
    fn = entry["fn"]
    try:
        return fn(n, seed)
    except TypeError:
        return fn(n)


if __name__ == "__main__":
    for name in CATALOG:
        data = generate(name, n=5000)
        print(f"{name:35s}  mean={data.mean():+.4f}  var={data.var():.4f}  "
              f"lag1_ac={np.corrcoef(data[:-1], data[1:])[0,1]:+.4f}")
