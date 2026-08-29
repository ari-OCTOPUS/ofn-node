"""Base sensor plugin contract. Plugins must not touch actuators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from octopus_sensorium.kernel.sequences import restore_sequence, save_sequence


@dataclass
class DiscoveryResult:
    present: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SelfTestResult:
    passed: bool
    message: str
    measurements: dict[str, Any] = field(default_factory=dict)


@dataclass
class SensorHealth:
    status: str
    consecutive_failures: int = 0
    message: str = ""


@dataclass
class RawObservation:
    payload: dict[str, Any]
    source_id: str
    bytes_len: int


class SensorError(Exception):
    """Plugin cannot run. Empty watchlist is an error, not a full PID scan."""


class BaseSensor(ABC):
    sensor_id: str = ""
    sensor_type: str = ""
    version: str = "1.0.0"
    schema_version: str = "1.0.0"
    capabilities: set[str] = set()

    def __init__(self, manifest: dict[str, Any]) -> None:
        self.manifest = manifest
        self.sensor_id = manifest["sensor_id"]
        self.sequence = restore_sequence(self.sensor_id)
        self.consecutive_failures = 0

    def next_sequence(self) -> int:
        self.sequence += 1
        save_sequence(self.sensor_id, self.sequence)
        return self.sequence

    @abstractmethod
    async def discover(self) -> DiscoveryResult: ...

    async def initialise(self, config: dict[str, Any]) -> None:
        return None

    @abstractmethod
    async def self_test(self) -> SelfTestResult: ...

    async def start(self) -> None:
        return None

    @abstractmethod
    async def observe(self) -> AsyncIterator[RawObservation]: ...

    async def health(self) -> SensorHealth:
        status = "healthy" if self.consecutive_failures == 0 else "degraded"
        return SensorHealth(status=status, consecutive_failures=self.consecutive_failures)

    async def set_rate(self, rate_hz: float) -> None:
        minimum = float(self.manifest.get("schedule", {}).get("minimum_interval_seconds", 1))
        maximum = float(self.manifest.get("schedule", {}).get("maximum_interval_seconds", 3600))
        interval = 1.0 / rate_hz if rate_hz > 0 else minimum
        if interval < minimum or interval > maximum:
            raise ValueError("rate outside signed schedule window")

    async def stop(self) -> None:
        return None

    async def reset(self) -> None:
        self.consecutive_failures = 0
        return None

    async def shutdown(self) -> None:
        await self.stop()
