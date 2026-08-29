"""Plugin lifecycle. A plugin must not release its own quarantine."""

from __future__ import annotations

from enum import Enum

from octopus_sensorium.kernel.errors import PluginLifecycleError


class PluginState(str, Enum):
    DISCOVERED = "DISCOVERED"
    VERIFIED = "VERIFIED"
    INITIALISED = "INITIALISED"
    SELF_TESTED = "SELF_TESTED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    UNAVAILABLE = "UNAVAILABLE"


_ALLOWED: dict[PluginState, set[PluginState]] = {
    PluginState.DISCOVERED: {PluginState.VERIFIED, PluginState.FAILED, PluginState.UNAVAILABLE, PluginState.QUARANTINED},
    PluginState.VERIFIED: {PluginState.INITIALISED, PluginState.FAILED, PluginState.QUARANTINED},
    PluginState.INITIALISED: {PluginState.SELF_TESTED, PluginState.FAILED, PluginState.QUARANTINED},
    PluginState.SELF_TESTED: {PluginState.ACTIVE, PluginState.FAILED, PluginState.QUARANTINED},
    PluginState.ACTIVE: {
        PluginState.DEGRADED,
        PluginState.QUARANTINED,
        PluginState.FAILED,
        PluginState.ACTIVE,
    },
    PluginState.DEGRADED: {PluginState.ACTIVE, PluginState.QUARANTINED, PluginState.FAILED},
    PluginState.QUARANTINED: {PluginState.AWAITING_APPROVAL, PluginState.FAILED},
    PluginState.FAILED: {PluginState.AWAITING_APPROVAL},
    PluginState.AWAITING_APPROVAL: {PluginState.VERIFIED, PluginState.FAILED, PluginState.QUARANTINED},
    PluginState.UNAVAILABLE: {PluginState.DISCOVERED, PluginState.FAILED},
}


class PluginLifecycle:
    def __init__(self) -> None:
        self.states: dict[str, PluginState] = {}

    def mark(self, sensor_id: str, target: PluginState) -> PluginState:
        current = self.states.get(sensor_id)
        if current is None:
            if target != PluginState.DISCOVERED:
                raise PluginLifecycleError(f"{sensor_id}: first state must be DISCOVERED, got {target.value}")
            self.states[sensor_id] = target
            return target
        allowed = _ALLOWED.get(current, set())
        if target not in allowed:
            raise PluginLifecycleError(f"{sensor_id}: {current.value} -> {target.value} is not allowed")
        self.states[sensor_id] = target
        return target

    def release_quarantine(self, sensor_id: str, *, human_approved: bool) -> PluginState:
        if not human_approved:
            raise PluginLifecycleError(f"{sensor_id}: plugin cannot self-release quarantine")
        if self.states.get(sensor_id) != PluginState.QUARANTINED:
            raise PluginLifecycleError(f"{sensor_id}: not quarantined")
        return self.mark(sensor_id, PluginState.AWAITING_APPROVAL)
