"""
core/metrics.py — Information-theoretic metrics derived from the model.

These functions take either a ModelSolution or raw data and compute the
quantities that the agents interpret as "signatures of a hidden dimension":
    E_shadow  — can an outside observer tell a hidden dimension exists?
    Δ_self    — value of first-person access
    I_pred    — total predictive information (excess entropy)
"""
from __future__ import annotations

import numpy as np
from .model import ModelSolution, solve_from_stds


# ════════════════════════════════════════════════════════════════════════
#  I_pred — predictive information (excess entropy) series
# ════════════════════════════════════════════════════════════════════════

def compute_I_pred(rho=0.5, lam=0.5, se=0.1, sz=0.05, sd=0.1,
                   n_terms: int = 50) -> dict:
    """
    Compute I_pred = ½·Σ_{L≥0} log(S_L / S_b) via Riccati iteration.

    This is the Bialek–Nemenman–Tishby predictive information. For ARMA(1,1)
    (our case when λρ≠0), I_pred > E_shadow strictly.

    Returns dict with: terms (list), total, first_term (=E_shadow), ratio.
    """
    from .model import P_closed
    se2, sz2, sd2 = se*se, sz*sz, sd*sd
    szp2 = sz2 + sd2

    P0 = szp2 / (1 - rho*rho)  # Var(s) with augmented noise
    P_L = P0
    terms = []
    for L in range(n_terms):
        S_L = lam*lam * P_L + se2
        S_b = lam*lam * P_closed(rho, lam, se2, szp2) + se2
        term = 0.5 * np.log(S_L / S_b) if S_b > 0 else 0.0
        terms.append(term)
        # advance Riccati
        P_L = rho*rho * P_L * se2 / S_L + szp2
        if abs(term) < 1e-12:
            break

    total = sum(terms)
    # geometric decay rate
    decay = terms[1] / terms[0] if len(terms) > 1 and terms[0] != 0 else 0.0

    return {
        "terms":  terms,
        "total":  total,
        "first":  terms[0] if terms else 0.0,  # = E_shadow
        "ratio":  total / terms[0] if terms and terms[0] > 0 else 0.0,
        "decay":  decay,
    }


# ════════════════════════════════════════════════════════════════════════
#  Empirical metrics — computed from raw time series
# ════════════════════════════════════════════════════════════════════════

def empirical_shadow(series: np.ndarray, max_lag: int = 10) -> dict:
    """
    Estimate the 'shadow' structure of an arbitrary time series:
    how much does the past tell us about the future?

    This is an EMPIRICAL proxy for E_shadow — it measures temporal redundancy
    without assuming the SOG model. Uses autocorrelation structure.

    A series with hidden-state structure (ρ≠0, λ≠0) will show positive
    temporal MI; pure noise will show ≈0.
    """
    series = np.asarray(series, dtype=float)
    series = series - series.mean()
    var = series.var()
    if var < 1e-15:
        return {"temporal_mi": 0.0, "autocorr": [0.0]*max_lag,
                "verdict": "flat (no signal)"}

    # autocorrelation
    acf = []
    for k in range(1, max_lag + 1):
        c = np.mean(series[:-k] * series[k:]) / var if k < len(series) else 0.0
        acf.append(c)

    # crude temporal MI estimate: −½·log(1 − ρ²) at lag-1 (Gaussian assumption)
    rho1 = acf[0] if acf else 0.0
    rho1 = max(-0.999, min(0.999, rho1))
    temporal_mi = -0.5 * np.log(1 - rho1**2) if abs(rho1) < 0.999 else 10.0

    # integrated autocorrelation (effective memory length)
    iac = sum(acf) if acf else 0.0

    if temporal_mi < 0.001:
        verdict = "iid-like (no hidden dimension visible)"
    elif temporal_mi < 0.01:
        verdict = "weak shadow (barely detectable)"
    elif temporal_mi < 0.1:
        verdict = "moderate shadow (hidden structure present)"
    else:
        verdict = "strong shadow (clear hidden-state dynamics)"

    return {
        "temporal_mi": temporal_mi,
        "autocorr":    acf,
        "lag1_rho":    rho1,
        "memory_len":  iac,
        "verdict":     verdict,
    }


