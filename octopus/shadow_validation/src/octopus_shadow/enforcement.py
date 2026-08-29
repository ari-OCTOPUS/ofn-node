from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Authority:
    profile: str
    execute_enabled: bool
    registry_signature_valid: bool
    verifier_ready: bool
    gates_failed: tuple[str, ...]
    owner_approval: bool
    ledger_chain_valid: bool = True
    skill_lower_bound: float | None = None
    evidence_fresh: bool = True


class EnforcementGuard:
    """Fail-closed. Independent of the world model. A local YAML flip is not enough."""

    ALLOWED_WAVE1 = frozenset({"NO_ACTION", "WRITE_ADVISORY"})

    def authorize(self, action: str, authority: Authority) -> tuple[bool, str]:
        if authority.profile == "WAVE0_OBSERVE_ONLY":
            return False, "denied_observe_only"
        if not authority.execute_enabled:
            return False, "execute_disabled"
        if not authority.registry_signature_valid:
            return False, "invalid_registry_signature"
        if not authority.verifier_ready or authority.gates_failed:
            return False, "verifier_not_ready"
        if not authority.owner_approval:
            return False, "owner_approval_missing"
        if not authority.ledger_chain_valid:
            return False, "ledger_chain_invalid"
        if authority.skill_lower_bound is None or authority.skill_lower_bound <= 0.0:
            return False, "skill_not_confirmed"
        if not authority.evidence_fresh:
            return False, "stale_evidence"
        if action not in self.ALLOWED_WAVE1:
            return False, "action_not_allowlisted"
        return True, "authorized"
