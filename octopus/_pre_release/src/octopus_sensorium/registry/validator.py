from __future__ import annotations

from octopus_sensorium.isolation import reject_actuator_manifest
from octopus_sensorium.models.sensor_manifest import SensorManifest
from octopus_sensorium.schema_ids import assert_no_sensor_id_collision


def validate_registry_document(document: dict) -> list[SensorManifest]:
    sensors = document.get("sensors") or []
    if not isinstance(sensors, list):
        raise ValueError("registry sensors must be a list")
    assert_no_sensor_id_collision(sensors)
    out: list[SensorManifest] = []
    for spec in sensors:
        reject_actuator_manifest(spec)
        out.append(SensorManifest.model_validate(spec))
    return out
