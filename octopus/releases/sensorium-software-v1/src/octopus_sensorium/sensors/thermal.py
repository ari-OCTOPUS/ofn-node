"""SoC thermal zones. Board temperature is not ambient weather."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult

THERMAL_ROOT = Path("/sys/class/thermal")


def read_zones(root: Path = THERMAL_ROOT) -> dict[str, float]:
    zones: dict[str, float] = {}
    if not root.exists():
        return zones
    for zone in sorted(root.glob("thermal_zone*")):
        try:
            name = (zone / "type").read_text(encoding="utf-8").strip()
            milli = int((zone / "temp").read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            continue
        zones[name] = milli / 1000.0
    return zones


class ThermalSensor(BaseSensor):
    sensor_type = "thermal"
    capabilities = {"soc_temperature", "zone_temperature"}

    async def discover(self) -> DiscoveryResult:
        zones = read_zones()
        return DiscoveryResult(present=bool(zones), details={"zones": list(zones)})

    async def self_test(self) -> SelfTestResult:
        zones = read_zones()
        ok = bool(zones) and all(-40.0 <= t <= 125.0 for t in zones.values())
        return SelfTestResult(
            passed=ok,
            message=f"{len(zones)} zones" if ok else "no valid thermal zones",
            measurements=zones,
        )

    async def observe(self) -> AsyncIterator[RawObservation]:
        zones = read_zones()
        payload = {"sequence": self.next_sequence(), "zones_celsius": zones}
        yield RawObservation(payload=payload, source_id="sysfs-thermal", bytes_len=len(str(payload)))
