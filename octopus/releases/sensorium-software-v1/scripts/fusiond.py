#!/usr/bin/env python3
"""S1: Registry-100 runtime contract, sensor state machine, Fusion Frame v1.

Does not invent measurements for MANIFEST_ONLY / DISABLED / BLOCKED sensors.
Does not promote those sensors to ACTIVE. Does not run Doctor, Lab, or Release.
LLM is not on this path. Authority remains WAVE0_OBSERVE_ONLY.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from octopus_sensorium.clock import probe_clock
from octopus_sensorium.config_loader import load_board_and_registry

STATE = Path("/var/lib/octopus/state")
EVIDENCE = STATE / "evidence"
STABILITY = STATE / "stability" / "latest.json"
REG_DIR = STATE / "registry"
SENS_DIR = STATE / "sensors"
FUS_DIR = STATE / "fusion"
ARCH_DIR = STATE / "architecture"
FRESH_S = {"fast": 20.0, "normal": 45.0, "slow": 300.0}
TICK_S = 5.0
FRAMES_KEEP = 1000

# Evidence files produced by the live Wave 0 runtime. Never synthesize extras.
EVIDENCE_MAP = {
    "OCT-SENSE-051": ["last_OCT-SENSE-051.json"],
    "OCT-SENSE-052": ["last_OCT-SENSE-052.json"],
    "OCT-SENSE-053": [
        "last_OCT-SENSE-053_CPU.json",
        "last_OCT-SENSE-053_MEMORY.json",
        "last_OCT-SENSE-053_STORAGE.json",
    ],
    "OCT-SENSE-053.THERMAL": ["last_OCT-SENSE-053_THERMAL.json"],
    "OCT-SENSE-092": ["last_OCT-SENSE-092.json"],
    "OCT-SENSE-095": ["last_OCT-SENSE-095.json"],
}

RUNTIME_STATES = (
    "MANIFEST_ONLY",
    "DISCOVERED",
    "PROBING",
    "ACTIVE",
    "DEGRADED",
    "STALE",
    "FAILED",
    "QUARANTINED",
    "SHADOW",
    "DISABLED",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _monotonic_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


def _wall_ns() -> int:
    return time.time_ns()


def atomic_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _parse_time(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def observation_datetime(doc: dict[str, Any]) -> tuple[datetime | None, str]:
    """Host and meta evidence use different time fields. Never invent a stamp."""
    time_block = doc.get("time") or {}
    if isinstance(time_block, dict):
        for key in ("phenomenon_time", "ingestion_time", "processing_time"):
            dt = _parse_time(time_block.get(key))
            if dt:
                return dt, f"time.{key}"
    evidence = doc.get("evidence") or {}
    if isinstance(evidence, dict):
        dt = _parse_time(evidence.get("baseline_window_end"))
        if dt:
            return dt, "evidence.baseline_window_end"
    contradiction = doc.get("contradiction") or {}
    if isinstance(contradiction, dict):
        dt = _parse_time(contradiction.get("last_seen"))
        if dt:
            return dt, "contradiction.last_seen"
    return None, "MISSING_TIMESTAMP"


def is_shadow_spec(spec: dict[str, Any]) -> bool:
    return str(spec.get("status") or "").upper() == "SHADOW" or str(spec.get("mode") or "").lower() == "shadow"


def load_evidence(name: str) -> dict[str, Any] | None:
    path = EVIDENCE / name
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def supervisor_family(sensor: dict[str, Any]) -> str:
    sid = str(sensor.get("sensor_id") or "")
    fam = str(sensor.get("family") or "")
    if sid in {"OCT-SENSE-096", "OCT-SENSE-097", "OCT-SENSE-099", "OCT-SENSE-100"} or fam == "evolution":
        return "evolution"
    if fam == "meta":
        return "octopus_cognition"
    if fam == "security":
        return "security"
    if fam in {"network", "bus"}:
        return "network"
    if fam == "clock":
        return "data_integrity"
    if fam == "power" or sid.endswith(".THERMAL") or "thermal" in str(sensor.get("sensor_type") or "").lower():
        return "thermal_power"
    if sid == "OCT-SENSE-052" or "process" in str(sensor.get("sensor_type") or ""):
        return "services"
    if sid == "OCT-SENSE-051" or "filesystem" in str(sensor.get("sensor_type") or ""):
        return "storage"
    if "memory" in sid.lower():
        return "memory"
    if fam == "host":
        return "compute"
    return fam or "other"


def map_runtime_state(sensor: dict[str, Any], fresh: bool, has_evidence: bool, stale: bool) -> str:
    status = str(sensor.get("status") or "MANIFEST_ONLY")
    enabled = bool(sensor.get("enabled"))
    if status in {"DISABLED_BY_POLICY", "BLOCKED_CONSENT"}:
        return "DISABLED"
    if status == "QUARANTINED":
        return "QUARANTINED"
    if status == "discovered_unregistered":
        return "DISCOVERED"
    if not enabled:
        if status in {"BLOCKED_HARDWARE", "BLOCKED_NETWORK", "PLANNED", "MANIFEST_ONLY"}:
            return "MANIFEST_ONLY"
        return "DISABLED"
    if status == "SHADOW":
        if has_evidence and stale:
            return "STALE"
        return "SHADOW"
    if status == "ACTIVE" or enabled:
        if not has_evidence:
            return "PROBING"
        if stale:
            return "STALE"
        if fresh:
            return "SHADOW" if status == "SHADOW" else "ACTIVE"
        return "DEGRADED"
    return "MANIFEST_ONLY"


def freshness_class(sensor: dict[str, Any]) -> str:
    fam = supervisor_family(sensor)
    ttl = (sensor.get("freshness") or {}).get("ttl_seconds") if isinstance(sensor.get("freshness"), dict) else None
    # thermal_power was "fast" (20s) while stability_monitor uses 45s — THERMAL flapped STALE.
    if fam == "thermal_power":
        return "normal"
    if fam in {"compute", "memory"}:
        return "fast"
    if fam in {"network", "services"}:
        return "normal"
    if isinstance(ttl, (int, float)) and ttl <= 60:
        return "normal"
    return "slow"


def collect_measurement(sensor_id: str) -> tuple[Any, dict[str, Any], bool, bool, str | None]:
    """Return (measurement_or_none, quality, has_evidence, stale, stamp). Never returns 0 for missing."""
    files = EVIDENCE_MAP.get(sensor_id) or []
    parts: dict[str, Any] = {}
    stamps: list[datetime] = []
    any_doc = False
    for name in files:
        doc = load_evidence(name)
        if not doc:
            continue
        any_doc = True
        value = (doc.get("result") or {}).get("value")
        if value is None and doc.get("anomaly"):
            value = doc.get("anomaly")
        if value is None and doc.get("observation_type") in {"anomaly", "contradiction"}:
            value = {"observation_type": doc.get("observation_type"), "sensor_id": doc.get("sensor_id")}
        if value is None:
            continue
        key = name.replace("last_", "").replace(".json", "")
        parts[key] = {
            "value": value,
            "unit": (doc.get("result") or {}).get("unit"),
            "observed_property": doc.get("observed_property"),
            "quality_valid": (doc.get("quality") or {}).get("valid"),
            "time_unverified": (doc.get("quality") or {}).get("time_unverified"),
            "clock_trust": (doc.get("provenance") or {}).get("clock_trust"),
        }
        dt, _src = observation_datetime(doc)
        if dt:
            stamps.append(dt)
    if not any_doc or not parts:
        return None, {"state": "unavailable", "confidence": 0.0, "stale": True, "synthetic": False}, False, True, None
    newest = max(stamps) if stamps else None
    age = (_now() - newest).total_seconds() if newest else 1e9
    # Caller decides stale vs fresh using the sensor's window.
    measurement: Any
    if len(parts) == 1:
        measurement = next(iter(parts.values()))["value"]
    else:
        measurement = parts
    stamp = newest.isoformat() if newest else None
    quality = {"state": "measured", "confidence": 1.0, "stale": False, "synthetic": False, "age_s": round(age, 3)}
    return measurement, quality, True, age, stamp


def build_contract() -> dict[str, Any]:
    board, registry = load_board_and_registry()
    clock = probe_clock()
    sensors_out: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for spec in registry.document.get("sensors") or []:
        sid = spec["sensor_id"]
        window = freshness_class(spec)
        measurement, quality, has_ev, age_or_flag, stamp = collect_measurement(sid)
        age_s = float(age_or_flag) if has_ev and isinstance(age_or_flag, (int, float)) else None
        limit = FRESH_S[window]
        stale = (not has_ev) or (age_s is not None and age_s > limit)
        fresh = has_ev and age_s is not None and age_s <= limit
        runtime = map_runtime_state(spec, fresh=fresh, has_evidence=has_ev, stale=bool(stale and has_ev))
        if runtime in {"MANIFEST_ONLY", "DISABLED", "DISCOVERED", "QUARANTINED"}:
            measurement = None
            quality = {"state": "unavailable", "confidence": 0.0, "stale": True, "synthetic": False}
        heartbeat = {
            "schema": "octopus.sensor.heartbeat.v1",
            "sensor_id": sid,
            "family": spec.get("family"),
            "supervisor_family": supervisor_family(spec),
            "registry_status": spec.get("status"),
            "enabled": bool(spec.get("enabled")),
            "runtime_state": runtime,
            "measurement": measurement,
            "quality": quality,
            "synthetic": False,
            "freshness_class": window,
            "evidence_stamp": stamp,
            "plugin": (spec.get("plugin") or {}).get("type") if isinstance(spec.get("plugin"), dict) else None,
        }
        if heartbeat["runtime_state"] in {"MANIFEST_ONLY", "DISABLED", "DISCOVERED"} and heartbeat["measurement"] is not None:
            raise RuntimeError(f"refusing fake measurement for {sid}")
        sensors_out.append(heartbeat)
        counts[runtime] += 1

    expected_all = [
        s
        for s in sensors_out
        if s["enabled"] and s["runtime_state"] not in {"DISABLED", "MANIFEST_ONLY", "DISCOVERED", "QUARANTINED"}
    ]
    # WAVE0 coverage denominator is host sensors. Shadow meta (092/095) stay classified,
    # never imputed, and are not required for usable_active_over_expected.
    expected = [s for s in expected_all if str(s.get("registry_status") or "").upper() != "SHADOW"]
    producing = [
        s for s in expected if s.get("measurement") is not None and s["runtime_state"] in {"ACTIVE"}
    ]
    missing = [s["sensor_id"] for s in expected if s.get("measurement") is None]
    degraded = [s["sensor_id"] for s in expected if s["runtime_state"] in {"STALE", "DEGRADED", "FAILED"}]
    coverage = (len(producing) / len(expected)) if expected else 0.0
    stability = {}
    if STABILITY.is_file():
        try:
            stability = json.loads(STABILITY.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            stability = {}
    axes_ok = bool(stability) and not any((ax or {}).get("stale") for ax in (stability.get("axes") or {}).values())
    usable_homeo = clock.clock_trust == "SYNCED_NTP" and axes_ok and coverage >= 0.5
    frame = {
        "schema": "octopus.state-frame.v1",
        "frame_id": f"FRAME-{uuid.uuid4()}",
        "board_id": board.document.get("board", {}).get("board_id") or "sensorium-opi5pro-68e44cdf",
        "time_range_ns": [_wall_ns() - int(TICK_S * 1e9), _wall_ns()],
        "captured_monotonic_ns": _monotonic_ns(),
        "published_wall_ns": _wall_ns(),
        "coverage": round(coverage, 4),
        "active_sensors": len(producing),
        "expected_sensors": len(expected),
        "missing": missing,
        "degraded": degraded,
        "clock_trust": clock.clock_trust,
        "usable_for_homeostasis": usable_homeo,
        "usable_for_training": False,
        "missing_policy": "mark_unknown",
        "synthetic_measurements": 0,
        "registry_version": registry.document.get("config_version"),
        "registry_hash": registry.payload_hash,
        "authority": "observe_only",
        "homeostasis_distance": stability.get("distance"),
        "homeostasis_in_envelope": stability.get("in_envelope"),
    }
    contract = {
        "schema": "octopus.registry-runtime-contract.v1",
        "timestamp": _now().isoformat(),
        "board_id": frame["board_id"],
        "registry_version": frame["registry_version"],
        "registry_hash": frame["registry_hash"],
        "registry_signed": True,
        "sensor_count": len(sensors_out),
        "runtime_counts": dict(counts),
        "enabled_count": sum(1 for s in sensors_out if s["enabled"]),
        "note": "Registry-100 means defined, not all producing. MANIFEST_ONLY emits heartbeat only.",
        "supervisors": dict(Counter(s["supervisor_family"] for s in sensors_out)),
        "clock": clock.as_dict(),
    }
    return {"contract": contract, "sensors": sensors_out, "frame": frame, "clock": clock.as_dict()}


def persist(bundle: dict[str, Any]) -> None:
    atomic_write(REG_DIR / "active.json", bundle["contract"])
    atomic_write(SENS_DIR / "latest.json", {"timestamp": bundle["contract"]["timestamp"], "sensors": bundle["sensors"]})
    atomic_write(
        SENS_DIR / "health.json",
        {
            "timestamp": bundle["contract"]["timestamp"],
            "counts": bundle["contract"]["runtime_counts"],
            "by_id": {s["sensor_id"]: s["runtime_state"] for s in bundle["sensors"]},
        },
    )
    atomic_write(FUS_DIR / "latest-frame.json", bundle["frame"])
    frames_path = FUS_DIR / "frames.jsonl"
    frames_path.parent.mkdir(parents=True, exist_ok=True)
    with frames_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(bundle["frame"], separators=(",", ":"), ensure_ascii=False) + "\n")
    try:
        lines = frames_path.read_text(encoding="utf-8").splitlines()
        if len(lines) > FRAMES_KEEP:
            frames_path.write_text("\n".join(lines[-FRAMES_KEEP:]) + "\n", encoding="utf-8")
    except OSError:
        pass
    atomic_write(
        ARCH_DIR / "s1-status.json",
        {
            "phase": "S1",
            "next_forbidden": ["doctor_auto_patch", "A3", "A4", "A5", "fake_manifest_measurements"],
            "daily_change_budget": {"max_promotions": 1, "max_modules_changed": 1},
            "frame_id": bundle["frame"]["frame_id"],
            "usable_for_homeostasis": bundle["frame"]["usable_for_homeostasis"],
            "usable_for_training": False,
        },
    )


def assert_no_fake_measurements(sensors: list[dict[str, Any]]) -> None:
    for item in sensors:
        if item["runtime_state"] in {"MANIFEST_ONLY", "DISABLED", "DISCOVERED", "QUARANTINED"}:
            if item.get("measurement") is not None or item.get("synthetic") is True:
                raise RuntimeError(f"fake data for {item['sensor_id']}")


def main() -> int:
    once = "--once" in sys.argv
    for path in (REG_DIR, SENS_DIR, FUS_DIR, ARCH_DIR):
        path.mkdir(parents=True, exist_ok=True)
    while True:
        bundle = build_contract()
        assert_no_fake_measurements(bundle["sensors"])
        persist(bundle)
        if once:
            print(
                json.dumps(
                    {
                        "sensors": bundle["contract"]["sensor_count"],
                        "counts": bundle["contract"]["runtime_counts"],
                        "coverage": bundle["frame"]["coverage"],
                        "missing": bundle["frame"]["missing"],
                        "clock": bundle["frame"]["clock_trust"],
                        "usable_for_homeostasis": bundle["frame"]["usable_for_homeostasis"],
                    }
                )
            )
            return 0
        time.sleep(TICK_S)


if __name__ == "__main__":
    raise SystemExit(main())