def fit_shadow_parameters(series: np.ndarray) -> dict:
    """
    Fit the SOG shadow model parameters to an empirical series via
    method-of-moments. Returns estimated ρ, λ-equivalent, and the
    implied E_shadow / Δ_self.

    This is the key function that connects RAW DATA to the model.
    """
    series = np.asarray(series, dtype=float)
    series = series - series.mean()

    n = len(series)
    if n < 20:
        return {"error": "series too short (need ≥20 points)"}

    var_y = series.var()
    if var_y < 1e-15:
        return {"error": "zero-variance series"}

    # lag-1 autocorrelation → estimate ρ
    rho_hat = np.mean(series[:-1] * series[1:]) / var_y
    rho_hat = max(-0.98, min(0.98, rho_hat))

    # For the SOG model: Var(z) = λ²σ_ζ'²/(1−ρ²) + σ_ε²
    # and lag-1 autocorr of an AR(1)+noise is approximately ρ·σ_signal²/var_total
    # We estimate the "signal fraction" = how much of variance is structured
    signal_frac = abs(rho_hat)  # crude estimate

    # implied E_shadow proxy
    if abs(rho_hat) > 0.001:
        e_shadow_proxy = -0.5 * np.log(1 - rho_hat**2)
    else:
        e_shadow_proxy = 0.0

    # classify detectability
    detectable = abs(rho_hat) > 0.05

    return {
        "rho_hat":       rho_hat,
        "signal_frac":   signal_frac,
        "var_y":         var_y,
        "E_shadow_proxy": e_shadow_proxy,
        "detectable":    detectable,
        "n_points":      n,
        "classification": (
            "hidden dimension DETECTED (λρ≠0 equivalent)"
            if detectable else
            "no detectable hidden structure (≈iid)"
        ),
    }


# ════════════════════════════════════════════════════════════════════════
#  Report card — assemble a complete experiment summary
# ════════════════════════════════════════════════════════════════════════

def build_report_card(series: np.ndarray, source_label: str = "",
                      op_point=None) -> dict:
    """
    Assemble a complete 'experiment report card' for a time series:
    empirical analysis + model-theoretic interpretation.
    """
    shadow = empirical_shadow(series)
    fit    = fit_shadow_parameters(series)

    # theoretical model at canonical point (for comparison)
    sol = op_point if op_point else solve_from_stds()
    ipred = compute_I_pred()

    return {
        "source":        source_label,
        "n_points":      len(series),
        "empirical":     shadow,
        "fit":           fit,
        "model_anchor":  sol.summary(),
        "I_pred":        ipred,
        "verdict":       fit.get("classification", "unknown"),
    }


if __name__ == "__main__":
    # Quick test with synthetic AR(1) data
    rng = np.random.default_rng(42)
    n = 10000
    rho_true = 0.7
    s = np.zeros(n)
    for t in range(1, n):
        s[t] = rho_true * s[t-1] + rng.normal(0, 0.1)
    s += rng.normal(0, 0.3, n)  # add observation noise

    print("=== Empirical shadow analysis (AR(1) with noise) ===")
    r = build_report_card(s, "synthetic AR(1) ρ=0.7")
    print(f"  source: {r['source']}")
    print(f"  n_points: {r['n_points']}")
    print(f"  empirical MI: {r['empirical']['temporal_mi']:.4f}")
    print(f"  fit ρ_hat: {r['fit']['rho_hat']:.4f}  (true=0.7)")
    print(f"  E_shadow proxy: {r['fit']['E_shadow_proxy']:.4f}")
    print(f"  verdict: {r['verdict']}")

    print("\n=== I_pred series (canonical point) ===")
    ip = r["I_pred"]
    print(f"  terms: {[f'{t:.6f}' for t in ip['terms'][:5]]}")
    print(f"  total I_pred: {ip['total']:.6f}")
    print(f"  ratio (I_pred/E_shadow): {ip['ratio']:.3f}")
