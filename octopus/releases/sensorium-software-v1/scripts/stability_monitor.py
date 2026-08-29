#!/usr/bin/env python3
"""WAVE0 observe-only stability / homeostatic core.

Reads evidence files and fusion coverage. Does not subscribe to NATS
observations. Does not actuate. Prometheus text on loopback :9101.
Healthy ranges, not attractive CPU setpoints.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/cognition/src")
from octopus_cognition.homeostasis.core import evaluate, load_specs  # noqa: E402
from octopus_cognition.homeostasis.models import HomeostaticSnapshot  # noqa: E402
import sys as _sys
_sys.path.insert(0, "/opt/octopus/scripts")
from authority_mirror import resolve_authority_mirror  # noqa: E402

EVIDENCE = Path("/var/lib/octopus/state/evidence")
STATE_DIR = Path("/var/lib/octopus/state/stability")
HOMEO_DIR = Path("/var/lib/octopus/state/homeostasis")
ENVELOPE_PATH = STATE_DIR / "envelope.json"
LATEST_PATH = STATE_DIR / "latest.json"
HOMEO_LATEST = HOMEO_DIR / "latest.json"
BIND_HOST = os.environ.get("OCTOPUS_STABILITY_BIND") or os.environ.get("STABILITY_BIND_ADDR") or "127.0.0.1"
BIND_PORT = int(os.environ.get("OCTOPUS_STABILITY_PORT", "9101"))
BOOT_REPORT = Path("/var/lib/octopus/state/boot_report.json")
FUSION = Path("/var/lib/octopus/state/fusion/latest-frame.json")
SKILL = Path("/var/lib/octopus/state/skill/latest.json")
META = Path("/var/lib/octopus/state/metacontrol/latest.json")
CONFIG = Path("/etc/octopus/homeostasis.yaml")
FRESH_S = 45.0

SOURCES = {
    "compute_pressure": ("last_OCT-SENSE-053_CPU.json", "load1_per_nproc"),
    "memory_pressure": ("last_OCT-SENSE-053_MEMORY.json", "percent_01"),
    "thermal_integrity": ("last_OCT-SENSE-053_THERMAL.json", "raw"),
    "storage_integrity": ("last_OCT-SENSE-053_STORAGE.json", "percent_01"),
}

_lock = threading.Lock()
_latest: dict[str, Any] = {}


def _nproc() -> int:
    return max(int(os.cpu_count() or 8), 1)


def _parse_obs(path: Path) -> tuple[float | None, str | None, float | None]:
    if not path.is_file():
        return None, None, None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None, None
    value = (doc.get("result") or {}).get("value")
    stamp = ((doc.get("time") or {}).get("phenomenon_time")) or ""
    age = None
    if stamp:
        try:
            dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - dt).total_seconds()
        except ValueError:
            age = None
    try:
        return float(value), stamp, age
    except (TypeError, ValueError):
        return None, stamp, age


def _scale(raw: float | None, how: str) -> float | None:
    if raw is None:
        return None
    if how == "percent_01":
        return raw / 100.0
    if how == "load1_per_nproc":
        return raw / float(_nproc())
    return raw


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def snapshot_dict(snap: HomeostaticSnapshot, extra: dict[str, Any]) -> dict[str, Any]:
    variables = {
        name: {
            "value": reading.value,
            "status": reading.status.value,
            "stale": reading.stale,
            "source": reading.source,
            "stamp": reading.stamp,
            "raw": reading.raw,
        }
        for name, reading in snap.variables.items()
    }
    _auth_mirror = resolve_authority_mirror()
    doc = {
        "schema": "octopus.homeostasis.snapshot.v1",
        "timestamp": extra.get("timestamp"),
        "board_id": "sensorium-opi5pro-68e44cdf",
        "readiness_profile": "WAVE0_OBSERVE_ONLY",
        "actuator_authority": _auth_mirror.get("actuator_authority") or "NONE",
        "estop_channel": _auth_mirror.get("estop_channel"),
        "authority_mirror": {
            "source": _auth_mirror.get("mirror_source"),
            "soft_unlock_ok": _auth_mirror.get("soft_unlock_ok"),
            "ARMED": False,
            "note": _auth_mirror.get("note"),
        },
        "clock_trust": extra.get("clock_trust"),
        "envelope_profile": snap.profile,
        "envelope_version": snap.version,
        "mode": snap.mode.value,
        "severity": snap.severity.value,
        "would_decide": extra.get("would_decide") or "reflex",
        "executed": "none",
        "executable": False,
        "action": "NONE",
        "host_in_range": snap.host_in_range,
        "data_ok": snap.data_ok,
        "homeostasis_ok": snap.homeostasis_ok,
        "in_envelope": snap.in_envelope,
        "distance": snap.range_distance,
        "range_distance": snap.range_distance,
        "energy_ratio": snap.energy_ratio,
        "nproc": _nproc(),
        "unknown": list(snap.unknown),
        "note": snap.note,
        "variables": variables,
        "axes": extra.get("axes") or {},
        "skill": extra.get("skill") or {},
        "metacontrol": extra.get("metacontrol") or {},
        "fusion_coverage": extra.get("fusion_coverage"),
    }
    return doc


def compute() -> dict[str, Any]:
    values: dict[str, float | None] = {}
    stale: dict[str, bool] = {}
    stamps: dict[str, str | None] = {}
    raws: dict[str, float | None] = {}
    axes: dict[str, Any] = {}
    ages: list[float] = []
    observation_ages: dict[str, float] = {}
    for name, (filename, scale) in SOURCES.items():
        raw, stamp, age = _parse_obs(EVIDENCE / filename)
        value = _scale(raw, scale)
        is_stale = age is None or age > FRESH_S or value is None
        values[name] = value
        stale[name] = is_stale
        stamps[name] = stamp
        raws[name] = raw
        if age is not None:
            ages.append(age)
        axis_name = {
            "compute_pressure": "cpu_utilisation",
            "memory_pressure": "memory_used",
            "thermal_integrity": "soc_temperature",
            "storage_integrity": "disk_used",
        }[name]
        axes[axis_name] = {
            "raw": raw,
            "value": value,
            "stale": is_stale,
            "stamp": stamp,
            "age_seconds": age,
            "evidence_file": filename,
        }
        sensor_id = {
            "last_OCT-SENSE-053_CPU.json": "OCT-SENSE-053.CPU",
            "last_OCT-SENSE-053_MEMORY.json": "OCT-SENSE-053.MEMORY",
            "last_OCT-SENSE-053_THERMAL.json": "OCT-SENSE-053.THERMAL",
            "last_OCT-SENSE-053_STORAGE.json": "OCT-SENSE-053.STORAGE",
        }.get(filename, filename.replace("last_", "").replace(".json", ""))
        if age is not None:
            observation_ages[sensor_id] = float(age)

    values["evidence_freshness"] = max(ages) if ages else None
    stale["evidence_freshness"] = values["evidence_freshness"] is None
    stamps["evidence_freshness"] = datetime.now(timezone.utc).isoformat()

    frame = _json(FUSION)
    coverage = frame.get("coverage")
    try:
        values["sensor_coverage"] = float(coverage) if coverage is not None else None
    except (TypeError, ValueError):
        values["sensor_coverage"] = None
    stale["sensor_coverage"] = values["sensor_coverage"] is None
    stamps["sensor_coverage"] = frame.get("frame_id")

    skill = _json(SKILL)
    score = skill.get("score")
    cal = skill.get("calibration_error")
    values["model_skill"] = float(score) if isinstance(score, (int, float)) else None
    values["prediction_calibration"] = float(cal) if isinstance(cal, (int, float)) else None
    stale["model_skill"] = values["model_skill"] is None
    stale["prediction_calibration"] = values["prediction_calibration"] is None

    specs = load_specs(CONFIG)
    envelope = _json(ENVELOPE_PATH)
    snap = evaluate(
        values,
        stale=stale,
        stamps=stamps,
        raw=raws,
        specs=specs,
        profile=str(envelope.get("profile") or "WAVE0_IDLE"),
        version=int(envelope.get("version") or 2),
    )
    clock_trust = "UNKNOWN"
    try:
        clock_trust = str((_json(BOOT_REPORT).get("clock") or {}).get("clock_trust") or "UNKNOWN")
    except Exception:
        pass
    meta = _json(META)
    mode_value = snap.mode.value
    would_decide = str(meta.get("would_decide") or "")
    if would_decide not in {"plan", "reflex", "block"}:
        would_decide = "block" if mode_value == "would_lockdown" else "reflex"
    doc = snapshot_dict(
        snap,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "clock_trust": clock_trust,
            "axes": axes,
            "skill": {"samples": skill.get("samples"), "reason": skill.get("reason"), "eligible": skill.get("eligible")},
            "metacontrol": meta,
            "fusion_coverage": values["sensor_coverage"],
            "would_decide": would_decide,
        },
    )
    # LAB ENRICH E1: surface observation ages for Prometheus / doctor
    doc["observation_ages"] = observation_ages
    if ages:
        doc["observation_age_max_seconds"] = float(max(ages))
    return doc


def render_metrics(doc: dict[str, Any]) -> bytes:
    lines = [
        "# HELP octopus_stability_distance RMS excess outside healthy host ranges",
        "# TYPE octopus_stability_distance gauge",
        f"octopus_stability_distance {float(doc['distance']):.6f}",
        "# HELP octopus_stability_in_envelope 1 if host variables are in healthy ranges",
        "# TYPE octopus_stability_in_envelope gauge",
        f"octopus_stability_in_envelope {1 if doc['in_envelope'] else 0}",
        "# HELP octopus_homeostasis_ok 1 if host ranges and data health are both ok",
        "# TYPE octopus_homeostasis_ok gauge",
        f"octopus_homeostasis_ok {1 if doc.get('homeostasis_ok') else 0}",
        "# HELP octopus_homeostasis_energy_ratio Headroom vs max(cpu, memory)",
        "# TYPE octopus_homeostasis_energy_ratio gauge",
        f"octopus_homeostasis_energy_ratio {float(doc.get('energy_ratio') or 0):.6f}",
        "# HELP octopus_homeostasis_mode 0=normal 1=conserve 2=would_lockdown(advisory)",
        "# TYPE octopus_homeostasis_mode gauge",
        f"octopus_homeostasis_mode { {'normal': 0, 'conserve': 1, 'would_lockdown': 2, 'protect': 2, 'lockdown': 2}.get(doc.get('mode'), -1) }",
        "# HELP octopus_axis_value Current host axis value",
        "# TYPE octopus_axis_value gauge",
        "# HELP octopus_axis_stale 1 if evidence is missing or older than freshness window",
        "# TYPE octopus_axis_stale gauge",
        "# HELP octopus_homeo_value Homeostatic variable value",
        "# TYPE octopus_homeo_value gauge",
        "# HELP octopus_homeo_unknown 1 if variable is missing and not zero-filled",
        "# TYPE octopus_homeo_unknown gauge",
    ]
    for name, axis in (doc.get("axes") or {}).items():
        val = axis.get("value")
        if val is not None:
            lines.append(f'octopus_axis_value{{axis="{name}"}} {float(val):.6f}')
        lines.append(f'octopus_axis_stale{{axis="{name}"}} {1 if axis.get("stale") else 0}')
    for name, var in (doc.get("variables") or {}).items():
        val = var.get("value")
        if val is not None:
            lines.append(f'octopus_homeo_value{{variable="{name}"}} {float(val):.6f}')
        lines.append(f'octopus_homeo_unknown{{variable="{name}"}} {1 if var.get("value") is None else 0}')
    skill = doc.get("skill") or {}
    if skill.get("samples") is not None:
        lines.append("# HELP octopus_skill_samples Paired prediction outcomes")
        lines.append("# TYPE octopus_skill_samples gauge")
        lines.append(f"octopus_skill_samples {int(skill['samples'])}")
    meta = doc.get("metacontrol") or {}
    lines.append("# HELP octopus_metacontrol_executable Always 0 in WAVE0_OBSERVE_ONLY")
    lines.append("# TYPE octopus_metacontrol_executable gauge")
    lines.append(f"octopus_metacontrol_executable {1 if meta.get('executable') else 0}")
    would = str(doc.get("would_decide") or meta.get("would_decide") or "reflex")
    if would not in {"plan", "reflex", "block"}:
        would = "reflex"
    lines.append("# HELP octopus_metacontrol_would_decide Hypothetical WAVE0 decision; never executed")
    lines.append("# TYPE octopus_metacontrol_would_decide gauge")
    for kind in ("plan", "reflex", "block"):
        lines.append(f'octopus_metacontrol_would_decide{{kind="{kind}"}} {1 if would == kind else 0}')
    lines.append("# HELP octopus_sensor_observation_age_seconds Seconds since evidence phenomenon_time")
    lines.append("# TYPE octopus_sensor_observation_age_seconds gauge")
    for sensor, age in sorted((doc.get("observation_ages") or {}).items()):
        try:
            lines.append(f'octopus_sensor_observation_age_seconds{{sensor="{sensor}"}} {float(age):.3f}')
        except (TypeError, ValueError):
            continue
    if doc.get("observation_age_max_seconds") is not None:
        lines.append("# HELP octopus_sensor_observation_age_max_seconds Max observation age across host evidence sources")
        lines.append("# TYPE octopus_sensor_observation_age_max_seconds gauge")
        lines.append(f"octopus_sensor_observation_age_max_seconds {float(doc['observation_age_max_seconds']):.3f}")
    lines.append("# HELP octopus_actions_executed_total Host actions executed; must stay 0 in WAVE0")
    lines.append("# TYPE octopus_actions_executed_total counter")
    lines.append('octopus_actions_executed_total{profile="WAVE0_OBSERVE_ONLY"} 0')
    lines.append("")
    return ("\n".join(lines)).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        with _lock:
            doc = dict(_latest)
        if self.path in {"/metrics", "/"}:
            body = render_metrics(doc) if doc else b"# no samples yet\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/healthz":
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)


def serve() -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HOMEO_DIR.mkdir(parents=True, exist_ok=True)
    try:
        serve()
    except OSError as exc:
        raise SystemExit(f"stability bind failed on {BIND_HOST}:{BIND_PORT}: {exc}") from exc
    while True:
        doc = compute()
        with _lock:
            _latest.clear()
            _latest.update(doc)
        text = json.dumps(doc, indent=2) + "\n"
        LATEST_PATH.write_text(text, encoding="utf-8")
        HOMEO_LATEST.write_text(text, encoding="utf-8")
        time.sleep(5)


if __name__ == "__main__":
    try:
        socket.setdefaulttimeout(2)
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
