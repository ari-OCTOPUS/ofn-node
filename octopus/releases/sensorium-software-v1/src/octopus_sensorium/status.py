"""Split runtime, readiness, bus, acquisition, and safety. Do not collapse them into one state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RuntimeState = Literal["ACTIVE", "INACTIVE", "FAILED"]
ReadinessState = Literal["READY", "DEGRADED", "UNVERIFIED"]
BusState = Literal["CONNECTED", "ISOLATED"]
AcquisitionState = Literal["ACTIVE", "IDLE", "FAILED"]
SafetyState = Literal["SOFTWARE_ONLY", "MCU_BOUND", "FAILED_SAFE"]
ReadinessProfile = Literal["WAVE0_OBSERVE_ONLY"]


@dataclass
class BoardStatus:
    runtime_state: RuntimeState
    readiness_state: ReadinessState
    bus_state: BusState
    acquisition_state: AcquisitionState
    safety_state: SafetyState
    actuator_authority: str = "NONE"
    readiness_profile: ReadinessProfile = "WAVE0_OBSERVE_ONLY"
    operational_mode: str = "OBSERVE_ONLY"
    leg_authority: str = "DENIED"
    mqtt_state: str = "DISABLED"

    def as_dict(self) -> dict[str, str]:
        return {
            "runtime_state": self.runtime_state,
            "readiness_state": self.readiness_state,
            "readiness_profile": self.readiness_profile,
            "bus_state": self.bus_state,
            "acquisition_state": self.acquisition_state,
            "safety_state": self.safety_state,
            "operational_mode": self.operational_mode,
            "actuator_authority": self.actuator_authority,
            "leg_authority": self.leg_authority,
            "mqtt_state": self.mqtt_state,
        }

    def systemd_status(self) -> str:
        return (
            f"runtime={self.runtime_state} "
            f"readiness={self.readiness_state}/{self.readiness_profile} "
            f"bus={self.bus_state}"
        )
