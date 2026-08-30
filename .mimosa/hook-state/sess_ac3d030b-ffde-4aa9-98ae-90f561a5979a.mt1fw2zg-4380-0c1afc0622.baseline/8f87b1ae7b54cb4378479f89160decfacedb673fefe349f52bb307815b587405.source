"""
core/simulator.py — Monte-Carlo simulator for the SOG model.

Reproduces and extends the simulation in 4.py (verify2_mc section):
generates the hidden state s and shadow observations Y, then computes
empirical statistics to confirm the analytical predictions.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from .model import solve_from_stds, ModelSolution


@dataclass
class SimulationResult:
    """Output of a single Monte-Carlo run."""
    s:      np.ndarray   # hidden state trajectory
    Y:      np.ndarray   # observed shadow
    z:      np.ndarray   # demeaned observation (Y - b)
    nu:     np.ndarray   # informed innovations
    nu_b:   np.ndarray   # blind innovations
    excess: np.ndarray   # per-step excess log-loss
    sol:    ModelSolution

    # empirical statistics
    emp_S:      float
    emp_Sb:     float
    emp_Delta:  float
    emp_Var_ex: float

    @property
    def corr_sq(self) -> float:
        """corr²(ν, ν_b) should ≈ S/S_b."""
        if len(self.nu) < 2:
            return 0.0
        c = np.corrcoef(self.nu, self.nu_b)[0, 1]
        return c * c


def simulate(rho=0.5, lam=0.5, se=0.1, sz=0.05, sd=0.1,
             T: int = 100_000, burn: int = 4000,
             seed: int | None = 0) -> SimulationResult:
    """
    Run the SOG Stage-B Monte-Carlo simulation.

    Generates:
        s(t+1) = ρ·s(t) + m(t) + ζ(t)       [hidden]
        Y(t)   = b(t) + λ·s(t) + ε(t)       [shadow]

    with private dither d(t) as the policy input m(t).
    """
    # B14: پیش‌فرضِ seed=۰ → MC به‌طورِ پیش‌فرض بازتولیدپذیر؛ seed=None یعنی
    # صریحاً غیرقطعی بخواه (default_rng(None) = آنتروپی OS).
    rng = np.random.default_rng(seed)

    sol = solve_from_stds(rho=rho, lam=lam, se=se, sz=sz, sd=sd)

    total = T + burn
    eps = rng.normal(0, se, total)   # observation noise
    zet = rng.normal(0, sz, total)   # process noise
    dit = rng.normal(0, sd, total)   # private dither

    K, Kb = sol.K, sol.Kb
    S, Sb = sol.S, sol.Sb
    lnr = sol.Delta_self

    # scalar state variables (exactly like 4.py)
    s = sh = shb = 0.0

    # post-burn-in arrays
    z_arr  = np.zeros(T)
    s_arr  = np.zeros(T)
    nu_arr  = np.zeros(T)
    nub_arr = np.zeros(T)
    ex_arr  = np.zeros(T)

    for t in range(total):
        z_t = lam * s + eps[t]           # b=0 (pure dither policy)
        nu  = z_t - lam * sh             # informed innovation
        nub = z_t - lam * shb            # blind innovation

        if t >= burn:
            i = t - burn
            z_arr[i]   = z_t
            s_arr[i]   = s
            nu_arr[i]  = nu
            nub_arr[i] = nub
            ex_arr[i]  = lnr + nub*nub/(2*Sb) - nu*nu/(2*S)

        m = dit[t]
        s   = rho * s + m + zet[t]       # advance hidden state
        sh  = rho * (sh + K * nu) + m    # informed: knows m incl. dither
        shb = rho * (shb + Kb * nub)     # blind: knows policy mean (0) only

    return SimulationResult(
        s=s_arr, Y=z_arr, z=z_arr,
        nu=nu_arr, nu_b=nub_arr, excess=ex_arr,
        sol=sol,
        emp_S=nu_arr.var(),
        emp_Sb=nub_arr.var(),
        emp_Delta=ex_arr.mean(),
        emp_Var_ex=ex_arr.var(),
    )


def verify_against_model(result: SimulationResult, tol: float = 0.05) -> dict:
    """
    Check that empirical MC statistics match the analytical model.
    Returns a dict of {check: (empirical, theoretical, passed)}.
    """
    sol = result.sol
    checks = {}

    checks["Var(ν) ≈ S"] = (result.emp_S, sol.S,
                             abs(result.emp_S - sol.S) / sol.S < tol)
    checks["Var(ν_b) ≈ S_b"] = (result.emp_Sb, sol.Sb,
                                 abs(result.emp_Sb - sol.Sb) / sol.Sb < tol)
    checks["mean(ex) ≈ Δ_self"] = (result.emp_Delta, sol.Delta_self,
                                    abs(result.emp_Delta - sol.Delta_self) < tol)
    checks["Var(ex) ≈ 1−S/S_b"] = (result.emp_Var_ex, sol.Var_ex,
                                    abs(result.emp_Var_ex - sol.Var_ex) / max(sol.Var_ex, 1e-10) < tol)
    checks["corr²(ν,ν_b) ≈ S/S_b"] = (result.corr_sq, sol.S / sol.Sb,
                                       abs(result.corr_sq - sol.S/sol.Sb) < tol)

    return checks


if __name__ == "__main__":
    print("=== SOG Monte-Carlo simulation (T=100k, seed=42) ===\n")
    result = simulate(T=100_000, seed=42)

    print(f"Analytical:  S={result.sol.S:.6f}  S_b={result.sol.Sb:.6f}  "
          f"Δ_self={result.sol.Delta_self:.6f}")
    print(f"Empirical:   S={result.emp_S:.6f}  S_b={result.emp_Sb:.6f}  "
          f"Δ_self={result.emp_Delta:.6f}")
    print(f"corr²(ν,ν_b)={result.corr_sq:.6f}  (theory S/S_b={result.sol.S/result.sol.Sb:.6f})")

    print("\n=== Verification checks ===")
    checks = verify_against_model(result)
    for name, (emp, thy, passed) in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {name}:  emp={emp:.6f}  thy={thy:.6f}")
