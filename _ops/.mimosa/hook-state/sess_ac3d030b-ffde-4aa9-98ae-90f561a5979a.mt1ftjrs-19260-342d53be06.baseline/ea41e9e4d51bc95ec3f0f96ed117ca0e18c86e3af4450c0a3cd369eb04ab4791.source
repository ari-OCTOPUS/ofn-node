#!/usr/bin/env python3
"""agent_circuit.py -- Per-agent circuit breaker for loop/retry storm detection (EQUIP G8).

Extends the existing per-target circuit breaker pattern to detect when an agent
enters a loop storm: too many actions in a short window, or too many retries
without making progress.

Design:
  - Per-agent state: tracks action count and retry count in sliding windows
  - Trip conditions: action rate > threshold, retry rate > threshold
  - Fail-closed: unknown state = circuit open (safer)
  - Kill-aware: once kill is active, circuit stays open permanently
  - State is stored as a simple dict (pluggable storage for production)

$0 | stdlib-only | no network | no external dependencies
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA = "agent-circuit.v1"


class AgentState(str, Enum):
    """Agent circuit states."""
    ACTIVE = "active"       # Normal operation
    DEGRADED = "degraded"   # High retry rate, warnings issued
    OPEN = "open"           # Blocked -- too many actions or retries
    KILLED = "killed"       # Kill switch active -- permanently open


@dataclass
class AgentCircuitState:
    """Per-agent circuit breaker state."""
    agent_id: str
    state: AgentState = AgentState.ACTIVE
    # Sliding window tracking (timestamps of recent actions)
    action_timestamps: list[float] = field(default_factory=list)
    retry_timestamps: list[float] = field(default_factory=list)
    # Counters
    total_actions: int = 0
    total_retries: int = 0
    total_denied: int = 0
    # Trip info
    opened_at: float | None = None
    open_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "action_timestamps": self.action_timestamps[-50:],  # last 50
            "retry_timestamps": self.retry_timestamps[-50:],
            "total_actions": self.total_actions,
            "total_retries": self.total_retries,
            "total_denied": self.total_denied,
            "opened_at": self.opened_at,
            "open_reason": self.open_reason,
        }


# Default thresholds (configurable)
DEFAULT_THRESHOLDS = {
    "max_actions_per_minute": 60,     # >60 actions/min = potential storm
    "max_retries_per_minute": 20,     # >20 retries/min = retry storm
    "max_actions_per_5min": 200,     # >200 in 5min = sustained storm
    "cooldown_seconds": 30,           # How long circuit stays open
    "degraded_retry_rate": 10,       # Retries/min for degraded state
}


def _clean_window(timestamps: list[float], window_seconds: float) -> list[float]:
    """Remove timestamps older than window."""
    cutoff = time.time() - window_seconds
    return [ts for ts in timestamps if ts > cutoff]


def _rate_per_minute(timestamps: list[float], window_seconds: float = 60) -> float:
    """Calculate events per minute in the sliding window.

    When all events are within 1 second (burst), the window_seconds is used
    as the denominator to avoid inflating the rate. This means a burst of N
    events in <1s is counted as N events per window_seconds, not N*60/min.
    """
    cleaned = _clean_window(timestamps, window_seconds)
    if not cleaned:
        return 0.0
    span = cleaned[-1] - cleaned[0]
    if span < 1.0:
        span = window_seconds  # burst: use full window as denominator
    else:
        span = min(span, window_seconds)  # cap at window size
    return len(cleaned) / (span / 60.0)


def check_agent(agent_state: AgentCircuitState,
                thresholds: dict | None = None) -> dict:
    """Check agent circuit breaker state.

    Returns:
        {allow: bool, state: str, reason: str, action_rate: float, retry_rate: float}
    """
    thr = thresholds or DEFAULT_THRESHOLDS

    # If killed, always deny
    if agent_state.state == AgentState.KILLED:
        return {"allow": False, "state": AgentState.KILLED.value,
                "reason": "agent_killed:permanent_block",
                "action_rate": 0.0, "retry_rate": 0.0}

    # If already open, check cooldown
    if agent_state.state == AgentState.OPEN:
        if agent_state.opened_at is not None:
            elapsed = time.time() - agent_state.opened_at
            if elapsed >= thr["cooldown_seconds"]:
                # Auto-recover to active
                agent_state.state = AgentState.ACTIVE
                agent_state.opened_at = None
                agent_state.open_reason = ""
                agent_state.action_timestamps.clear()
                agent_state.retry_timestamps.clear()
                return {"allow": True, "state": AgentState.ACTIVE.value,
                        "reason": "cooldown_elapsed:recovered",
                        "action_rate": 0.0, "retry_rate": 0.0}
            return {"allow": False, "state": AgentState.OPEN.value,
                    "reason": f"circuit_open:cooldown_remaining={int(thr['cooldown_seconds'] - elapsed)}s",
                    "action_rate": _rate_per_minute(agent_state.action_timestamps),
                    "retry_rate": _rate_per_minute(agent_state.retry_timestamps)}

    # Clean windows
    agent_state.action_timestamps = _clean_window(
        agent_state.action_timestamps, 300)  # 5-minute window
    agent_state.retry_timestamps = _clean_window(
        agent_state.retry_timestamps, 60)  # 1-minute window

    action_rate_1m = _rate_per_minute(agent_state.action_timestamps, 60)
    action_rate_5m = _rate_per_minute(agent_state.action_timestamps, 300)
    retry_rate_1m = _rate_per_minute(agent_state.retry_timestamps, 60)

    # Check trip conditions
    if action_rate_1m > thr["max_actions_per_minute"]:
        agent_state.state = AgentState.OPEN
        agent_state.opened_at = time.time()
        agent_state.open_reason = f"action_rate_1m={action_rate_1m:.0f}>{thr['max_actions_per_minute']}"
        agent_state.total_denied += 1
        return {"allow": False, "state": AgentState.OPEN.value,
                "reason": agent_state.open_reason,
                "action_rate": action_rate_1m, "retry_rate": retry_rate_1m}

    if action_rate_5m > thr["max_actions_per_5min"]:
        agent_state.state = AgentState.OPEN
        agent_state.opened_at = time.time()
        agent_state.open_reason = f"action_rate_5m={action_rate_5m:.0f}>{thr['max_actions_per_5min']}"
        agent_state.total_denied += 1
        return {"allow": False, "state": AgentState.OPEN.value,
                "reason": agent_state.open_reason,
                "action_rate": action_rate_5m, "retry_rate": retry_rate_1m}

    if retry_rate_1m > thr["max_retries_per_minute"]:
        agent_state.state = AgentState.OPEN
        agent_state.opened_at = time.time()
        agent_state.open_reason = f"retry_rate_1m={retry_rate_1m:.0f}>{thr['max_retries_per_minute']}"
        agent_state.total_denied += 1
        return {"allow": False, "state": AgentState.OPEN.value,
                "reason": agent_state.open_reason,
                "action_rate": action_rate_1m, "retry_rate": retry_rate_1m}

    # Degraded state check (warning, not blocking)
    if retry_rate_1m > thr.get("degraded_retry_rate", 10):
        if agent_state.state == AgentState.ACTIVE:
            agent_state.state = AgentState.DEGRADED

    return {"allow": True, "state": agent_state.state.value,
            "reason": "within_thresholds",
            "action_rate": action_rate_1m, "retry_rate": retry_rate_1m}


def record_action(agent_state: AgentCircuitState,
                  is_retry: bool = False) -> dict:
    """Record an action attempt. Returns updated circuit check."""
    now = time.time()
    agent_state.action_timestamps.append(now)
    agent_state.total_actions += 1
    if is_retry:
        agent_state.retry_timestamps.append(now)
        agent_state.total_retries += 1
    return check_agent(agent_state)


def kill_agent(agent_state: AgentCircuitState) -> dict:
    """Kill an agent -- permanently open circuit, no recovery."""
    agent_state.state = AgentState.KILLED
    agent_state.opened_at = time.time()
    agent_state.open_reason = "kill_switch_activated"
    return {"allow": False, "state": AgentState.KILLED.value,
            "reason": "kill_switch_activated",
            "agent_id": agent_state.agent_id}


def is_agent_killed(agent_state: AgentCircuitState) -> bool:
    """Check if agent is in killed state (independent of LLM)."""
    return agent_state.state == AgentState.KILLED


if __name__ == "__main__":
    # Demo
    state = AgentCircuitState(agent_id="test-agent")
    print("Initial:", check_agent(state))

    # Simulate actions
    for i in range(65):
        record_action(state, is_retry=(i % 3 == 0))
    result = check_agent(state)
    print(f"After 65 actions (some retries): {result}")

    # Kill
    kill_agent(state)
    print("After kill:", check_agent(state))
