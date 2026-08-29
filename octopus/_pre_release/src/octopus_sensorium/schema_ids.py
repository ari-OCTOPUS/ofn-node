"""Detect SENSORIUM-100 identifier collisions. Thermal must not occupy 054 or 015."""

from __future__ import annotations

THERMAL_FORBIDDEN_IDS = {"OCT-SENSE-054", "OCT-SENSE-015"}
THERMAL_CANONICAL = "OCT-SENSE-053.THERMAL"
INACTIVE_STATUSES = {
    "not_enabled",
    "discovered_unregistered",
    "PLANNED",
    "MANIFEST_ONLY",
    "BLOCKED_HARDWARE",
    "BLOCKED_CREDENTIAL",
    "BLOCKED_CONSENT",
    "BLOCKED_NETWORK",
    "DISABLED_BY_POLICY",
    "QUARANTINED",
    "DEFERRED",
}
RUNTIME_STATUSES = {"ACTIVE", "SHADOW"}
RESERVED_SEMANTICS = {
    "OCT-SENSE-001": "migrated_to_OCT-SENSE-053",
    "OCT-SENSE-002": "migrated_to_OCT-SENSE-053.THERMAL",
    "OCT-SENSE-003": "migrated_to_OCT-SENSE-051",
    "OCT-SENSE-015": "reserved_collision_slot",
    "OCT-SENSE-051": "filesystem",
    "OCT-SENSE-052": "process_and_service",
    "OCT-SENSE-053": "system_resources",
    "OCT-SENSE-053.CPU": "cpu_resources",
    "OCT-SENSE-053.MEMORY": "memory_resources",
    "OCT-SENSE-053.STORAGE": "storage_resources",
    "OCT-SENSE-053.THERMAL": "board_thermal",
    "OCT-SENSE-054": "structured_logs",
    "OCT-SENSE-055": "distributed_traces",
    "OCT-SENSE-056": "metrics",
    "OCT-SENSE-092": "anomaly",
    "OCT-SENSE-095": "contradiction",
    "OCT-SENSE-096": "uncertainty",
    "OCT-SENSE-097": "novelty",
    "OCT-SENSE-099": "policy_safety",
    "OCT-SENSE-100": "provenance_trust",
}


class SensorIdCollision(Exception):
    pass


def is_runtime_enabled(spec: dict) -> bool:
    if spec.get("enabled") is False:
        return False
    status = spec.get("status")
    if status in INACTIVE_STATUSES:
        return False
    if status in RUNTIME_STATUSES:
        return True
    return bool(spec.get("plugin")) and spec.get("enabled") is not False


def assert_no_sensor_id_collision(sensors: list[dict]) -> None:
    by_id: dict[str, dict] = {}
    for spec in sensors:
        sid = spec.get("sensor_id")
        if not sid:
            raise SensorIdCollision("sensor missing sensor_id")
        if sid in by_id:
            raise SensorIdCollision(f"duplicate enabled sensor_id {sid}")
        by_id[sid] = spec
        name = str(spec.get("name", "")).lower()
        ptype = str((spec.get("plugin") or {}).get("type", "")).lower()
        thermalish = "thermal" in name or ptype == "thermal" or "temperature" in name
        if thermalish and sid in THERMAL_FORBIDDEN_IDS:
            raise SensorIdCollision(
                f"{sid} cannot be thermal; canonical id is {THERMAL_CANONICAL}"
            )
        if sid == "OCT-SENSE-054" and ptype not in {"", "structured_logs"} and is_runtime_enabled(spec):
            raise SensorIdCollision("OCT-SENSE-054 is reserved for structured_logs")
    logs = next((s for s in sensors if s.get("sensor_id") == "OCT-SENSE-054"), None)
    if logs and is_runtime_enabled(logs):
        if (logs.get("plugin") or {}).get("type") == "thermal":
            raise SensorIdCollision("OCT-SENSE-054 enabled as thermal")
