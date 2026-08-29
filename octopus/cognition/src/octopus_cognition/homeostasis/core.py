"""Healthy-range homeostasis. Missing skill/calibration is UNKNOWN, never zero-filled."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from octopus_cognition.homeostasis.models import (
    HomeostaticMode,
    HomeostaticSnapshot,
    VariableReading,
    VariableSpec,
    VariableStatus,
    VitalSeverity,
)

DEFAULT_YAML = Path("/etc/octopus/homeostasis.yaml")

DEFAULT_SPECS: tuple[VariableSpec, ...] = (
    VariableSpec("compute_pressure", "cpu_utilisation", (0.0, 0.70), critical_high=0.90),
    VariableSpec("memory_pressure", "memory_used_ratio", (0.0, 0.75), critical_high=0.90),
    VariableSpec("thermal_integrity", "soc_temperature_celsius", (20.0, 70.0), critical_high=80.0, unit="celsius"),
    VariableSpec("storage_integrity", "disk_used_ratio", (0.0, 0.80), critical_high=0.92),
    VariableSpec("evidence_freshness", "evidence_age_seconds", (0.0, 15.0), critical_high=60.0, unit="s"),
    VariableSpec("sensor_coverage", "usable_active_over_expected", (0.90, 1.00), critical_low=0.70),
    VariableSpec("model_skill", "world_model_skill", (0.10, 1.00), critical_low=0.00),
    VariableSpec("prediction_calibration", "world_model_calibration_error", (0.00, 0.10), critical_high=0.25),
)

HOST_VARS = ("compute_pressure", "memory_pressure", "thermal_integrity", "storage_integrity")
DATA_VARS = ("evidence_freshness", "sensor_coverage")
MODEL_VARS = ("model_skill", "prediction_calibration")


def load_specs(path: Path | None = None) -> tuple[VariableSpec, ...]:
    target = path or DEFAULT_YAML
    if not target.is_file():
        return DEFAULT_SPECS
    doc = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    rows = doc.get("variables") or {}
    out: list[VariableSpec] = []
    for spec in DEFAULT_SPECS:
        name = spec.name
        raw = rows.get(name) or {}
        healthy = raw.get("healthy") or list(spec.healthy)
        out.append(
            VariableSpec(
                name=name,
                source=str(raw.get("source") or spec.source),
                healthy=(float(healthy[0]), float(healthy[1])),
                critical_high=_maybe_float(raw.get("critical_high"), spec.critical_high),
                critical_low=_maybe_float(raw.get("critical_low"), spec.critical_low),
                unit=spec.unit,
            )
        )
    return tuple(out)


def _maybe_float(value: Any, fallback: float | None) -> float | None:
    if value is None:
        return fallback
    return float(value)


def classify(spec: VariableSpec, value: float | None, stale: bool) -> VariableStatus:
    if value is None or stale:
        return VariableStatus.UNKNOWN
    lo, hi = spec.healthy
    if spec.critical_high is not None and value >= spec.critical_high:
        return VariableStatus.CRITICAL
    if spec.critical_low is not None and value <= spec.critical_low:
        return VariableStatus.CRITICAL
    if lo <= value <= hi:
        return VariableStatus.HEALTHY
    return VariableStatus.WATCH


def _excess(spec: VariableSpec, value: float) -> float:
    lo, hi = spec.healthy
    span = max(hi - lo, 1e-6)
    if value > hi:
        return (value - hi) / span
    if value < lo:
        return (lo - value) / span
    return 0.0


def evaluate(
    values: dict[str, float | None],
    *,
    stale: dict[str, bool] | None = None,
    stamps: dict[str, str | None] | None = None,
    raw: dict[str, float | None] | None = None,
    specs: tuple[VariableSpec, ...] | None = None,
    profile: str = "WAVE0_IDLE",
    version: int = 2,
) -> HomeostaticSnapshot:
    specs = specs or DEFAULT_SPECS
    stale = stale or {}
    stamps = stamps or {}
    raw = raw or {}
    readings: dict[str, VariableReading] = {}
    for spec in specs:
        value = values.get(spec.name)
        is_stale = bool(stale.get(spec.name, value is None))
        status = classify(spec, value, is_stale)
        readings[spec.name] = VariableReading(
            name=spec.name,
            value=None if status == VariableStatus.UNKNOWN else value,
            status=status,
            stale=is_stale or value is None,
            source=spec.source,
            stamp=stamps.get(spec.name),
            raw=raw.get(spec.name),
        )

    def _ok(names: tuple[str, ...]) -> bool:
        present = [readings[n] for n in names if n in readings]
        if len(present) != len(names):
            return False
        if any(r.status == VariableStatus.UNKNOWN for r in present):
            return False
        return all(r.status == VariableStatus.HEALTHY for r in present)

    host_in_range = _ok(HOST_VARS)
    data_ok = _ok(DATA_VARS)
    model_known = any(readings[n].status != VariableStatus.UNKNOWN for n in MODEL_VARS if n in readings)
    unknown = tuple(n for n, r in readings.items() if r.status == VariableStatus.UNKNOWN)

    host_excess = [
        _excess(spec, readings[spec.name].value)
        for spec in specs
        if spec.name in HOST_VARS and readings[spec.name].value is not None
    ]
    range_distance = (sum(x * x for x in host_excess) / len(host_excess)) ** 0.5 if host_excess else 0.0

    cpu = readings["compute_pressure"].value
    mem = readings["memory_pressure"].value
    pressures = [p for p in (cpu, mem) if p is not None]
    energy_ratio = 1.0 - max(pressures) if pressures else 1.0

    critical = any(r.status == VariableStatus.CRITICAL for r in readings.values() if r.name not in MODEL_VARS)
    watch = any(r.status == VariableStatus.WATCH for r in readings.values() if r.name not in MODEL_VARS)
    if critical:
        mode = HomeostaticMode.WOULD_LOCKDOWN
        severity = VitalSeverity.CRITICAL
    elif watch or not host_in_range or not data_ok:
        mode = HomeostaticMode.CONSERVE
        severity = VitalSeverity.WATCH
    else:
        mode = HomeostaticMode.NORMAL
        severity = VitalSeverity.HEALTHY

    return HomeostaticSnapshot(
        profile=profile,
        version=version,
        mode=mode,
        severity=severity,
        host_in_range=host_in_range,
        data_ok=data_ok,
        homeostasis_ok=host_in_range and data_ok,
        in_envelope=host_in_range,
        range_distance=range_distance,
        energy_ratio=max(0.0, min(1.0, energy_ratio)),
        evidence_age_s=readings["evidence_freshness"].value,
        sensor_coverage=readings["sensor_coverage"].value,
        variables=readings,
        unknown=unknown,
        note=(
            "WAVE0_IDLE uses healthy ranges, not attractive setpoints. "
            "model_skill/calibration stay UNKNOWN until 50 paired outcomes. "
            "Mode is advisory; WOULD_LOCKDOWN is never applied to the host as LOCKDOWN."
            + ("" if model_known else " Skill gates are not yet computable.")
        ),
    )
