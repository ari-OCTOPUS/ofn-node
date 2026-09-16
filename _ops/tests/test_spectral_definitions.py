#!/usr/bin/env python3
"""test_spectral_definitions.py -- Versioned spectral definition tests.

Covers:
  (a) Legacy sigma anchors unchanged (formula, cap, eps).
  (b) connectivity_ratio_v2: bounds [0,1]; path < complete; None guards.
  (c) Disconnected / tiny / non-finite inputs return None.
  (d) SpectralMetrics and CriticalitySnapshot expose separate metric names.
"""
from __future__ import annotations

import sys
from math import inf, nan
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("spectral_definitions")
_REAL_DOCTOR = harness.SELF_OPS / "doctor"
if str(_REAL_DOCTOR) not in sys.path:
    sys.path.insert(0, str(_REAL_DOCTOR))

from spectral_definitions import (  # noqa: E402
    FORMULA_CONNECTIVITY_RATIO_V2,
    FORMULA_LEGACY_SIGMA,
    LEGACY_EPS,
    LEGACY_SIGMA_CAP,
    compute_connectivity_ratio_v2,
    compute_legacy_sigma,
)


# ---------------------------------------------------------------------------
# Legacy sigma anchors
# ---------------------------------------------------------------------------

def t_legacy_sigma_formula_id():
    """Legacy formula identifier is the expected string."""
    assert FORMULA_LEGACY_SIGMA == "legacy_sigma.v1"


def t_legacy_sigma_constants():
    """Cap = 10.0 and eps = 1e-9 match historical values."""
    assert LEGACY_SIGMA_CAP == 10.0
    assert LEGACY_EPS == 1e-6


def t_legacy_sigma_basic():
    """Standard case: lambda_max=6, lambda_2=2 -> sigma = 6/(2+eps) ~ 3.0."""
    result = compute_legacy_sigma(2.0, 6.0)
    assert result is not None
    assert abs(result - 3.0) < 1e-4  # eps=1e-6 historical


def t_legacy_sigma_capped():
    """sigma is capped at 10 even when lambda_max/lambda_2 is huge."""
    result = compute_legacy_sigma(0.1, 100.0)
    assert result is not None
    assert result == 10.0


def t_legacy_sigma_one_to_one():
    """When lambda_max == lambda_2, sigma ~ 1.0."""
    result = compute_legacy_sigma(3.0, 3.0)
    assert result is not None
    assert abs(result - 1.0) < 1e-4  # eps=1e-6 historical


# ---------------------------------------------------------------------------
# connectivity_ratio_v2 basics
# ---------------------------------------------------------------------------

def t_connectivity_ratio_v2_formula_id():
    """V2 formula identifier is the expected string."""
    assert FORMULA_CONNECTIVITY_RATIO_V2 == "connectivity_ratio_v2.v1"


def t_connectivity_ratio_v2_basic():
    """lambda_2=2, lambda_max=6 -> ratio = 2/(6+eps) ~ 1/3."""
    result = compute_connectivity_ratio_v2(2.0, 6.0)
    assert result is not None
    assert abs(result - 1.0 / 3.0) < 1e-4  # eps=1e-6


def t_connectivity_ratio_v2_bounds_zero():
    """lambda_2 نزدیکِ صفر = disconnected/UNKNOWN، نه صفر جعلی."""
    assert compute_connectivity_ratio_v2(1e-12, 10.0) is None


def t_connectivity_ratio_v2_bounds_one():
    """lambda_2 == lambda_max -> ratio ~ 1.0 (upper bound)."""
    result = compute_connectivity_ratio_v2(5.0, 5.0)
    assert result is not None
    assert abs(result - 1.0) < 1e-4  # eps=1e-6


def t_connectivity_ratio_v2_upper_clamp():
    """Even if lambda_2 > lambda_max (shouldn't happen), result is clamped to 1."""
    result = compute_connectivity_ratio_v2(100.0, 1.0)
    assert result is not None
    assert result == 1.0


# ---------------------------------------------------------------------------
# Graph-theoretic ordering: path graph ratio < complete graph ratio
# ---------------------------------------------------------------------------

def t_path_graph_ratio_lt_complete_graph():
    """Algebraic connectivity of a path graph is lower than complete graph,
    so connectivity_ratio_v2 should be strictly smaller for the path."""
    # Path graph P_4: eigenvalues of L = {0, 2-sqrt(2), 2, 2+sqrt(2)}
    # lambda_2(P_4) = 2 - sqrt(2) ~ 0.5858, lambda_max(P_4) = 2+sqrt(2) ~ 3.4142
    path_l2 = 2.0 - 2.0 ** 0.5
    path_lmax = 2.0 + 2.0 ** 0.5

    # Complete graph K_4: eigenvalues of L = {0, 4, 4, 4}
    # lambda_2(K_4) = 4, lambda_max(K_4) = 4
    comp_l2 = 4.0
    comp_lmax = 4.0

    path_ratio = compute_connectivity_ratio_v2(path_l2, path_lmax)
    comp_ratio = compute_connectivity_ratio_v2(comp_l2, comp_lmax)

    assert path_ratio is not None
    assert comp_ratio is not None
    assert path_ratio < comp_ratio, (
        f"path ratio {path_ratio} should be < complete ratio {comp_ratio}"
    )


