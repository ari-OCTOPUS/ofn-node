"""Pydantic v2 models for the universal Observation envelope."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from octopus_sensorium.models.provenance import Provenance
from octopus_sensorium.models.uncertainty import Uncertainty

OBSERVATION_TYPES = (
    "measurement",
    "state",
    "event",
    "anomaly",
    "contradiction",
    "prediction",
    "fault",
)


class Subject(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    entity_type: str = "sensorium_board"


class Result(BaseModel):
    model_config = ConfigDict(extra="allow")
    value: Any = None
    unit: str | None = None
    encoding: Literal["json"] = "json"


class ObservationTime(BaseModel):
    model_config = ConfigDict(extra="allow")
    phenomenon_time: str
    ingestion_time: str
    processing_time: str
    valid_until: str
    time_unverified: bool = False


class Quality(BaseModel):
    model_config = ConfigDict(extra="allow")
    valid: bool = True
    confidence: float = 0.0
    completeness: float = 0.0
    freshness_seconds: int = 0
    calibration_status: str = "not_applicable"
    time_unverified: bool = False


class Evidence(BaseModel):
    model_config = ConfigDict(extra="allow")
    evidence_chain_id: str | None = None
    supporting_event_ids: list[str] = Field(default_factory=list)
    opposing_event_ids: list[str] = Field(default_factory=list)


class Security(BaseModel):
    model_config = ConfigDict(extra="allow")
    classification: Literal["public", "internal", "personal", "health"] = "internal"
    contains_pii: bool = False
    consent_id: str | None = None
    untrusted_content: bool = False
    redaction_applied: bool = False


class Routing(BaseModel):
    model_config = ConfigDict(extra="allow")
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    allowed_consumers: list[str] = Field(default_factory=list)
    raw_available: bool = False


class Policy(BaseModel):
    model_config = ConfigDict(extra="allow")
    actionable: bool = False
    may_change_readiness: bool = False
    may_quarantine: bool = False
    human_approval_required: bool = True


class Observation(BaseModel):
    """Universal L1 envelope. Extra plugin fields (scope, subsensor_id) are allowed."""

    model_config = ConfigDict(extra="allow")
    event_id: str
    schema_version: str
    sequence_number: int
    sensorium_board_id: str
    sensor_id: str
    subsensor_id: str | None = None
    sensor_agent_id: str
    observation_type: Literal[
        "measurement", "state", "event", "anomaly", "contradiction", "prediction", "fault"
    ] = "measurement"
    observed_property: str
    subject: Subject
    result: Result
    time: ObservationTime
    quality: Quality
    uncertainty: Uncertainty
    provenance: Provenance
    evidence: Evidence = Field(default_factory=Evidence)
    security: Security
    routing: Routing
    policy: Policy = Field(default_factory=Policy)
