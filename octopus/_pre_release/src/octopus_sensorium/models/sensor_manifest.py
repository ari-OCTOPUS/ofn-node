from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SensorManifest(BaseModel):
    """Live registry entries may carry extra Wave 0 fields; unknown plugins are still refused at load."""

    model_config = ConfigDict(extra="allow")
    sensor_id: str
    name: str | None = None
    family: str | None = None
    sensor_type: str | None = None
    version: str | None = None
    schema_version: str | None = None
    status: str | None = None
    enabled: bool | None = None
    capabilities: list[str] | dict[str, Any] | None = None
    observed_properties: list[str] | None = None
    source_requirements: Any = None
    hardware_requirements: Any = None
    credential_requirements: Any = None
    consent_requirements: Any = None
    network_requirements: Any = None
    plugin: dict[str, Any] | None = None
    schedule: dict[str, Any] | None = None
    freshness: dict[str, Any] | None = None
    resources: dict[str, Any] | None = None
    security: dict[str, Any] = Field(default_factory=dict)
    failure: dict[str, Any] | None = None
    publication: dict[str, Any] | None = None
    dependencies: list[str] | None = None
    fusion_targets: list[str] | None = None
    implementation_wave: str | None = None
