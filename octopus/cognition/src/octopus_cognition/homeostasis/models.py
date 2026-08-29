from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HomeostaticMode(StrEnum):
    """Advisory mode only. WOULD_LOCKDOWN is never applied to the host."""

    NORMAL = "normal"
    CONSERVE = "conserve"
    WOULD_LOCKDOWN = "would_lockdown"


class VitalSeverity(StrEnum):
    """Per-snapshot vital severity. Separate from HomeostaticMode."""

    HEALTHY = "healthy"
    WATCH = "watch"
    CRITICAL = "critical"


class VariableStatus(StrEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    WATCH = "watch"
    CRITICAL = "critical"


@dataclass(frozen=True)
class VariableSpec:
    name: str
    source: str
    healthy: tuple[float, float]
    critical_high: float | None = None
    critical_low: float | None = None
    unit: str = "1"


@dataclass(frozen=True)
class VariableReading:
    name: str
    value: float | None
    status: VariableStatus
    stale: bool
    source: str
    stamp: str | None = None
    raw: float | None = None


@dataclass(frozen=True)
class HomeostaticSnapshot:
    profile: str
    version: int
    mode: HomeostaticMode
    severity: VitalSeverity
    host_in_range: bool
    data_ok: bool
    homeostasis_ok: bool
    in_envelope: bool
    range_distance: float
    energy_ratio: float
    evidence_age_s: float | None
    sensor_coverage: float | None
    variables: dict[str, VariableReading]
    unknown: tuple[str, ...]
    note: str


def interpret_mode(value: str | HomeostaticMode | None) -> HomeostaticMode:
    """Map leftover protect/lockdown labels to advisory WOULD_LOCKDOWN."""
    raw = value.value if isinstance(value, HomeostaticMode) else str(value or "normal").lower()
    if raw in {"protect", "lockdown", "would_lockdown"}:
        return HomeostaticMode.WOULD_LOCKDOWN
    if raw == "conserve":
        return HomeostaticMode.CONSERVE
    return HomeostaticMode.NORMAL
