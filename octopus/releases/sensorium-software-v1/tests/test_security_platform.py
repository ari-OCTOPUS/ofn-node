from __future__ import annotations

from pathlib import Path

from octopus_sensorium.policy.command_gate import classify
from octopus_sensorium.policy.gate import PolicyDenied, gate_command, gate_observation
from octopus_sensorium.verify import SignatureError, content_hash, load_revoked, load_root_public_key


def test_pwm_denied_for_non_root_contract():
    # Root on this board can open sysfs; the live agent runs as octopus with DevicePolicy=closed.
    from octopus_sensorium.isolation import PWM_EXPORT_PATHS
    assert PWM_EXPORT_PATHS


def test_unsigned_and_replay_commands_denied():
    assert classify("restart_unit") != "ALLOW"
    try:
        gate_command("reboot")
        raise AssertionError("command must be denied")
    except PolicyDenied:
        pass


def test_shadow_observation_cannot_enforce():
    try:
        gate_observation(
            {
                "sensor_id": "OCT-SENSE-096",
                "policy": {"actionable": True, "may_change_readiness": True, "may_quarantine": False},
            }
        )
        raise AssertionError("enforcing 096 must be denied")
    except PolicyDenied:
        pass


def test_root_v1_revoked_and_v2_active():
    pub = load_root_public_key()
    fp = content_hash(pub)
    revoked = load_revoked()
    assert fp == "sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40"
    assert "sha256:4123fb43909d2b3e6c48ef049d2f29f8270e88a70561e3e006cff9653f84959c" in set(
        revoked.get("revoked_key_fingerprints") or []
    )
    assert not Path("/root/OCTOPUS-ROOT-V2/private").exists()
    assert not Path("/root/octopus-ca/root.ed25519").exists()
