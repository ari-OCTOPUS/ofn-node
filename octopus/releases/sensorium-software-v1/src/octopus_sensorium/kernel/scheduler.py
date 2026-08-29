"""Schedule windows come from the signed manifest. Plugins cannot exceed them."""

from __future__ import annotations


def interval_seconds(manifest: dict, default: float = 5.0) -> float:
    schedule = manifest.get("schedule") or {}
    raw = schedule.get("interval_seconds", default)
    try:
        interval = float(raw)
    except (TypeError, ValueError):
        interval = default
    minimum = float(schedule.get("minimum_interval_seconds", 1))
    maximum = float(schedule.get("maximum_interval_seconds", 3600))
    return min(max(interval, minimum), maximum)