# ---------------------------------------------------------------------------
# None guards: disconnected, tiny, non-finite
# ---------------------------------------------------------------------------

def t_legacy_sigma_none_on_both_none():
    """Both inputs None -> None."""
    assert compute_legacy_sigma(None, None) is None


def t_legacy_sigma_none_on_lambda_max_zero():
    """lambda_max == 0 -> None (degenerate)."""
    assert compute_legacy_sigma(1.0, 0.0) is None


def t_legacy_sigma_none_on_lambda_max_negative():
    """lambda_max < 0 -> None."""
    assert compute_legacy_sigma(1.0, -5.0) is None


def t_legacy_sigma_none_on_tiny_lambda_2():
    """lambda_2 extremely small (disconnected) -> None."""
    assert compute_legacy_sigma(1e-15, 5.0) is None


def t_legacy_sigma_none_on_nan():
    """NaN inputs -> None."""
    assert compute_legacy_sigma(nan, 5.0) is None
    assert compute_legacy_sigma(1.0, nan) is None


def t_legacy_sigma_none_on_inf():
    """Inf inputs -> None."""
    assert compute_legacy_sigma(inf, 5.0) is None
    assert compute_legacy_sigma(1.0, inf) is None


def t_connectivity_ratio_v2_none_on_both_none():
    """Both inputs None -> None."""
    assert compute_connectivity_ratio_v2(None, None) is None


def t_connectivity_ratio_v2_none_on_lambda_max_zero():
    """lambda_max == 0 -> None."""
    assert compute_connectivity_ratio_v2(1.0, 0.0) is None


def t_connectivity_ratio_v2_none_on_lambda_max_negative():
    """lambda_max < 0 -> None."""
    assert compute_connectivity_ratio_v2(1.0, -5.0) is None


def t_connectivity_ratio_v2_none_on_nan():
    """NaN inputs -> None."""
    assert compute_connectivity_ratio_v2(nan, 5.0) is None
    assert compute_connectivity_ratio_v2(1.0, nan) is None


def t_connectivity_ratio_v2_none_on_inf():
    """Inf inputs -> None."""
    assert compute_connectivity_ratio_v2(inf, 5.0) is None
    assert compute_connectivity_ratio_v2(1.0, inf) is None


def t_connectivity_ratio_v2_rejects_tiny_lambda_2():
    """V2 روی گراف disconnected/tiny باید UNKNOWN بماند."""
    assert compute_connectivity_ratio_v2(1e-15, 5.0) is None


# ---------------------------------------------------------------------------
# SpectralMetrics and CriticalitySnapshot expose separate names
# ---------------------------------------------------------------------------

def t_spectral_metrics_exposes_connectivity_ratio_v2():
    """SpectralMetrics has connectivity_ratio_v2 field, defaults to None."""
    from spectral_metrics import SpectralMetrics
    sm = SpectralMetrics(
        node_count=3, edge_count=2, spectral_radius=1.0,
        lambda_2=0.5, lambda_max=2.0, sigma_heuristic=4.0,
        confidence="HIGH", connectivity_ratio_v2=None,
    )
    assert hasattr(sm, "connectivity_ratio_v2")
    assert sm.connectivity_ratio_v2 is None


def t_criticality_snapshot_exposes_connectivity_ratio_v2():
    """CriticalitySnapshot has connectivity_ratio_v2 field, defaults to None."""
    from criticality_v2 import CriticalitySnapshot
    snap = CriticalitySnapshot(
        spectral_radius=None, activity_variance=0.0,
        spectral_heuristic=None, lambda_2=None, lambda_max=None,
        c_t=None, confidence="NONE", measurement_status="UNKNOWN",
    )
    assert hasattr(snap, "connectivity_ratio_v2")
    assert snap.connectivity_ratio_v2 is None


def t_criticality_snapshot_metrics_exports_v2():
    """CriticalitySnapshot.metrics() includes the v2 key with a separate name."""
    from criticality_v2 import CriticalitySnapshot
    snap = CriticalitySnapshot(
        spectral_radius=1.0, activity_variance=0.1,
        spectral_heuristic=2.0, lambda_2=0.5, lambda_max=2.0,
        c_t=0.5, confidence="HIGH", connectivity_ratio_v2=0.25,
    )
    m = snap.metrics()
    assert "octopus.spectral.connectivity_ratio_v2" in m
    assert m["octopus.spectral.connectivity_ratio_v2"] == 0.25
    # Legacy name is untouched
    assert "octopus.spectral.sigma_legacy" in m
    assert m["octopus.spectral.sigma_legacy"] == 2.0


