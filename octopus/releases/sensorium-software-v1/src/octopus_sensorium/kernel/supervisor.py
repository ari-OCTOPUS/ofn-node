"""Plugin supervisor. Unknown types are refused; quarantine is not self-cleared."""

from __future__ import annotations

from typing import Any

from octopus_sensorium.isolation import reject_actuator_manifest
from octopus_sensorium.kernel.lifecycle import PluginLifecycle, PluginState
from octopus_sensorium.schema_ids import assert_no_sensor_id_collision, is_runtime_enabled
from octopus_sensorium.sensors.base import SensorError


class PluginSupervisor:
    def __init__(self, plugin_types: dict[str, type], lifecycle: PluginLifecycle | None = None) -> None:
        self.plugin_types = plugin_types
        self.lifecycle = lifecycle or PluginLifecycle()
        self.plugins: dict[str, Any] = {}
        self.health: dict[str, str] = {}
        self.skipped_unknown: list[str] = []

    def instantiate(self, sensors: list[dict[str, Any]]) -> None:
        assert_no_sensor_id_collision(sensors)
        for spec in sensors:
            sensor_id = str(spec.get("sensor_id") or "")
            if not is_runtime_enabled(spec):
                continue
            if spec.get("enabled") is False:
                continue
            if not spec.get("plugin"):
                continue
            reject_actuator_manifest(spec)
            self.lifecycle.mark(sensor_id, PluginState.DISCOVERED)
            plugin_type = (spec.get("plugin") or {}).get("type")
            cls = self.plugin_types.get(plugin_type)
            if cls is None:
                self.skipped_unknown.append(sensor_id)
                self.lifecycle.mark(sensor_id, PluginState.FAILED)
                continue
            try:
                plugin = cls(spec)
            except SensorError:
                self.health[sensor_id] = "quarantine"
                self.lifecycle.mark(sensor_id, PluginState.QUARANTINED)
                continue
            self.plugins[sensor_id] = plugin
            self.lifecycle.mark(sensor_id, PluginState.VERIFIED)
