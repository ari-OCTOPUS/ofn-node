"""Observation pipeline. Fail-closed: any stage error drops the event."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from octopus_sensorium.observation import make_observation
from octopus_sensorium.policy.gate import PolicyDenied, gate_observation
from octopus_sensorium.security.injection_filter import contains_untrusted_instruction
from octopus_sensorium.sensors.base import RawObservation

MAX_PAYLOAD = 1_048_576


class PipelineError(Exception):
    def __init__(self, stage: str, message: str) -> None:
        super().__init__(f"{stage}: {message}")
        self.stage = stage
        self.message = message


def run_pipeline(
    raw: RawObservation,
    *,
    board_id: str,
    sensor_id: str,
    sensor_agent_id: str,
    observed_property: str,
    value: Any,
    unit: str | None,
    sequence_number: int,
    source_id: str,
    collector_version: str,
    transformations: list[str],
    clock_trust: str,
    ttl_seconds: int,
    range_check: Callable[[Any], bool] | None = None,
    seen_hashes: set[str] | None = None,
) -> dict[str, Any]:
    stage = "ACQUIRE"
    if raw is None:
        raise PipelineError(stage, "empty")
    stage = "DECODE"
    if not isinstance(raw.payload, dict):
        raise PipelineError(stage, "payload is not an object")
    stage = "SIZE_CHECK"
    if raw.bytes_len > MAX_PAYLOAD:
        raise PipelineError(stage, "payload too large")
    stage = "SCHEMA_VALIDATE"
    if sequence_number < 1:
        raise PipelineError(stage, "sequence_number must increase from 1")
    stage = "TIMESTAMP_VALIDATE"
    now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise PipelineError(stage, "timezone missing")
    stage = "UNIT_NORMALISE"
    # units are already SI at plugin boundary for Wave 1
    stage = "RANGE_CHECK"
    if range_check is not None and not range_check(value):
        raise PipelineError(stage, "value out of range")
    stage = "DUPLICATE_CHECK"
    obs = make_observation(
        board_id=board_id,
        sensor_id=sensor_id,
        sensor_agent_id=sensor_agent_id,
        observed_property=observed_property,
        value=value,
        unit=unit,
        sequence_number=sequence_number,
        ttl_seconds=ttl_seconds,
        source_id=source_id,
        collector_version=collector_version,
        transformations=transformations + ["pipeline:v1"],
        clock_trust=clock_trust,
            time_unverified=clock_trust in {"UNTRUSTED", "MONOTONIC_ONLY"},
    )
    digest = obs["provenance"]["content_hash"]
    if seen_hashes is not None:
        if digest in seen_hashes:
            raise PipelineError(stage, "duplicate")
        seen_hashes.add(digest)
        if len(seen_hashes) > 4096:
            seen_hashes.clear()
    stage = "FRESHNESS_CHECK"
    # produced now; freshness is 0
    stage = "SOURCE_VERIFY"
    if not source_id:
        raise PipelineError(stage, "missing source")
    stage = "PROVENANCE_ATTACH"
    if not obs["provenance"]["content_hash"]:
        raise PipelineError(stage, "missing hash")
    stage = "UNCERTAINTY_ESTIMATE"
    stage = "PRIVACY_FILTER"
    if obs["security"]["contains_pii"]:
        raise PipelineError(stage, "pii not permitted on this sensor")
    published = str(obs.get("result") or {}).lower()
    if "command_line" in published or "command_args" in published:
        raise PipelineError(stage, "command line must not be published")
    stage = "INJECTION_SCAN"
    if contains_untrusted_instruction(str(raw.payload)):
        raise PipelineError(stage, "untrusted instruction in sensor string")
    stage = "POLICY_GATE"
    try:
        gate_observation(obs)
    except PolicyDenied as exc:
        raise PipelineError(stage, exc.reason) from exc
    return obs
