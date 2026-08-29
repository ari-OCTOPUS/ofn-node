"""Agent state machine. READY is a gate, not a courtesy title."""

from __future__ import annotations

from enum import Enum


class AgentState(str, Enum):
    BOOTING = "BOOTING"
    SELF_TEST = "SELF_TEST"
    CONNECTING = "CONNECTING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    ISOLATED = "ISOLATED"
    QUARANTINE = "QUARANTINE"
    MAINTENANCE = "MAINTENANCE"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    FAILED_SAFE = "FAILED_SAFE"


_ALLOWED = {
    AgentState.BOOTING: {AgentState.SELF_TEST, AgentState.FAILED_SAFE, AgentState.DEGRADED},
    AgentState.SELF_TEST: {AgentState.CONNECTING, AgentState.FAILED_SAFE, AgentState.DEGRADED},
    AgentState.CONNECTING: {AgentState.READY, AgentState.DEGRADED, AgentState.ISOLATED, AgentState.FAILED_SAFE},
    AgentState.READY: {AgentState.ACTIVE, AgentState.DEGRADED, AgentState.FAILED_SAFE, AgentState.SHUTTING_DOWN},
    AgentState.ACTIVE: {
        AgentState.DEGRADED,
        AgentState.ISOLATED,
        AgentState.QUARANTINE,
        AgentState.FAILED_SAFE,
        AgentState.SHUTTING_DOWN,
        AgentState.MAINTENANCE,
    },
    AgentState.DEGRADED: {
        AgentState.READY,
        AgentState.SELF_TEST,
        AgentState.FAILED_SAFE,
        AgentState.SHUTTING_DOWN,
        AgentState.ISOLATED,
    },
    AgentState.ISOLATED: {AgentState.DEGRADED, AgentState.CONNECTING, AgentState.FAILED_SAFE, AgentState.SHUTTING_DOWN},
    AgentState.QUARANTINE: {AgentState.DEGRADED, AgentState.FAILED_SAFE, AgentState.MAINTENANCE, AgentState.SHUTTING_DOWN},
    AgentState.MAINTENANCE: {AgentState.SELF_TEST, AgentState.DEGRADED, AgentState.FAILED_SAFE, AgentState.SHUTTING_DOWN},
    AgentState.SHUTTING_DOWN: {AgentState.FAILED_SAFE},
    AgentState.FAILED_SAFE: set(),
}


class IllegalTransition(Exception):
    pass


class StateMachine:
    def __init__(self) -> None:
        self.state = AgentState.BOOTING

    def transition(self, target: AgentState) -> AgentState:
        if target == AgentState.FAILED_SAFE:
            self.state = target
            return self.state
        allowed = _ALLOWED.get(self.state, set())
        if target not in allowed:
            raise IllegalTransition(f"{self.state.value} -> {target.value} is not allowed")
        self.state = target
        return self.state
