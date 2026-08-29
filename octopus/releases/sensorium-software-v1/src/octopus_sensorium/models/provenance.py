"""Provenance attached to every Observation. signature_verified is true only after a real verify."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Provenance(BaseModel):
    model_config = ConfigDict(extra="allow")
    source_id: str
    collector_version: str
    transformations: list[str] = Field(default_factory=list)
    content_hash: str
    signature_verified: bool = False
    clock_trust: str = "UNTRUSTED"
