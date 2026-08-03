"""No-op telemetry with an in-memory tap for tests. Phase 3 swaps in OTel behind the same port."""

from __future__ import annotations

from typing import Mapping


class NoopTelemetry:
    def emit(self, name: str, value: float, tags: Mapping[str, str] | None = None) -> None:
        return None


class CapturingTelemetry:
    """Test double: remembers every metric emitted."""

    def __init__(self) -> None:
        self.records: list[tuple[str, float, dict[str, str]]] = []

    def emit(self, name: str, value: float, tags: Mapping[str, str] | None = None) -> None:
        self.records.append((name, value, dict(tags or {})))
