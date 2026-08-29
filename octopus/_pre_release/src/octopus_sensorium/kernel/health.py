from __future__ import annotations

from octopus_sensorium.models.health import SensorHealthRecord


def from_runtime(sensor_id: str, status: str, consecutive_failures: int = 0, plugin_state: str | None = None) -> SensorHealthRecord:
    return SensorHealthRecord(
        sensor_id=sensor_id,
        status=status,  # type: ignore[arg-type]
        consecutive_failures=consecutive_failures,
        can_self_release_quarantine=False,
        plugin_state=plugin_state,
    )
