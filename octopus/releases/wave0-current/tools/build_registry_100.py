#!/usr/bin/env python3
"""Build unsigned SENSORIUM-100 registry staging. Does not write live /etc/octopus/config."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from octopus_sensorium.isolation import reject_actuator_manifest
from octopus_sensorium.registry.validator import validate_registry_document
from octopus_sensorium.schema_ids import assert_no_sensor_id_collision, is_runtime_enabled

LIVE_REGISTRY = Path("/etc/octopus/config/registry.yaml")
LIVE_BOARD = Path("/etc/octopus/config/board.yaml")
STAGING = Path("/var/lib/octopus/staging/phase3-registry-100")
PACKAGER = Path("/root/OCTOPUS-REGISTRY-100")
BOARD_ID = "sensorium-opi5pro-68e44cdf"
V2_FP = "sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40"
REQUIRED = (
    "sensor_id",
    "name",
    "family",
    "sensor_type",
    "version",
    "schema_version",
    "status",
    "enabled",
    "capabilities",
    "observed_properties",
    "source_requirements",
    "hardware_requirements",
    "credential_requirements",
    "consent_requirements",
    "network_requirements",
    "plugin",
    "schedule",
    "freshness",
    "resources",
    "security",
    "failure",
    "publication",
    "dependencies",
    "fusion_targets",
    "implementation_wave",
)

# n, name, family, sensor_type, status, observed_property, block_reason
SLOTS: list[tuple[int, str, str, str, str, str, str]] = [
    (1, "migrated_system_resources", "host", "system_resources", "DISABLED_BY_POLICY", "host.system_resources", "migrated to OCT-SENSE-053"),
    (2, "migrated_board_thermal", "host", "thermal", "DISABLED_BY_POLICY", "host.soc.temperature", "migrated to OCT-SENSE-053.THERMAL; 002 must not be reused as thermal"),
    (3, "migrated_filesystem", "host", "filesystem", "DISABLED_BY_POLICY", "host.filesystem.mtime", "migrated to OCT-SENSE-051"),
    (4, "ambient_temperature", "environment", "temperature", "BLOCKED_HARDWARE", "env.air.temperature", "no ambient sensor; SoC thermal is OCT-SENSE-053.THERMAL"),
    (5, "humidity", "environment", "humidity", "BLOCKED_HARDWARE", "env.air.humidity", "no humidity sensor on this board"),
    (6, "barometric_pressure", "environment", "pressure", "BLOCKED_HARDWARE", "env.air.pressure", "no barometer"),
    (7, "gas_voc", "environment", "gas", "BLOCKED_HARDWARE", "env.air.voc", "no gas sensor"),
    (8, "illuminance", "environment", "light", "BLOCKED_HARDWARE", "env.illuminance", "no lux sensor"),
    (9, "uv_index", "environment", "light", "BLOCKED_HARDWARE", "env.uv_index", "no UV sensor"),
    (10, "precipitation", "environment", "weather", "BLOCKED_HARDWARE", "env.precipitation", "no weather station"),
    (11, "accelerometer", "inertial", "imu", "BLOCKED_HARDWARE", "host.imu.accel", "no IMU"),
    (12, "gyroscope", "inertial", "imu", "BLOCKED_HARDWARE", "host.imu.gyro", "no IMU"),
    (13, "magnetometer", "inertial", "imu", "BLOCKED_HARDWARE", "host.imu.mag", "no magnetometer"),
    (14, "imu_fusion", "inertial", "imu", "BLOCKED_HARDWARE", "host.imu.attitude", "no IMU fusion source"),
    (15, "reserved_collision_slot", "host", "reserved", "DISABLED_BY_POLICY", "none", "ID 015 is forbidden for SoC temperature; canonical is OCT-SENSE-053.THERMAL"),
    (16, "gnss", "localization", "gnss", "BLOCKED_HARDWARE", "pose.gnss", "no GNSS receiver"),
    (17, "uwb", "localization", "ranging", "BLOCKED_HARDWARE", "pose.uwb", "no UWB"),
    (18, "lidar", "localization", "lidar", "BLOCKED_HARDWARE", "pose.lidar", "no lidar"),
    (19, "ultrasonic", "localization", "ranging", "BLOCKED_HARDWARE", "pose.ultrasonic", "no ultrasonic ranger"),
    (20, "wheel_odometry", "localization", "odometry", "DISABLED_BY_POLICY", "pose.wheel", "leg/actuator path forbidden in WAVE0_OBSERVE_ONLY"),
    (21, "rgb_camera", "vision", "camera", "BLOCKED_HARDWARE", "vision.rgb", "no camera claimed"),
    (22, "depth_camera", "vision", "camera", "BLOCKED_HARDWARE", "vision.depth", "no depth camera"),
    (23, "stereo_camera", "vision", "camera", "BLOCKED_HARDWARE", "vision.stereo", "no stereo camera"),
    (24, "thermal_camera", "vision", "camera", "BLOCKED_HARDWARE", "vision.thermal", "thermal camera absent; not SoC thermal and not id 015/054"),
    (25, "event_camera", "vision", "camera", "BLOCKED_HARDWARE", "vision.events", "no event camera"),
    (26, "microphone_array", "audio", "microphone", "BLOCKED_HARDWARE", "audio.mic_array", "no mic-array plugin"),
    (27, "i2s_codec_capture", "audio", "codec", "BLOCKED_HARDWARE", "audio.i2s", "es8388 is DISCOVERED_UNREGISTERED; no capture plugin"),
    (28, "speaker_path", "audio", "actuator", "DISABLED_BY_POLICY", "audio.speaker", "speaker/DAC path is actuator-adjacent"),
    (29, "ultrasonic_mic", "audio", "microphone", "BLOCKED_HARDWARE", "audio.ultrasonic", "no ultrasonic mic"),
    (30, "audio_beamform", "audio", "microphone", "BLOCKED_HARDWARE", "audio.beamform", "no beamform pipeline"),
    (31, "ir_camera", "vision", "camera", "BLOCKED_HARDWARE", "vision.ir", "no IR camera"),
    (32, "optical_flow", "vision", "camera", "BLOCKED_HARDWARE", "vision.flow", "no optical-flow source"),
    (33, "barcode", "vision", "camera", "BLOCKED_HARDWARE", "vision.barcode", "no barcode camera"),
    (34, "display_capture", "vision", "framebuffer", "PLANNED", "host.display.frame", "no display capture plugin"),
    (35, "hdmi_hotplug", "vision", "display", "PLANNED", "host.display.hotplug", "no HDMI plugin"),
    (36, "line_in", "audio", "codec", "BLOCKED_HARDWARE", "audio.line_in", "codec unregistered"),
    (37, "headset_mic", "audio", "microphone", "BLOCKED_HARDWARE", "audio.headset", "no headset"),
    (38, "audio_vad", "audio", "dsp", "PLANNED", "audio.vad", "no VAD plugin"),
    (39, "audio_level", "audio", "dsp", "PLANNED", "audio.level", "no level plugin"),
    (40, "i2s_clock", "audio", "codec", "PLANNED", "audio.i2s_clock", "no I2S clock sensor"),
    (41, "board_power_monitor", "power", "ina", "BLOCKED_HARDWARE", "power.board.watts", "board.yaml: /sys/class/power_supply empty; add INA219/INA226 first"),
    (42, "battery", "power", "battery", "BLOCKED_HARDWARE", "power.battery", "no battery sysfs"),
    (43, "pd_input", "power", "pd", "BLOCKED_HARDWARE", "power.pd", "no PD telemetry"),
    (44, "rail_3v3", "power", "rail", "BLOCKED_HARDWARE", "power.rail.3v3", "no rail ADC"),
    (45, "rail_5v", "power", "rail", "BLOCKED_HARDWARE", "power.rail.5v", "no rail ADC"),
    (46, "current_shunt", "power", "shunt", "BLOCKED_HARDWARE", "power.shunt", "no shunt"),
    (47, "energy_counter", "power", "energy", "BLOCKED_HARDWARE", "power.energy", "no energy counter"),
    (48, "thermal_power_envelope", "power", "thermal", "PLANNED", "power.thermal_envelope", "not implemented; SoC temp stays 053.THERMAL"),
    (49, "pmic", "power", "pmic", "BLOCKED_HARDWARE", "power.pmic", "no PMIC plugin"),
    (50, "fan_tach", "power", "fan", "DISABLED_BY_POLICY", "power.fan.rpm", "fan control is actuator-adjacent"),
    (51, "filesystem", "host", "filesystem", "ACTIVE", "host.filesystem.mtime", "live Wave 0"),
    (52, "process_and_service", "host", "process", "ACTIVE", "system.process.count", "live Wave 0"),
    (53, "system_resources", "host", "system_resources", "ACTIVE", "host.cpu.load1", "live Wave 0"),
    (54, "structured_logs", "host", "structured_logs", "MANIFEST_ONLY", "host.logs.structured", "OCT-SENSE-054 reserved; not_enabled / no plugin"),
    (55, "distributed_traces", "host", "traces", "MANIFEST_ONLY", "host.traces", "OpenTelemetry exporter not_enabled"),
    (56, "metrics", "host", "metrics", "MANIFEST_ONLY", "host.metrics", "OTel metrics not_enabled"),
    (57, "kernel_dmesg", "host", "logs", "PLANNED", "host.kernel.dmesg", "no dmesg plugin"),
    (58, "cgroup_pressure", "host", "cgroup", "PLANNED", "host.cgroup.pressure", "no PSI plugin"),
    (59, "disk_smart", "host", "storage", "BLOCKED_HARDWARE", "host.disk.smart", "SMART not exposed as a sensor"),
    (60, "usb_topology", "host", "usb", "PLANNED", "host.usb.topology", "no USB inventory plugin"),
    (61, "nats_delivery_stats", "bus", "nats", "PLANNED", "bus.nats.delivery", "no NATS stats plugin; agent must not manage streams"),
    (62, "ethernet_link", "network", "link", "PLANNED", "net.eth.link", "no link sensor plugin"),
    (63, "wifi", "network", "wifi", "BLOCKED_HARDWARE", "net.wifi", "wifi not claimed as a sensor"),
    (64, "mqtt_bridge", "network", "mqtt", "DISABLED_BY_POLICY", "net.mqtt", "port 1883 must stay closed"),
    (65, "otel_exporter", "network", "otel", "MANIFEST_ONLY", "net.otel.export", "same family as 055/056; not_enabled"),
    (66, "dns", "network", "dns", "PLANNED", "net.dns", "no DNS plugin"),
    (67, "ntp_offset", "clock", "ntp", "PLANNED", "clock.ntp.offset", "clock probe exists in kernel; not this sensor id"),
    (68, "ptp", "clock", "ptp", "BLOCKED_NETWORK", "clock.ptp", "no PTP grandmaster path"),
    (69, "ssh_session_audit", "security", "ssh", "PLANNED", "host.ssh.sessions", "no SSH session sensor"),
    (70, "firewall", "security", "netfilter", "PLANNED", "host.firewall", "no firewall sensor"),
    (71, "occupancy", "human", "presence", "BLOCKED_CONSENT", "human.occupancy", "would require consent"),
    (72, "face_presence", "human", "vision", "BLOCKED_CONSENT", "human.face", "would require consent"),
    (73, "voice_activity", "human", "audio", "BLOCKED_CONSENT", "human.vad", "would require consent"),
    (74, "wearable_hr", "health", "wearable", "BLOCKED_CONSENT", "health.heart_rate", "no wearable; health classification blocked"),
    (75, "wearable_spo2", "health", "wearable", "BLOCKED_CONSENT", "health.spo2", "no wearable; health classification blocked"),
    (76, "room_presence", "human", "presence", "BLOCKED_CONSENT", "human.room", "would require consent"),
    (77, "touch", "human", "hmi", "BLOCKED_CONSENT", "human.touch", "would require consent"),
    (78, "speech_transcript", "human", "audio", "BLOCKED_CONSENT", "human.transcript", "would require consent"),
    (79, "personal_location", "human", "location", "BLOCKED_CONSENT", "human.location", "would require consent"),
    (80, "biometrics", "health", "biometric", "BLOCKED_CONSENT", "health.biometric", "would require consent"),
    (81, "leg01_joint", "robot", "leg", "DISABLED_BY_POLICY", "leg.01.joint", "leg_authority=DENIED"),
    (82, "leg02_joint", "robot", "leg", "DISABLED_BY_POLICY", "leg.02.joint", "leg_authority=DENIED"),
    (83, "leg03_joint", "robot", "leg", "DISABLED_BY_POLICY", "leg.03.joint", "leg_authority=DENIED"),
    (84, "leg04_joint", "robot", "leg", "DISABLED_BY_POLICY", "leg.04.joint", "leg_authority=DENIED"),
    (85, "imu_base", "robot", "imu", "DISABLED_BY_POLICY", "robot.base.imu", "robot body not attached"),
    (86, "motor_current", "robot", "actuator", "DISABLED_BY_POLICY", "robot.motor.current", "actuator telemetry forbidden"),
    (87, "torque", "robot", "actuator", "DISABLED_BY_POLICY", "robot.motor.torque", "actuator telemetry forbidden"),
    (88, "estop_channel", "safety", "estop", "DISABLED_BY_POLICY", "safety.estop", "estop_channel=NOT_PRESENT"),
    (89, "sto_state", "safety", "sto", "DISABLED_BY_POLICY", "safety.sto", "no STO hardware"),
    (90, "pwm_feedback", "robot", "pwm", "DISABLED_BY_POLICY", "robot.pwm.feedback", "PWM path closed"),
    (91, "fusion_situation", "meta", "fusion", "PLANNED", "world.situation", "fusion STATUS=NOT_ENABLED"),
    (92, "anomaly", "meta", "anomaly", "SHADOW", "sensor.anomaly", "live Wave 0 shadow"),
    (93, "active_sensing", "meta", "active_sensing", "DISABLED_BY_POLICY", "sensing.active", "WAVE0_OBSERVE_ONLY is not armed"),
    (94, "world_state", "meta", "world_state", "PLANNED", "world.snapshot", "snapshot/replay exist; not a sensor plugin"),
    (95, "contradiction", "meta", "contradiction", "SHADOW", "world.contradiction", "live Wave 0 shadow"),
    (96, "uncertainty", "meta", "uncertainty", "MANIFEST_ONLY", "meta.uncertainty", "skeleton only; advisory; no plugin"),
    (97, "novelty", "meta", "novelty", "MANIFEST_ONLY", "meta.novelty", "skeleton only; novelty≠anomaly; no plugin"),
    (98, "calibration", "meta", "calibration", "MANIFEST_ONLY", "meta.calibration", "no calibration agent"),
    (99, "policy_safety", "meta", "policy", "MANIFEST_ONLY", "meta.policy_safety", "skeleton may propose DEGRADED/FAILED_SAFE; not enabled; cannot actuate"),
    (100, "provenance_trust", "meta", "provenance", "MANIFEST_ONLY", "meta.provenance", "skeleton only; does not declare world truth"),
]


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def security(consent: bool = False, classification: str = "internal") -> dict:
    return {
        "classification": classification,
        "requires_consent": consent,
        "network_access": "none",
        "actuator_access": False,
        "shell_access": False,
        "command_access": False,
    }


def skeleton(slot: tuple[int, str, str, str, str, str, str]) -> dict:
    n, name, family, sensor_type, status, prop, reason = slot
    enabled = status in {"ACTIVE", "SHADOW"}
    consent = family in {"human", "health"} or status == "BLOCKED_CONSENT"
    classification = "health" if family == "health" else "internal"
    return {
        "sensor_id": f"OCT-SENSE-{n:03d}",
        "name": name,
        "family": family,
        "sensor_type": sensor_type,
        "version": "0.0.0" if not enabled else "1.0.0",
        "schema_version": "1.0.0",
        "status": status,
        "enabled": enabled,
        "capabilities": [],
        "observed_properties": [prop] if prop != "none" else [],
        "source_requirements": {"present": False, "reason": reason} if not enabled else {"present": True},
        "hardware_requirements": {"present": enabled or status == "SHADOW"},
        "credential_requirements": {"required": False},
        "consent_requirements": {"required": consent},
        "network_requirements": {"required": False, "mqtt_forbidden": True},
        "plugin": None,
        "schedule": {
            "mode": "disabled",
            "default_interval_seconds": 0,
            "minimum_interval_seconds": 1,
            "maximum_interval_seconds": 3600,
        },
        "freshness": {"ttl_seconds": 0},
        "resources": {"max_memory_mb": 0, "max_cpu_percent": 0, "max_payload_bytes": 0},
        "security": security(consent=consent, classification=classification),
        "failure": {"timeout_seconds": 1, "maximum_retries": 0, "backoff": "none", "quarantine_after_failures": 1},
        "publication": {
            "raw_enabled": False,
            "observation_enabled": False,
            "feature_enabled": False,
            "can_change_readiness": False,
            "can_quarantine": False,
            "can_execute": False,
        },
        "dependencies": [],
        "fusion_targets": [],
        "implementation_wave": "wave0" if enabled else "unscheduled",
        "block_reason": reason,
        "simulated": False,
    }


def enrich_live(live: dict, slot: tuple[int, str, str, str, str, str, str]) -> dict:
    n, name, family, sensor_type, status, prop, reason = slot
    out = dict(live)
    defaults = skeleton(slot)
    for key in REQUIRED:
        if key not in out or out[key] in (None, "", []):
            if key == "plugin" and live.get("plugin"):
                continue
            if key in live and live[key] not in (None, ""):
                continue
            out[key] = defaults[key]
    out["name"] = live.get("name") or name
    out["family"] = family
    out["sensor_type"] = live.get("sensor_type") or sensor_type
    out["status"] = status
    out["enabled"] = True
    out["implementation_wave"] = "wave0"
    out["block_reason"] = reason
    out["simulated"] = False
    if not out.get("observed_properties"):
        out["observed_properties"] = [prop]
    out.setdefault("source_requirements", {"present": True, "authority": (live.get("source") or {}).get("authority")})
    out.setdefault("hardware_requirements", {"present": True})
    out.setdefault("credential_requirements", {"required": False})
    out.setdefault("consent_requirements", {"required": False})
    out.setdefault("network_requirements", {"required": False, "mqtt_forbidden": True})
    out.setdefault("dependencies", [])
    out.setdefault("fusion_targets", [])
    out.setdefault("resources", {"max_memory_mb": 64, "max_cpu_percent": 8, "max_payload_bytes": 262144})
    sec = dict(out.get("security") or {})
    sec.setdefault("actuator_access", False)
    sec.setdefault("shell_access", False)
    sec.setdefault("command_access", False)
    sec.setdefault("classification", "internal")
    out["security"] = sec
    pub = dict(out.get("publication") or {})
    pub.setdefault("can_change_readiness", False)
    pub.setdefault("can_quarantine", False)
    pub.setdefault("can_execute", False)
    out["publication"] = pub
    return out


def extra_discovered(live: dict) -> dict:
    out = dict(live)
    out.setdefault("family", "discovered")
    out.setdefault("sensor_type", out.get("name") or "unknown")
    out.setdefault("schema_version", "1.0.0")
    out["enabled"] = False
    out.setdefault("capabilities", [])
    out.setdefault("observed_properties", [])
    out.setdefault("source_requirements", {"present": True, "registered": False})
    out.setdefault("hardware_requirements", {"present": True, "registered": False})
    out.setdefault("credential_requirements", {"required": False})
    out.setdefault("consent_requirements", {"required": False})
    out.setdefault("network_requirements", {"required": False})
    out["plugin"] = None
    out.setdefault("schedule", {"mode": "disabled"})
    out.setdefault("freshness", {"ttl_seconds": 0})
    out.setdefault("resources", {"max_memory_mb": 0})
    sec = dict(out.get("security") or {})
    sec["actuator_access"] = False
    sec["shell_access"] = False
    sec["command_access"] = False
    out["security"] = sec
    out.setdefault("failure", {"timeout_seconds": 1, "maximum_retries": 0})
    out.setdefault("publication", {"raw_enabled": False, "observation_enabled": False})
    out.setdefault("dependencies", [])
    out.setdefault("fusion_targets", [])
    out.setdefault("implementation_wave", "unscheduled")
    return out


def extra_thermal(live: dict) -> dict:
    slot = (53, "board_thermal", "host", "thermal", "ACTIVE", "host.soc.temperature", "live Wave 0; not id 015/054")
    out = enrich_live(live, slot)
    out["sensor_id"] = "OCT-SENSE-053.THERMAL"
    out["name"] = "board_thermal"
    out["family"] = "host"
    out["sensor_type"] = "thermal"
    return out


def build(live_doc: dict) -> dict:
    by_id = {s["sensor_id"]: s for s in live_doc["sensors"]}
    sensors: list[dict] = []
    for slot in SLOTS:
        n = slot[0]
        sid = f"OCT-SENSE-{n:03d}"
        live = by_id.get(sid)
        if live and slot[4] in {"ACTIVE", "SHADOW"}:
            sensors.append(enrich_live(live, slot))
        elif sid == "OCT-SENSE-054" and live:
            spec = skeleton(slot)
            spec["wave"] = 0
            sensors.append(spec)
        else:
            sensors.append(skeleton(slot))
    thermal = by_id.get("OCT-SENSE-053.THERMAL")
    if thermal:
        sensors.append(extra_thermal(thermal))
    for extra_id in ("OCT-SENSE-CODEC-ES8388", "OCT-SENSE-RTC-HYM8563"):
        if extra_id in by_id:
            sensors.append(extra_discovered(by_id[extra_id]))
    doc = {
        "schema_version": live_doc.get("schema_version", "1.0.0"),
        "config_version": 5,
        "not_before": live_doc["not_before"],
        "not_after": live_doc["not_after"],
        "id_namespace": "SENSORIUM-100",
        "board_id": BOARD_ID,
        "phase": 3,
        "content_changes": True,
        "actuator_changes": False,
        "network_changes": False,
        "mqtt_state": "DISABLED",
        "leg_authority": "DENIED",
        "sensors": sensors,
    }
    return doc


def write_yaml(path: Path, doc: dict) -> None:
    path.write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def catalog_markdown(doc: dict) -> str:
    lines = [
        "# SENSORIUM-100 catalog (staging)",
        "",
        "Unsigned staging only. Live registry is unchanged until a root-v2 signature is applied.",
        "",
        "| ID | Name | Family | Status | Enabled | Plugin |",
        "|---|---|---|---|---|---|",
    ]
    for spec in doc["sensors"]:
        plugin = (spec.get("plugin") or {}).get("type") if spec.get("plugin") else "none"
        lines.append(
            f"| {spec['sensor_id']} | {spec.get('name')} | {spec.get('family')} | {spec.get('status')} | {spec.get('enabled')} | {plugin} |"
        )
    lines.append("")
    lines.append("ACTIVE/SHADOW sensors are the only runtime plugins. All others are manifest slots.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    live_doc = yaml.safe_load(LIVE_REGISTRY.read_text(encoding="utf-8"))
    doc = build(live_doc)
    assert_no_sensor_id_collision(doc["sensors"])
    for spec in doc["sensors"]:
        reject_actuator_manifest(spec)
        missing = [k for k in REQUIRED if k not in spec]
        if missing:
            raise SystemExit(f"{spec.get('sensor_id')} missing {missing}")
    validate_registry_document(doc)
    numeric = [s for s in doc["sensors"] if str(s["sensor_id"]).startswith("OCT-SENSE-") and str(s["sensor_id"])[10:].isdigit()]
    if len(numeric) != 100:
        raise SystemExit(f"expected 100 numeric ids, got {len(numeric)}")
    runtime = [s["sensor_id"] for s in doc["sensors"] if is_runtime_enabled(s)]
    allowed_runtime = {
        "OCT-SENSE-051",
        "OCT-SENSE-052",
        "OCT-SENSE-053",
        "OCT-SENSE-053.THERMAL",
        "OCT-SENSE-092",
        "OCT-SENSE-095",
    }
    if set(runtime) != allowed_runtime:
        raise SystemExit(f"runtime set mismatch: {runtime}")
    if any((s.get("plugin") or {}).get("type") not in {None, "filesystem", "process", "system_resources", "thermal", "anomaly", "contradiction"} for s in doc["sensors"] if s.get("plugin")):
        raise SystemExit("unexpected plugin type")

    STAGING.mkdir(parents=True, exist_ok=True)
    PACKAGER.mkdir(parents=True, exist_ok=True)
    registry_path = STAGING / "registry.yaml"
    write_yaml(registry_path, doc)
    shutil.copyfile(LIVE_BOARD, STAGING / "board.yaml")
    if sha(STAGING / "board.yaml") != sha(LIVE_BOARD):
        raise SystemExit("board.yaml copy drifted")

    hashes = (
        f"{sha(STAGING / 'board.yaml')[7:]}  board.yaml\n"
        f"{sha(registry_path)[7:]}  registry.yaml\n"
    )
    (STAGING / "current-hashes.sha256").write_text(hashes, encoding="utf-8")
    (STAGING / "SENSOR_CATALOG_100.md").write_text(catalog_markdown(doc), encoding="utf-8")
    summary = {
        "board_id": BOARD_ID,
        "phase": "PHASE_3",
        "execution_state": "AWAITING_OFFLINE_SIGNATURE",
        "config_version": 5,
        "live_registry_hash": sha(LIVE_REGISTRY),
        "staging_registry_hash": sha(registry_path),
        "board_hash": sha(STAGING / "board.yaml"),
        "expected_root_v2_fingerprint": V2_FP,
        "numeric_sensors": 100,
        "runtime_enabled": sorted(runtime),
        "content_changes": True,
        "actuator_changes": False,
        "network_changes": False,
        "live_files_modified": False,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    (STAGING / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (STAGING / "README.txt").write_text(
        "PHASE 3 unsigned staging.\n"
        "Do not copy registry.yaml onto /etc/octopus/config.\n"
        "Sign on Windows with OCTOPUS-REGISTRY-100/sign-registry-v2.bat\n"
        "using the EXISTING root-v2 private key. Do not run make-root-v2.bat.\n",
        encoding="utf-8",
    )

    for name in ("registry.yaml", "board.yaml", "current-hashes.sha256", "manifest.json", "SENSOR_CATALOG_100.md"):
        shutil.copyfile(STAGING / name, PACKAGER / name)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
