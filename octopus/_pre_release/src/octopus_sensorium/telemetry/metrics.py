"""In-process counters. OpenTelemetry exporters are not enabled (OCT-SENSE-055/056 remain not_enabled)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InProcessMetrics:
    observations_published: int = 0
    invalid_observations: int = 0
    nats_disconnects: int = 0
    pipeline_drops: dict[str, int] = field(default_factory=dict)

    def drop(self, stage: str) -> None:
        self.pipeline_drops[stage] = self.pipeline_drops.get(stage, 0) + 1
        self.invalid_observations += 1
