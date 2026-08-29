"""In-process counters. OpenTelemetry exporters are not enabled (OCT-SENSE-055/056 remain not_enabled)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InProcessMetrics:
    sensorium_board_up: int = 1
    sensorium_runtime_state: str = "ACTIVE"
    sensorium_readiness_state: str = "UNVERIFIED"
    sensorium_bus_connected: int = 0
    sensorium_acquisition_active: int = 0
    sensorium_active_sensors: int = 0
    sensorium_degraded_sensors: int = 0
    sensorium_quarantined_sensors: int = 0
    sensorium_observations_total: int = 0
    sensorium_invalid_observations_total: int = 0
    sensorium_nats_reconnect_total: int = 0
    sensorium_offline_buffer_depth: int = 0
    sensorium_evidence_chain_valid: int = 1
    sensorium_audit_chain_valid: int = 1
    sensorium_replay_hash_match: int = 1
    sensorium_open_contradictions: int = 0
    sensorium_anomalies_total: int = 0
    sensorium_uncertainty_score: float = 0.0
    sensorium_novelty_total: int = 0
    sensorium_provenance_invalid_total: int = 0
    sensorium_policy_violations_total: int = 0
    sensorium_unauthorized_leg_birth_total: int = 0
    observations_published: int = 0
    invalid_observations: int = 0
    nats_disconnects: int = 0
    pipeline_drops: dict[str, int] = field(default_factory=dict)

    def drop(self, stage: str) -> None:
        self.pipeline_drops[stage] = self.pipeline_drops.get(stage, 0) + 1
        self.invalid_observations += 1
        self.sensorium_invalid_observations_total += 1

    def as_dict(self) -> dict[str, object]:
        return {
            "sensorium_board_up": self.sensorium_board_up,
            "sensorium_runtime_state": self.sensorium_runtime_state,
            "sensorium_readiness_state": self.sensorium_readiness_state,
            "sensorium_bus_connected": self.sensorium_bus_connected,
            "sensorium_acquisition_active": self.sensorium_acquisition_active,
            "sensorium_active_sensors": self.sensorium_active_sensors,
            "sensorium_degraded_sensors": self.sensorium_degraded_sensors,
            "sensorium_quarantined_sensors": self.sensorium_quarantined_sensors,
            "sensorium_observations_total": self.sensorium_observations_total,
            "sensorium_invalid_observations_total": self.sensorium_invalid_observations_total,
            "sensorium_nats_reconnect_total": self.sensorium_nats_reconnect_total,
            "sensorium_offline_buffer_depth": self.sensorium_offline_buffer_depth,
            "sensorium_evidence_chain_valid": self.sensorium_evidence_chain_valid,
            "sensorium_audit_chain_valid": self.sensorium_audit_chain_valid,
            "sensorium_replay_hash_match": self.sensorium_replay_hash_match,
            "sensorium_open_contradictions": self.sensorium_open_contradictions,
            "sensorium_anomalies_total": self.sensorium_anomalies_total,
            "sensorium_uncertainty_score": self.sensorium_uncertainty_score,
            "sensorium_novelty_total": self.sensorium_novelty_total,
            "sensorium_provenance_invalid_total": self.sensorium_provenance_invalid_total,
            "sensorium_policy_violations_total": self.sensorium_policy_violations_total,
            "sensorium_unauthorized_leg_birth_total": self.sensorium_unauthorized_leg_birth_total,
        }
