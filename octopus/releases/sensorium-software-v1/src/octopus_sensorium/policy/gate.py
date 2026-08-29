"""Policy gate. Observations may publish; commands never execute on WAVE0_OBSERVE_ONLY."""

from __future__ import annotations

from typing import Any

from octopus_sensorium.policy.action_boundary import may_actuate
from octopus_sensorium.policy.command_gate import classify


class PolicyDenied(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def gate_observation(obs: dict[str, Any]) -> None:
    policy = obs.get("policy") or {}
    sensor_id = str(obs.get("sensor_id") or "")
    if may_actuate():
        raise PolicyDenied("actuator_authority leaked into observe-only kernel")
    if sensor_id in {"OCT-SENSE-092", "OCT-SENSE-095", "OCT-SENSE-096", "OCT-SENSE-097", "OCT-SENSE-099", "OCT-SENSE-100"}:
        if policy.get("actionable") or policy.get("may_change_readiness") or policy.get("may_quarantine"):
            raise PolicyDenied(f"{sensor_id} shadow output cannot be enforcing")
    if policy.get("may_change_readiness") or policy.get("may_quarantine"):
        raise PolicyDenied("observation cannot change readiness or quarantine")


def gate_command(command: str) -> str:
    decision = classify(command)
    if decision != "ALLOWLISTED_DEFERRED":
        raise PolicyDenied(decision)
    raise PolicyDenied("command_trust_root_not_bound")
