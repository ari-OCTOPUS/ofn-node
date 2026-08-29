"""Shadow-only action × state candidate. Never imported by live Policy or planner.

persistence-v1 remains the live baseline. This model is evaluated offline against
the same outcomes. It must not be wired into octopus-world-model.service.
"""

from __future__ import annotations

from typing import Mapping

from octopus_cognition.world_model.contracts import PersistenceModel, Prediction

VERSION = "interaction-meanrev-v1"

# Documented attractor for the candidate only. Not applied to the host.
# sensor_coverage attractor is the live 4/6 ratio, not 1.0 (would impute missing sensors).
ATTRACTOR = {
    "compute_pressure": 0.10,
    "memory_pressure": 0.20,
    "storage_integrity": 0.05,
    "sensor_coverage": 0.6667,
}

# Gain is action-specific so delta(action, state) depends on both.
ACTION_GAIN = {
    "NO_ACTION_OBSERVE_ONLY": {
        "compute_pressure": 0.12,
        "memory_pressure": 0.08,
        "storage_integrity": 0.02,
        "sensor_coverage": 0.00,
    },
    "NO_ACTION": {
        "compute_pressure": 0.12,
        "memory_pressure": 0.08,
        "storage_integrity": 0.02,
        "sensor_coverage": 0.00,
    },
    "ADVISORY_THROTTLE": {
        "compute_pressure": 0.40,
        "memory_pressure": 0.10,
        "storage_integrity": 0.02,
        "sensor_coverage": 0.00,
    },
    "ADVISORY_RESTART": {
        "compute_pressure": 0.08,
        "memory_pressure": 0.08,
        "storage_integrity": 0.02,
        "sensor_coverage": 0.25,
    },
}


def delta(state: Mapping[str, float], action: str) -> dict[str, float]:
    gains = ACTION_GAIN.get(action) or ACTION_GAIN["NO_ACTION_OBSERVE_ONLY"]
    out: dict[str, float] = {}
    for key, value in state.items():
        gain = float(gains.get(key, 0.0))
        target = float(ATTRACTOR.get(key, value))
        out[key] = gain * (target - float(value))
    return out


def apply_delta(state: Mapping[str, float], action: str) -> dict[str, float]:
    d = delta(state, action)
    return {key: float(state[key]) + d[key] for key in state}


class InteractionMeanReversionModel:
    """Candidate: next = state + gain(action) * (attractor - state)."""

    version = VERSION

    def predict(
        self,
        domain: str,
        state: Mapping[str, float],
        action: str,
        issued_at_ns: int,
        state_hash: str,
        horizon_s: int = 30,
    ) -> Prediction:
        mean = apply_delta(state, action)
        return Prediction(
            prediction_id=f"cand-{issued_at_ns}",
            domain=domain,
            horizon_s=horizon_s,
            issued_at_ns=issued_at_ns,
            state_hash=state_hash,
            action=action,
            mean=mean,
            uncertainty={key: abs(delta(state, action)[key]) for key in state},
            model_version=self.version,
        )


def persistence_delta(state: Mapping[str, float], action: str) -> dict[str, float]:
    del action
    return {key: 0.0 for key in state}


def interaction_guard(action: str = "NO_ACTION_OBSERVE_ONLY") -> dict[str, object]:
    state_a = {
        "compute_pressure": 0.05,
        "memory_pressure": 0.10,
        "storage_integrity": 0.04,
        "sensor_coverage": 0.50,
    }
    state_b = {
        "compute_pressure": 0.40,
        "memory_pressure": 0.35,
        "storage_integrity": 0.12,
        "sensor_coverage": 0.6667,
    }
    cand_a = delta(state_a, action)
    cand_b = delta(state_b, action)
    base_a = persistence_delta(state_a, action)
    base_b = persistence_delta(state_b, action)
    cand_differs = cand_a != cand_b
    persistence_blind = base_a == base_b
    return {
        "action": action,
        "state_a": state_a,
        "state_b": state_b,
        "candidate_delta_a": cand_a,
        "candidate_delta_b": cand_b,
        "persistence_delta_a": base_a,
        "persistence_delta_b": base_b,
        "candidate_interaction": cand_differs,
        "persistence_is_interaction_blind": persistence_blind,
        "pass": cand_differs,
        "persistence_fails_this_guard": persistence_blind,
        "baseline_model": PersistenceModel.version,
        "candidate_model": VERSION,
    }
