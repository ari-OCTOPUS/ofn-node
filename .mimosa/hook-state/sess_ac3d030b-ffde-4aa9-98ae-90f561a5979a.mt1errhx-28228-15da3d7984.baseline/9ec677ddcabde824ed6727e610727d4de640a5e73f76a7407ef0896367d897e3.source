#!/usr/bin/env python3
"""fusion_sim.py — M-1: simِ تحقیقاتیِ Fusion (جدای از production).

سه ماژولِ آری (FusionField، FusionGate، ChronoUnit) = بیانِ کدِ معادلهٔ یکپارچهٔ
Time-Architecture/MAP.md: ∂Ψ/∂t = −L(G)·Ψ + ξ(t).

⚑ پلِ کانونی: FusionField یک آرگومانِ A می‌گیرد. اگر A = −L(G) (لاپلاسینِ گراف)،
این دقیقاً گسسته‌سازیِ MAP است. −L(G) پایدار است چون L(G) نیمه‌معین‌مثبت (eigenvalues ≤0).

این فایل RESEARCH است: در Time-Architecture/ زندگی می‌کند، نه در _ops/. هیچ وابستگی
به *_gate یا chrono.py production. ChronoUnit جای pacemaker را نمی‌گیرد (خطِ قرمز §۵).
γ و σ = متریکِ توصیفی، نه هدفِ reward (λ_persist منفی می‌ماند).

numpy مجاز (محلی/رایگان). $0 آفلاین.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


@dataclass
class FusionField:
    """φ-field: dφ = A·φ·dt + B·u·dt + Σ·dW (SDE گسسته).
    A = ماتریسِ پایداری (برای پلِ کانونی: A = −L(G)). پایدار اگر eigenvaluesِ A ≤ ۰.
    φ هرگز نباید منفجر شود (‖φ‖ کران‌دار)."""
    A: "list | object"          # ماتریس (list-of-list یا np.ndarray)
    B: "list | object | None" = None
    Sigma: "list | object | None" = None   # نویزِ محرکِ SOC
    phi: "list | object | None" = None     # بردارِ حالت
    dt: float = 0.01

    def __post_init__(self):
        if not _HAS_NUMPY:
            self._A = self.A
            self._phi = self.phi or [0.0] * len(self.A) if isinstance(self.A, list) else [0.0]
            return
        self._A = np.asarray(self.A, dtype=float)
        n = self._A.shape[0]
        self._phi = (np.asarray(self.phi, dtype=float) if self.phi is not None
                     else np.zeros(n))
        self._B = (np.asarray(self.B, dtype=float) if self.B is not None
                   else np.eye(n))
        self._Sig = (np.asarray(self.Sigma, dtype=float) if self.Sigma is not None
                     else 0.05 * np.eye(n))

    def step(self, u=None) -> "list":
        """یک گامِ گسسته: φ += A·φ·dt + B·u·dt + Σ·√dt·N(0,1). خروجی: φ."""
        if not _HAS_NUMPY:
            # fallback ساده (بدونِ ماتریس-عملیات): φ += A·φ·dt
            self._phi = [self._phi[i] + sum(self.A[i][j] * self._phi[j] for j in range(len(self._phi))) * self.dt
                         for i in range(len(self._phi))]
            return list(self._phi)
        noise = self._Sig @ (np.sqrt(self.dt) * np.random.randn(len(self._phi)))
        u_vec = np.asarray(u, dtype=float) if u is not None else np.zeros(len(self._phi))
        drift = self._A @ self._phi
        ctrl = self._B @ u_vec
        self._phi = self._phi + (drift + ctrl) * self.dt + noise
        return self._phi.tolist()

    @property
    def norm(self) -> float:
        """‖φ‖₂ — برای چکِ پایداری (نباید منفجر شود)."""
        if not _HAS_NUMPY:
            return sum(x * x for x in self._phi) ** 0.5
        return float(np.linalg.norm(self._phi))


def laplacian_matrix(edges, n):
    """L(G) = D − A از لیستِ یال‌ها. پلِ کانونی: A_stability = −L(G)."""
    if not _HAS_NUMPY:
        D = [[0.0] * n for _ in range(n)]
        A = [[0.0] * n for _ in range(n)]
        for (i, j) in edges:
            A[i][j] = A[j][i] = 1.0
            D[i][i] += 1.0
            D[j][j] += 1.0
        return [[D[i][i] - A[i][j] for j in range(n)] for i in range(n)]
    D = np.zeros((n, n))
    A = np.zeros((n, n))
    for (i, j) in edges:
        A[i][j] = A[j][i] = 1.0
        D[i][i] += 1.0
        D[j][j] += 1.0
    return D - A


def stability_matrix(edges, n):
    """A = −L(G) — پلِ کانونی. پایدار (eigenvalues ≤ ۰)."""
    if not _HAS_NUMPY:
        L = laplacian_matrix(edges, n)
        return [[-L[i][j] for j in range(n)] for i in range(n)]
    return -laplacian_matrix(edges, n)


@dataclass
class FusionGate:
    """احتمالِ تونل‌زنیِ گذارِ فاز: P = 1 − e^{−λ·dt}، λ = λ₀·e^{−α·d}.
    بحرانیت/percolation (P2/P4): σ≈1 = گذار. این فقط مدلِ تشخیصیِ فشار است —
    هرگز واردِ organ/money/capability/EffectorGate نمی‌شود (خطِ قرمز §۵.۱)."""
    lam0: float = 1.0
    alpha: float = 1.0

    def prob(self, dt: float, distance: float) -> float:
        """احتمالِ عبور در بازهٔ dt با فاصلهٔ d."""
        lam = self.lam0 * (2.718281828 ** (-self.alpha * max(0.0, distance)))
        return 1.0 - (2.718281828 ** (-lam * dt))


@dataclass
class ChronoUnit:
    """واحدِ زمانِ ذهنی: γ (اُکسِلریتر)، spiking، refractory.
    claim C1..C8: γ>1 ↔ زمانِ کش‌دار (r بالا)، γ<1 ↔ برق‌آسا.
    ⚠️ این فقط در sim است — جای pacemakerِ production را نمی‌گیرد (§۵.۲)."""
    gamma: float = 1.0
    refractory_ms: float = 2.0
    _last_fire: float = field(default=0.0, repr=False)

    def subjective_time(self, physical_dt: float) -> float:
        """مدتِ ذهنی = γ × مدتِ فیزیکی."""
        return self.gamma * physical_dt

    def try_fire(self, physical_t: float, threshold: float = 0.5) -> bool:
        """آیا در زمانِ physical_t فایر می‌کند؟ (با refractory)."""
        if physical_t - self._last_fire < self.refractory_ms / 1000.0:
            return False
        fires = random.random() < threshold
        if fires:
            self._last_fire = physical_t
        return fires


def simulate_fusion_world(edges, n_nodes, n_steps=100, dt=0.01,
                          gamma=1.0, seed=42):
    """شبیه‌سازیِ یک دنیای Fusion: فیزیکی، ذهنی، فایرها.
    خروجی: {physical_time, subjective_time, fires, final_norm, stable}."""
    random.seed(seed)
    if _HAS_NUMPY:
        np.random.seed(seed)
    A = stability_matrix(edges, n_nodes)
    field_obj = FusionField(A=A, dt=dt)
    chrono = ChronoUnit(gamma=gamma)
    fires = 0
    max_norm = 0.0
    for _ in range(n_steps):
        phi = field_obj.step()
        n = field_obj.norm
        max_norm = max(max_norm, n)
        # فایر: اگر ‖φ‖ از آستانه گذر کند
        if chrono.try_fire(physical_t=field_obj.dt, threshold=min(0.9, n / (n + 1))):
            fires += 1
    stable = max_norm < 1e6   # پایداری: منفجر نشود
    return {"physical_time": n_steps * dt,
            "subjective_time": chrono.subjective_time(n_steps * dt),
            "fires": fires, "final_norm": field_obj.norm,
            "max_norm": max_norm, "stable": stable,
            "gamma": gamma, "n_nodes": n_nodes}
