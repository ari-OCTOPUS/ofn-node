"""Classify coverage as freshness, missing series, or validity. Never impute."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVIDENCE_DIR = Path("/var/lib/octopus/state/evidence")
SENSORS_LATEST = Path("/var/lib/octopus/state/sensors/latest.json")
FUSION_FRAME = Path("/var/lib/octopus/state/fusion/latest-frame.json")

# Host sensors required for WAVE0 homeostasis. Shadow meta sensors are not
# in this set — counting them as expected was a registration/evidence-path
# error, not a reason to fill them as healthy.
WAVE0_REQUIRED_IDS = (
    "OCT-SENSE-051",
    "OCT-SENSE-052",
    "OCT-SENSE-053",
    "OCT-SENSE-053.THERMAL",
)
SHADOW_OPTIONAL_IDS = ("OCT-SENSE-092", "OCT-SENSE-095")

# Align thermal/host windows with stability_monitor.FRESH_S (45s), not fusiond's
# 20s "fast" class which flaps THERMAL to STALE while stability still treats it fresh.
HOST_FRESH_S = 45.0
EVENT_DRIVEN_IDS = {"OCT-SENSE-092", "OCT-SENSE-095"}

EVIDENCE_FILES = {
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


def _parse_time(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def observation_datetime(doc: dict[str, Any]) -> tuple[datetime | None, str]:
    """Extract a timestamp from host or meta evidence. Never invent a value."""
    time_block = doc.get("time") or {}
    for key in ("phenomenon_time", "ingestion_time", "processing_time"):
        dt = _parse_time(time_block.get(key) if isinstance(time_block, dict) else None)
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


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def classify_sensor(sensor_id: str, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    names = EVIDENCE_FILES.get(sensor_id) or [f"last_{sensor_id}.json"]
    docs: list[tuple[Path, dict[str, Any]]] = []
    for name in names:
        path = EVIDENCE_DIR / name
        if not path.is_file():
            continue
        doc = load_json(path)
        if doc:
            docs.append((path, doc))
    if not docs:
        return {
            "sensor_id": sensor_id,
            "class": "missing_series",
            "usable": False,
            "age_s": None,
            "time_source": None,
            "paths": [str(EVIDENCE_DIR / n) for n in names],
            "reason": "no_evidence_file",
        }
    ages: list[float] = []
    sources: list[str] = []
    invalid = False
    for path, doc in docs:
        quality = doc.get("quality") or {}
        if quality.get("valid") is False:
            invalid = True
        dt, src = observation_datetime(doc)
        if dt is None:
            return {
                "sensor_id": sensor_id,
                "class": "validity",
                "usable": False,
                "age_s": None,
                "time_source": src,
                "paths": [str(path)],
                "reason": "missing_timestamp_not_imputed",
                "has_file": True,
            }
        ages.append((now - dt).total_seconds())
        sources.append(src)
    age = max(ages)
    if invalid:
        return {
            "sensor_id": sensor_id,
            "class": "validity",
            "usable": False,
            "age_s": age,
            "time_source": sources[-1],
            "paths": [str(p) for p, _ in docs],
            "reason": "quality_valid_false",
        }
    if sensor_id in EVENT_DRIVEN_IDS:
        return {
            "sensor_id": sensor_id,
            "class": "event_driven_shadow",
            "usable": False,
            "age_s": age,
            "time_source": sources[-1],
            "paths": [str(p) for p, _ in docs],
            "reason": "shadow_not_in_wave0_denominator",
            "event_age_s": age,
        }
    if age > HOST_FRESH_S:
        return {
            "sensor_id": sensor_id,
            "class": "freshness",
            "usable": False,
            "age_s": age,
            "time_source": sources[-1],
            "paths": [str(p) for p, _ in docs],
            "reason": "observation_age_exceeds_host_window_45s",
            "window_s": HOST_FRESH_S,
        }
    return {
        "sensor_id": sensor_id,
        "class": "fresh_valid",
        "usable": True,
        "age_s": age,
        "time_source": sources[-1],
        "paths": [str(p) for p, _ in docs],
        "reason": "ok",
        "window_s": HOST_FRESH_S,
    }


def classify_coverage(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    required = [classify_sensor(sid, now=now) for sid in WAVE0_REQUIRED_IDS]
    shadow = [classify_sensor(sid, now=now) for sid in SHADOW_OPTIONAL_IDS]
    usable = [r for r in required if r["usable"]]
    fusion = load_json(FUSION_FRAME)
    expected = len(WAVE0_REQUIRED_IDS)
    ratio = (len(usable) / expected) if expected else None
    return {
        "schema": "octopus.coverage-classification.v1",
        "wave0_required": WAVE0_REQUIRED_IDS,
        "shadow_optional": SHADOW_OPTIONAL_IDS,
        "required": required,
        "shadow": shadow,
        "usable": len(usable),
        "expected": expected,
        "ratio": None if ratio is None else round(ratio, 4),
        "fusion_expected": fusion.get("expected_sensors"),
        "fusion_active": fusion.get("active_sensors"),
        "fusion_coverage": fusion.get("coverage"),
        "fusion_degraded": fusion.get("degraded"),
        "note": (
            "WAVE0 coverage denominator is host sensors, not shadow meta sensors. "
            "092/095 are classified, not imputed. Fusion 4/6 or 3/6 mixes shadow STALE "
            "and a 20s thermal window that disagrees with stability's 45s."
        ),
        "threshold_not_lowered": True,
        "healthy_low": 0.90,
        "critical_low": 0.70,
    }