# ---------------------------------------------------------------------------
# estimate_sigma in spectral.py still works with delegation
# ---------------------------------------------------------------------------

def t_estimate_sigma_delegation_unchanged():
    """estimate_sigma still returns the same float as before for known inputs."""
    from spectral import estimate_sigma
    # Same test as in test_spectral.py: [0.0, 0.5, 2.0]
    sigma = estimate_sigma([0.0, 0.5, 2.0])
    assert 0 < sigma <= 10.0
    # Historical value: lambda_max=2, lambda_2=0.5 => 2/(0.5+1e-9) ~ 4.0
    assert abs(sigma - 4.0) < 1e-3


def t_estimate_sigma_empty_returns_zero():
    """Empty eigvals -> 0.0 (preserved from original)."""
    from spectral import estimate_sigma
    assert estimate_sigma([]) == 0.0


# ---------------------------------------------------------------------------
# No new dependencies
# ---------------------------------------------------------------------------

def t_spectral_definitions_no_heavy_deps():
    """spectral_definitions.py has no numpy/networkx/etc. imports."""
    src = Path(_REAL_DOCTOR, "spectral_definitions.py").read_text(encoding="utf-8")
    forbidden = ["import numpy", "import networkx", "from numpy", "from networkx",
                 "import scipy", "from scipy"]
    for f in forbidden:
        assert f not in src, f"forbidden import {f} found in spectral_definitions.py"


if __name__ == "__main__":
    failed = harness.run([
        ("[SD] legacy formula ID", t_legacy_sigma_formula_id),
        ("[SD] legacy constants (cap, eps)", t_legacy_sigma_constants),
        ("[SD] legacy sigma basic", t_legacy_sigma_basic),
        ("[SD] legacy sigma capped at 10", t_legacy_sigma_capped),
        ("[SD] legacy sigma one-to-one ~1", t_legacy_sigma_one_to_one),
        ("[SD] v2 formula ID", t_connectivity_ratio_v2_formula_id),
        ("[SD] v2 ratio basic ~1/3", t_connectivity_ratio_v2_basic),
        ("[SD] v2 ratio lower bound ~0", t_connectivity_ratio_v2_bounds_zero),
        ("[SD] v2 ratio upper bound ~1", t_connectivity_ratio_v2_bounds_one),
        ("[SD] v2 ratio clamped at 1", t_connectivity_ratio_v2_upper_clamp),
        ("[SD] path ratio < complete ratio", t_path_graph_ratio_lt_complete_graph),
        ("[SD] legacy sigma None on both None", t_legacy_sigma_none_on_both_none),
        ("[SD] legacy sigma None on lambda_max=0", t_legacy_sigma_none_on_lambda_max_zero),
        ("[SD] legacy sigma None on lambda_max<0", t_legacy_sigma_none_on_lambda_max_negative),
        ("[SD] legacy sigma None on tiny lambda_2", t_legacy_sigma_none_on_tiny_lambda_2),
        ("[SD] legacy sigma None on NaN", t_legacy_sigma_none_on_nan),
        ("[SD] legacy sigma None on Inf", t_legacy_sigma_none_on_inf),
        ("[SD] v2 ratio None on both None", t_connectivity_ratio_v2_none_on_both_none),
        ("[SD] v2 ratio None on lambda_max=0", t_connectivity_ratio_v2_none_on_lambda_max_zero),
        ("[SD] v2 ratio None on lambda_max<0", t_connectivity_ratio_v2_none_on_lambda_max_negative),
        ("[SD] v2 ratio None on NaN", t_connectivity_ratio_v2_none_on_nan),
        ("[SD] v2 ratio None on Inf", t_connectivity_ratio_v2_none_on_inf),
        ("[SD] v2 ratio rejects tiny lambda_2", t_connectivity_ratio_v2_rejects_tiny_lambda_2),
        ("[SD] SpectralMetrics exposes v2", t_spectral_metrics_exposes_connectivity_ratio_v2),
        ("[SD] CriticalitySnapshot exposes v2", t_criticality_snapshot_exposes_connectivity_ratio_v2),
        ("[SD] CriticalitySnapshot.metrics() exports v2", t_criticality_snapshot_metrics_exports_v2),
        ("[SD] estimate_sigma delegation unchanged", t_estimate_sigma_delegation_unchanged),
        ("[SD] estimate_sigma empty -> 0.0", t_estimate_sigma_empty_returns_zero),
        ("[SD] spectral_definitions has no heavy deps", t_spectral_definitions_no_heavy_deps),
    ])
    sys.exit(1 if failed else 0)
