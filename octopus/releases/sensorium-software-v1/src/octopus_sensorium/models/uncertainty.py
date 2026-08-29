from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Uncertainty(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal["aleatoric", "epistemic", "mixed", "unknown"] = "unknown"
    score: float = 0.0
    method: str = "unspecified"
