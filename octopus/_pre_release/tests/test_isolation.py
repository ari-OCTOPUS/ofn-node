from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from octopus_sensorium.isolation import IsolationViolation, reject_actuator_manifest


def test_manifest_rejects_actuator_access():
    with pytest.raises(IsolationViolation):
        reject_actuator_manifest(
            {"sensor_id": "bad", "security": {"actuator_access": True, "shell_access": False}}
        )


def test_wave1_manifests_forbid_actuators():
    registry = yaml.safe_load(Path("/etc/octopus/config/registry.yaml").read_text(encoding="utf-8"))
    for sensor in registry["sensors"]:
        reject_actuator_manifest(sensor)


def test_systemd_unit_has_closed_device_policy():
    unit = Path("/etc/systemd/system/octopus-sensorium.service").read_text(encoding="utf-8")
    assert "DevicePolicy=closed" in unit
    assert "PrivateDevices=true" in unit
    assert "ProtectKernelTunables=true" in unit
    assert "pwm" not in unit.lower()
    assert "gpio" not in unit.lower()
    assert "watchdog" not in unit.lower() or "WatchdogSec" in unit
    assert "DeviceAllow=/dev/watchdog" not in unit
    assert "DIRECT_MOTOR" not in unit


def test_agent_user_not_in_gpio(monkeypatch):
    # Evaluated after user creation; skip if bootstrap has not run.
    import grp
    import pwd

    try:
        pwd.getpwnam("octopus")
    except KeyError:
        pytest.skip("octopus user not created yet")
    try:
        gpio = grp.getgrnam("gpio")
    except KeyError:
        return
    members = set(gpio.gr_mem)
    assert "octopus" not in members
