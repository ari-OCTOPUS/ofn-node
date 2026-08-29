from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorldStateSnapshot(BaseModel):
    """Projected snapshot. Not a belief about the world and not an actuator permit."""

    model_config = ConfigDict(extra="allow")
    board_id: str | None = None
    health: dict[str, str] = Field(default_factory=dict)
    observations_published: int = 0
    invalid_observations: int = 0
    observation_hashes: list[str] = Field(default_factory=list)
    readiness_profile: str = "WAVE0_OBSERVE_ONLY"
    actuator_authority: str = "NONE"
    leg_authority: str = "DENIED"
    belief_engine: str = "NOT_ENABLED"
    extras: dict[str, Any] = Field(default_factory=dict)
