from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence
import uuid


@dataclass(frozen=True)
class State:
    compute_pressure: float
    memory_pressure: float
    thermal_celsius: float
    storage_pressure: float
    evidence_age_s: float
    sensor_coverage: float

    def as_dict(self) -> dict[str, float]:
        return {
            "compute_pressure": self.compute_pressure,
            "memory_pressure": self.memory_pressure,
            "thermal_celsius": self.thermal_celsius,
            "storage_pressure": self.storage_pressure,
            "evidence_age_s": self.evidence_age_s,
            "sensor_coverage": self.sensor_coverage,
        }


@dataclass(frozen=True)
class Action:
    name: str
    intensity: float = 1.0


@dataclass(frozen=True)
class PredictedState:
    mean: State
    uncertainty: float


@dataclass(frozen=True)
class Prediction:
    prediction_id: str
    domain: str
    horizon_s: int
    issued_at_ns: int
    state_hash: str
    action: str
    mean: Mapping[str, float]
    uncertainty: Mapping[str, float]
    model_version: str


class WorldModel(Protocol):
    version: str

    def predict(self, state: State, action: Action) -> PredictedState: ...

    def rollout(self, state: State, actions: Sequence[Action]) -> list[PredictedState]: ...


class PersistenceModel:
    """Baseline: next state equals current state. Not a neural world model."""

    version = "persistence-v1"

    def predict(
        self,
        domain: str,
        state: Mapping[str, float],
        action: str,
        issued_at_ns: int,
        state_hash: str,
        horizon_s: int = 30,
    ) -> Prediction:
        return Prediction(
            prediction_id=f"pred-{uuid.uuid4().hex}",
            domain=domain,
            horizon_s=horizon_s,
            issued_at_ns=issued_at_ns,
            state_hash=state_hash,
            action=action,
            mean=dict(state),
            uncertainty={key: 0.0 for key in state},
            model_version=self.version,
        )
