from octopus_cognition.authority_lease import (
    AuthorityLease,
    check_command_budget,
    require_lease_for_level,
    revoke,
)


def _lease(**kwargs):
    defaults = dict(
        schema="octopus.authority-lease.v1",
        lease_id="LEASE-TEST",
        level="A3",
        actuator_allowlist=("motor-A",),
        max_commands=5,
        max_duration_s=120,
        max_energy_j=0,
        expires_at="2026-08-17T00:00:00Z",
        operator_present=True,
        estop_verified_at="2026-08-17T00:00:00Z",
        auto_revoke_on=("lease_expiry", "budget_exhausted"),
        post_expiry_state="AUTHORITY_NONE",
        commands_issued=0,
    )
    defaults.update(kwargs)
    return AuthorityLease(**defaults)


def test_levels_above_a1_require_lease():
    assert require_lease_for_level("A0") is False
    assert require_lease_for_level("A1") is False
    assert require_lease_for_level("A3") is True


def test_budget_exhausted_revokes():
    lease = _lease(commands_issued=5, max_commands=5)
    out = check_command_budget(lease)
    assert out is not None
    assert out["reason"] == "budget_exhausted"
    assert out["authority_after"] == "AUTHORITY_NONE"
    assert out["renewal"] == "ISSUE_NEW_LEASE_NOT_MUTATE_FIELDS"


def test_budget_remaining_does_not_revoke():
    assert check_command_budget(_lease(commands_issued=4, max_commands=5)) is None


def test_revoke_does_not_extend_fields():
    out = revoke(_lease(), reason="lease_expiry")
    assert out["post_expiry_state"] == "AUTHORITY_NONE"
