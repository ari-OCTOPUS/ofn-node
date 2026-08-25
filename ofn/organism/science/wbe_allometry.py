"""West-Brown-Enquist / Savage allometry as analysis only.

Do not import this module from homeostasis, soak abort, or systemd units.
Exponents are scientific claims, not board safety trips.
"""

from __future__ import annotations

from typing import Any

KLEIBER_EXPONENT = 0.75
SAVAGE_OLS_EXPONENT = 0.81
WEST_INFINITE_SIZE = 0.75

# Specific metabolic rate: f ∝ C^{α−1}
SPECIFIC_KLEIBER = KLEIBER_EXPONENT - 1.0  # -0.25
SPECIFIC_SAVAGE = SAVAGE_OLS_EXPONENT - 1.0  # -0.19
SPECIFIC_085 = 0.85 - 1.0  # -0.15

EXECUTABLE = False
SAFETY_BIND_FORBIDDEN = True


def specific_rate_exponent(alpha: float) -> float:
    return float(alpha) - 1.0


def finite_size_note() -> dict[str, Any]:
    return {
        "wbe_1997": {
            "assumptions": [
                "space_filling",
                "invariant_terminals",
                "min_dissipation",
            ],
            "B_scaling": "M^{3/4}",
            "regime": "infinite_size_limit",
        },
        "savage_2008": {
            "tree": "mixed",
            "mass_decades": 8,
            "ols_a": SAVAGE_OLS_EXPONENT,
            "relation_to_kleiber": "at_odds",
            "curvature": "opposite_empirical_convexity",
        },
        "specific_rate": {
            "form": "f ∝ C^{α−1}",
            "kleiber_0.75": SPECIFIC_KLEIBER,
            "savage_0.81": SPECIFIC_SAVAGE,
            "alpha_0.85": SPECIFIC_085,
        },
        "executable": EXECUTABLE,
        "use_as_octopus_safety_trip": False,
        "use_as_timer_or_halt_threshold": False,
    }


def analysis_report() -> dict[str, Any]:
    note = finite_size_note()
    note["claim_level"] = "LITERATURE"
    note["board_binding"] = "NONE"
    return note
