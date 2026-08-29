"""Time-bounded authority leases. Levels above A1 exist only as expiring leases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


STABLE_LEVELS = frozenset({"AUTHORITY_NONE", "A0", "A1"})
LEASE_REQUIRED_LEVELS = frozenset({"A2", "A3", "A4", "A5"})

AUTO_REVOKE_ON = (
    "telemetry_gap",
    "watchdog_timeout",
    "clock_anomaly",
    "ledger_failure",
    "doctor_not_pass",
    "lease_expiry",
    "budget_exhausted",
)


class LeaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthorityLease:
    schema: str
    lease_id: str
    level: str
    actuator_allowlist: tuple[str, ...]
    max_commands: int
    max_duration_s: int
    max_energy_j: float
    expires_at: str
    operator_present: bool
    estop_verified_at: str
    auto_revoke_on: tuple[str, ...]
    post_expiry_state: str
    commands_issued: int = 0

    def remaining_commands(self) -> int:
        return max(0, self.max_commands - self.commands_issued)


def require_lease_for_level(level: str) -> bool:
    return level in LEASE_REQUIRED_LEVELS


def revoke(lease: AuthorityLease, reason: str) -> dict:
    return {
        "schema": "octopus.authority-lease.revoke.v1",
        "lease_id": lease.lease_id,
        "reason": reason,
        "post_expiry_state": lease.post_expiry_state or "AUTHORITY_NONE",
        "authority_after": "AUTHORITY_NONE",
        "renewal": "ISSUE_NEW_LEASE_NOT_MUTATE_FIELDS",
    }


def check_command_budget(lease: AuthorityLease) -> dict | None:
    if lease.commands_issued >= lease.max_commands:
        return revoke(lease, reason="budget_exhausted")
    return None
