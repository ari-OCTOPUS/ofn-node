from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SignedCommand(BaseModel):
    """Wave 0 commands require every field; execution still waits for a bound command-trust root."""

    model_config = ConfigDict(extra="forbid")
    sender_id: str
    signature: str
    role: str
    permission: str
    timestamp: str
    expiry: str
    nonce: str
    command: str
    board_id: str | None = None
    request_id: str | None = None
    arguments: dict = Field(default_factory=dict)
