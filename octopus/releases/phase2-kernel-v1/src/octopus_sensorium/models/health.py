from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SensorHealthRecord(BaseModel):
    model_config = ConfigDict(extra="allow")
    sensor_id: str
    status: Literal["healthy", "degraded", "quarantine", "unavailable", "not_enabled"]
    consecutive_failures: int = 0
    message: str = ""
    can_self_release_quarantine: bool = False
    plugin_state: str | None = None


class BoardHealth(BaseModel):
    model_config = ConfigDict(extra="allow")
    board_id: str
    runtime_state: str
    readiness_state: str
    readiness_profile: str = "WAVE0_OBSERVE_ONLY"
    sensors: list[SensorHealthRecord] = Field(default_factory=list)
