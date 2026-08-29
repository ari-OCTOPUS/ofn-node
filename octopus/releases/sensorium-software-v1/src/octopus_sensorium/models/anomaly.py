from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AnomalyBody(BaseModel):
    model_config = ConfigDict(extra="allow")
    anomaly_id: str
    detector: str
    klass: str = Field(alias="class", default="unspecified")
    severity: str
    score: float
    threshold: float | None = None
    direction: str | None = None


class AnomalyEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    event_id: str
    sensor_id: str = "OCT-SENSE-092"
    observation_type: str = "anomaly"
    anomaly: AnomalyBody | None = None
    actionable: bool = False
    policy: dict = Field(default_factory=dict)
