from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ContradictionEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    event_id: str
    sensor_id: str = "OCT-SENSE-095"
    observation_type: str = "contradiction"
    rule_id: str | None = None
    status: str | None = None
    can_resolve_belief: bool = False
    actionable: bool = False
    policy: dict = Field(default_factory=dict)
