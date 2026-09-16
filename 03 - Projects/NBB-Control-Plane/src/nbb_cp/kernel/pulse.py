"""Allostatic pulse — epoch length as a function of pressure, not a fixed clock.

The charter forbids "heart as clock": inputs modulate the rhythm parameter,
never the phase. Under pressure (fast burn, near deadline, anomalies) the
system beats faster; when calm it slows toward base metabolism. The factor is
smooth, strictly decreasing in pressure, and clamped so the pulse can neither
race away nor flatline.
"""

from __future__ import annotations

MIN_FACTOR = 0.25
MAX_FACTOR = 4.0


def epoch_length_seconds(
    base_seconds: float,
    spend_velocity: float = 0.0,       # fraction of headroom burned per epoch, 0..1+
    deadline_proximity: float = 0.0,   # 0 = far, 1 = due now
    anomaly_pressure: float = 0.0,     # 0 = calm, 1 = incident storm
) -> float:
    if base_seconds <= 0:
        raise ValueError("base_seconds must be positive")
    pressure = max(0.0, spend_velocity) + max(0.0, deadline_proximity) + max(0.0, anomaly_pressure)
    # 2.0x base at zero pressure (resting metabolism), 1.0x at pressure 0.5,
    # halving per further unit of pressure; clamped to [MIN, MAX].
    factor = 2.0 ** (1.0 - 2.0 * pressure)
    factor = min(MAX_FACTOR, max(MIN_FACTOR, factor))
    return base_seconds * factor
