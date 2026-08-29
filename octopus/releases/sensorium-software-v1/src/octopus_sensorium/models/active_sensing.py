from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ActiveSensingRequest(BaseModel):
    """Active sensing is not armed on WAVE0_OBSERVE_ONLY."""

    model_config = ConfigDict(extra="allow")
    sensor_id: str
    requested_rate_hz: float | None = None
    armed: bool = False
    allowed: bool = False
    reason: str = "WAVE0_OBSERVE_ONLY"
