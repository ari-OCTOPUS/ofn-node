"""L1 Observation factory. LLM output must never use this without a traceable source."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from octopus_sensorium import SCHEMA_VERSION
from octopus_sensorium.evidence.canonical_json import canonical_json
from octopus_sensorium.evidence.content_hash import content_hash
from octopus_sensorium.models.observation import Observation


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def make_observation(
    *,
    board_id: str,
    sensor_id: str,
    sensor_agent_id: str,
    observed_property: str,
    value: Any,
    unit: str | None,
    sequence_number: int,
    phenomenon_time: datetime | None = None,
    ttl_seconds: int = 30,
    confidence: float = 1.0,
    completeness: float = 1.0,
    calibration_status: str = "unknown",
    uncertainty_type: str = "aleatoric",
    uncertainty_score: float = 0.0,
    uncertainty_method: str = "device_repeatability",
    source_id: str,
    collector_version: str,
    transformations: list[str],
    classification: str = "internal",
    contains_pii: bool = False,
    clock_trust: str,
    time_unverified: bool = False,
    valid: bool = True,
    priority: str = "normal",
    allowed_consumers: list[str] | None = None,
    subject: dict[str, str] | None = None,
    scope: str = "board_internal",
    is_environment_feature: bool = False,
    subsensor_id: str | None = None,
    observation_type: str = "measurement",
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    phen = phenomenon_time or now
    payload_for_hash = {
        "sensor_id": sensor_id,
        "observed_property": observed_property,
        "value": value,
        "unit": unit,
        "phenomenon_time": _iso(phen),
        "sequence_number": sequence_number,
    }
    raw = canonical_json(payload_for_hash)
    obs = {
        "event_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "sequence_number": sequence_number,
        "sensorium_board_id": board_id,
        "sensor_id": sensor_id,
        "sensor_agent_id": sensor_agent_id,
        "observation_type": observation_type,
        "observed_property": observed_property,
        "subject": subject or {"entity_id": board_id, "entity_type": "sensorium_board"},
        "result": {"value": value, "unit": unit, "encoding": "json"},
        "time": {
            "phenomenon_time": _iso(phen),
            "ingestion_time": _iso(now),
            "processing_time": _iso(now),
            "valid_until": _iso(now + timedelta(seconds=ttl_seconds)),
            "time_unverified": time_unverified,
        },
        "quality": {
            "valid": valid,
            "confidence": confidence,
            "completeness": completeness,
            "freshness_seconds": max(0, int((now - phen).total_seconds())),
            "calibration_status": calibration_status,
            "time_unverified": time_unverified,
        },
        "uncertainty": {
            "type": uncertainty_type,
            "score": uncertainty_score,
            "method": uncertainty_method,
        },
        "provenance": {
            "source_id": source_id,
            "collector_version": collector_version,
            "transformations": transformations,
            "content_hash": content_hash(raw),
            "signature_verified": False,
            "clock_trust": clock_trust,
        },
        "evidence": {
            "evidence_chain_id": None,
            "supporting_event_ids": [],
            "opposing_event_ids": [],
        },
        "security": {
            "classification": classification,
            "contains_pii": contains_pii,
            "consent_id": None,
            "untrusted_content": False,
            "redaction_applied": False,
        },
        "routing": {
            "priority": priority,
            "allowed_consumers": allowed_consumers or ["octopus-core"],
            "raw_available": False,
        },
        "policy": {
            "actionable": False,
            "may_change_readiness": False,
            "may_quarantine": False,
            "human_approval_required": True,
        },
        "scope": scope,
        "is_environment_feature": is_environment_feature,
        "subsensor_id": subsensor_id or sensor_id,
    }
    return Observation.model_validate(obs).model_dump()


def monotonic_ns() -> int:
    return time.monotonic_ns()
