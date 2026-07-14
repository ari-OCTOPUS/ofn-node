"""
core/model.py — The SOG linear-Gaussian model, modularized.

This is the mathematical heart of the system, extracted and cleaned up from the
reference script 4D/4.py (which remains the immutable golden-rule source).

The model:
    s(t+1) = ρ·s(t) + m(t) + ζ(t)      ζ ~ N(0, σ_ζ²)     [hidden dimension]
    Y(t)   = b(t) + λ·s(t) + ε(t)      ε ~ N(0, σ_ε²)     [observed shadow]

Three information floors:
    null      (iid):       σ_z²
    blind     (dynamics):  S_b  from DARE with σ_ζ'² = σ_ζ² + σ_d²
    informed  (self):      S    from DARE with σ_ζ²
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass


# ════════════════════════════════════════════════════════════════════════
#  DARE solver — the steady-state Kalman error covariance
# ════════════════════════════════════════════════════════════════════════

def P_closed(rho: float, lam: float, se2: float, sz2: float) -> float:
    """
    Closed-form solution of the scalar DARE:
        P = ρ²·P·σ_ε²/(λ²P + σ_ε²) + σ_ζ²

    Positive root of:  λ²P² + [σ_ε²(1−ρ²) − σ_ζ²λ²]P − σ_ζ²σ_ε² = 0

    Guard: λ→0 gives the 0/0 limit P → σ_ζ²/(1−ρ²).
    """
    if lam == 0.0:
        return sz2 / (1.0 - rho * rho)
    c = se2 * (1.0 - rho * rho)
    discriminant = (c - sz2 * lam * lam) ** 2 + 4.0 * lam * lam * sz2 * se2
    return ((sz2 * lam * lam - c) + np.sqrt(discriminant)) / (2.0 * lam * lam)


def P_iter(rho: float, lam: float, se2: float, sz2: float,
           iters: int = 8000, P0: float = 1.0) -> float:
    """
    Fixed-point iteration of the same DARE. Used for cross-validation
    against the closed form (expected rel err < 1e-9).
    """
    P = P0
    for _ in range(iters):
        P = rho * rho * (P * se2) / (lam * lam * P + se2) + sz2
    return P


# ════════════════════════════════════════════════════════════════════════
#  Kalman quantities
# ════════════════════════════════════════════════════════════════════════

@dataclass
class KalmanFloor:
    """All quantities derived from a single DARE solve."""
    P:   float
    S:   float      # innovation variance = λ²P + σ_ε²
    K:   float      # Kalman gain = Pλ/S

    @property
    def nat_floor(self) -> float:
        """½·log(2πe·S) — the differential entropy floor in nats."""
        return 0.5 * np.log(2 * np.pi * np.e * self.S)


def solve_floor(rho: float, lam: float, se2: float, sz2: float) -> KalmanFloor:
    """Solve DARE and derive S, K for one arm (informed or blind)."""
    P = P_closed(rho, lam, se2, sz2)
    S = lam * lam * P + se2
    K = P * lam / S if S != 0 else 0.0
    return KalmanFloor(P=P, S=S, K=K)


# ════════════════════════════════════════════════════════════════════════
#  Full model solution — both arms (informed + blind)
# ════════════════════════════════════════════════════════════════════════

@dataclass
class ModelSolution:
    """Complete analytical solution of the SOG Stage-B model at one point."""
    # inputs
    rho: float
    lam: float
    se2: float
    sz2: float
    sd2: float

    # informed arm
    P: float
    S: float
    K: float

    # blind arm (σ_ζ'² = σ_ζ² + σ_d²)
    Pb: float
    Sb: float
    Kb: float

    # auxiliary
    a:  float    # = ρ(1 − λK_b), the autocorrelation decay of excess
    var_e: float # Var(e), the prediction-gap process

    @property
    def Delta_self(self) -> float:
        """Value of self-modeling: ½·log(S_b/S) [nats]."""
        return 0.5 * np.log(self.Sb / self.S)

    @property
    def sigma_z2(self) -> float:
        """Marginal variance of the demeaned observation z = Y − b."""
        return self.lam ** 2 * (self.sz2 + self.sd2) / (1 - self.rho ** 2) + self.se2

    @property
    def E_shadow(self) -> float:
        """Shadow visibility: ½·log(σ_z²/S_b) [nats per step]."""
        return 0.5 * np.log(self.sigma_z2 / self.Sb)

    @property
    def identity(self) -> float:
        """Chain-rule identity: ½·log(σ_z²/S) should = E_shadow + Δ_self."""
        return 0.5 * np.log(self.sigma_z2 / self.S)

    @property
    def identity_check(self) -> float:
        """Residual of the identity (should be ≈ 0)."""
        return self.identity - (self.E_shadow + self.Delta_self)

    @property
    def detectable(self) -> bool:
        """E_shadow > 0  ⟺  λ·ρ ≠ 0  (the identifiability theorem)."""
        return self.lam * self.rho != 0

    @property
    def Var_ex(self) -> float:
        """Per-step variance of excess log-loss: 1 − S/S_b."""
        return 1.0 - self.S / self.Sb

    @property
    def Var_eff(self) -> float:
        """Effective variance accounting for negative autocovariance."""
        # autocovariance sum: −[λ²ρσ_ε²(P_b−P)/S_b]² / [S·S_b·(1−a²)]
        numer = (self.lam ** 2 * self.rho * self.se2 * (self.Pb - self.P) / self.Sb) ** 2
        denom = self.S * self.Sb * (1 - self.a ** 2)
        sum_ac = -numer / denom if denom > 0 else 0.0
        return self.Var_ex + 2 * sum_ac

    def summary(self) -> dict:
        """Return all key quantities as a dict (for tables/reports)."""
        return {
            "ρ":          self.rho,
            "λ":          self.lam,
            "σ_z²":       self.sigma_z2,
            "P":          self.P,
            "S":          self.S,
            "P_blind":    self.Pb,
            "S_blind":    self.Sb,
            "Δ_self":     self.Delta_self,
            "E_shadow":   self.E_shadow,
            "identity":   self.identity,
            "id_check":   self.identity_check,
            "detectable": self.detectable,
            "Var(ex)":    self.Var_ex,
            "Var_eff":    self.Var_eff,
        }


def solve(rho: float = 0.5, lam: float = 0.5,
          se2: float = 0.01, sz2: float = 0.0025, sd2: float = 0.01) -> ModelSolution:
    """
    Solve the full SOG Stage-B model analytically.

    Defaults match the canonical operating point from 4.py:
        ρ=0.5, λ=0.5, σ_ε=0.1, σ_ζ=0.05, σ_d=0.1
    """
    fi = solve_floor(rho, lam, se2, sz2)
    fb = solve_floor(rho, lam, se2, sz2 + sd2)

    a = rho * (1 - lam * fb.K)
    # Var(e): the prediction-gap process between informed and blind
    # گاردِ لبه: |a|→1 (مثلاً |ρ|→1) مخرج را صفر می‌کند — کفِ کوچک به‌جای ZeroDivision
    var_e = ((rho * (fi.K - fb.K)) ** 2 * fi.S + sd2) / max(1 - a ** 2, 1e-12)

    return ModelSolution(
        rho=rho, lam=lam, se2=se2, sz2=sz2, sd2=sd2,
        P=fi.P, S=fi.S, K=fi.K,
        Pb=fb.P, Sb=fb.S, Kb=fb.K,
        a=a, var_e=var_e,
    )


def solve_from_stds(rho=0.5, lam=0.5, se=0.1, sz=0.05, sd=0.1) -> ModelSolution:
    """Convenience wrapper taking std-devs instead of variances."""
    return solve(rho=rho, lam=lam, se2=se*se, sz2=sz*sz, sd2=sd*sd)


# ════════════════════════════════════════════════════════════════════════
#  Grid sweep — Δ_self and E_shadow across the λ axis
# ════════════════════════════════════════════════════════════════════════

def lambda_grid(rho=0.5, se=0.1, sz=0.05, sd=0.1,
                lam_values=None) -> list[ModelSolution]:
    """Sweep the model across a λ grid. Defaults match the ledger grid."""
    if lam_values is None:
        lam_values = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    return [solve_from_stds(rho=rho, lam=l, se=se, sz=sz, sd=sd)
            for l in lam_values]


# ════════════════════════════════════════════════════════════════════════
#  Self-test: reproduce the anchor values from 4.py
# ════════════════════════════════════════════════════════════════════════

ANCHORS = {
    "P":         0.00325184,
    "S":         0.01081296,
    "P_blind":   0.01526172,
    "S_blind":   0.01381543,
    "Delta_self": 0.122520,
    "E_shadow":   0.012553,
    "sigma_z2":   0.0141667,
    "identity":   0.135073,
}


def run_self_test() -> dict:
    """
    Reproduce the anchor numbers from 4.py to verify our modular extraction
    is faithful. Returns a dict of {quantity: (computed, expected, rel_err)}.
    """
    sol = solve_from_stds()  # canonical operating point
    results = {}
    for name, expected in ANCHORS.items():
        computed = getattr(sol, name) if hasattr(sol, name) else sol.summary()[name]
        rel_err = abs(computed - expected) / max(abs(expected), 1e-15)
        results[name] = (computed, expected, rel_err)
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("SOG Stage-B model — self-test against 4.py anchors")
    print("=" * 60)
    results = run_self_test()
    all_pass = True
    for name, (comp, exp, err) in results.items():
        status = "✓ PASS" if err < 1e-4 else "✗ FAIL"
        if err >= 1e-4:
            all_pass = False
        print(f"  {name:12s}  computed={comp:.8f}  expected={exp:.8f}  "
              f"rel_err={err:.2e}  {status}")

    print("\n" + ("✓ ALL ANCHORS PASS — modular extraction is faithful."
                  if all_pass else "✗ SOME ANCHORS FAILED — check the math."))

    # Also cross-check closed-form vs iteration
    worst = 0.0
    rng = np.random.default_rng(7)
    for _ in range(300):
        rho = rng.uniform(0.0, 0.98)
        lam = rng.uniform(1e-3, 3.0)
        se2 = rng.uniform(1e-4, 1.0)
        sz2 = rng.uniform(1e-4, 1.0)
        pc = P_closed(rho, lam, se2, sz2)
        pi = P_iter(rho, lam, se2, sz2)
        worst = max(worst, abs(pc - pi) / pc)
    print(f"\nDARE closed vs iter (300 random draws), max rel err: {worst:.2e}")

    # Grid summary
    print("\nλ grid (Δ_self, E_shadow):")
    print(f"  {'λ':>4s}  {'g':>4s}  {'Δ_self':>10s}  {'E_shadow':>10s}  {'detectable':>10s}")
    for sol in lambda_grid():
        print(f"  {sol.lam:4.1f}  {2*sol.lam:4.1f}  {sol.Delta_self:10.4f}  "
              f"{sol.E_shadow:10.4f}  {str(sol.detectable):>10s}")
