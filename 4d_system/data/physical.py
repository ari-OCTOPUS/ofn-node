"""
data/physical.py — Physical system simulators.

These generate data from well-known dynamical systems that genuinely
have hidden dimensions / deterministic structure. They serve as
positive controls for the shadow-detection pipeline.
"""
from __future__ import annotations

import numpy as np


def brownian_motion(n: int = 10000, dt: float = 0.01,
                    D: float = 0.5, seed: int | None = None) -> np.ndarray:
    """
    Brownian motion (Wiener process): integrated white noise.
    Position is the integral of noise → strong temporal correlation.
    """
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, np.sqrt(2 * D * dt), n)
    return np.cumsum(steps)


def harmonic_oscillator(n: int = 10000, dt: float = 0.01,
                        omega: float = 2.0, gamma: float = 0.1,
                        seed: int | None = None) -> np.ndarray:
    """
    Damped harmonic oscillator. The position x(t) is observed but the
    velocity ẋ(t) is HIDDEN — a genuine hidden-dimension scenario.
    """
    rng = np.random.default_rng(seed)
    x, v = 1.0, 0.0
    trajectory = np.zeros(n)
    noise_scale = 0.01
    for t in range(n):
        # Verlet integration with damping + noise
        a = -omega**2 * x - 2 * gamma * v + rng.normal(0, noise_scale)
        v += a * dt
        x += v * dt
        trajectory[t] = x
    return trajectory


def lorenz_system(n: int = 10000, dt: float = 0.01,
                  x0=(1.0, 1.0, 1.0), sigma=10.0, beta=8/3, rho=28.0,
                  observe: str = "x") -> np.ndarray:
    """
    The Lorenz attractor — the classic chaotic system with hidden dimensions.
    We observe one coordinate (x) but the full state (x,y,z) drives it.

    This is the archetypal example of Takens' embedding theorem: a scalar
    observation from a higher-dimensional chaotic system.
    """
    x, y, z = x0
    trajectory = np.zeros(n)
    for t in range(n):
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z
        x += dx * dt
        y += dy * dt
        z += dz * dt
        trajectory[t] = {"x": x, "y": y, "z": z}[observe]
    return trajectory


def double_pendulum(n: int = 10000, dt: float = 0.005,
                    seed: int | None = None) -> np.ndarray:
    """
    Double pendulum angle θ₁(t). The full state (θ₁, θ₂, ω₁, ω₂) is
    4-dimensional but we observe only θ₁ — a direct 4D→1D shadow.
    """
    rng = np.random.default_rng(seed)
    g = 9.81
    L1 = L2 = 1.0
    m1 = m2 = 1.0

    # initial conditions (slightly randomized)
    th1 = 0.8 * np.pi + rng.normal(0, 0.01)
    th2 = 0.6 * np.pi + rng.normal(0, 0.01)
    w1 = w2 = 0.0

    angles = np.zeros(n)
    for t in range(n):
        # Lagrangian equations of motion (simplified)
        delta = th2 - th1
        den1 = (m1 + m2) * L1 - m2 * L1 * np.cos(delta)**2

        a1 = (m2 * L1 * w2**2 * np.sin(delta) * np.cos(delta)
              + m2 * g * np.sin(th2) * np.cos(delta)
              + m2 * L2 * w2**2 * np.sin(delta)
              - (m1 + m2) * g * np.sin(th1)) / den1

        den2 = L2 / L1 * den1
        a2 = (-m2 * L2 * w2**2 * np.sin(delta) * np.cos(delta)
              + (m1 + m2) * g * np.sin(th1) * np.cos(delta)
              - (m1 + m2) * L1 * w1**2 * np.sin(delta)
              - (m1 + m2) * g * np.sin(th2)) / den2

        w1 += a1 * dt
        w2 += a2 * dt
        th1 += w1 * dt
        th2 += w2 * dt
        angles[t] = th1
    return angles


# Catalog
CATALOG = {
    "Brownian motion":          {"fn": lambda n, s: brownian_motion(n, seed=s),
                                  "desc": "حرکت براونی — همبستگی قوی"},
    "Damped oscillator":        {"fn": lambda n, s: harmonic_oscillator(n),  # no seed needed
                                  "desc": "نوسان‌ساز — سرعت پنهان است"},
    "Lorenz attractor (x)":     {"fn": lambda n, s: lorenz_system(n, observe="x"),
                                  "desc": "آشوب ۳D، مشاهده‌ی ۱D — مثالِ Takens"},
    "Double pendulum (θ₁)":     {"fn": lambda n, s: double_pendulum(n, seed=s),
                                  "desc": "سایه‌ی ۴D→۱D — مستقیم‌ترین نمونه"},
}


def generate(name: str, n: int = 10000, seed: int = 42) -> np.ndarray:
    entry = CATALOG[name]
    return entry["fn"](n, seed)


if __name__ == "__main__":
    for name in CATALOG:
        data = generate(name, n=5000)
        print(f"{name:30s}  mean={data.mean():+.4f}  var={data.var():.4f}  "
              f"lag1_ac={np.corrcoef(data[:-1], data[1:])[0,1]:+.4f}")
