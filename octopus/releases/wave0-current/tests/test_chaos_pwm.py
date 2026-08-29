from __future__ import annotations

import os
from pathlib import Path

import pytest

PWM_EXPORT = Path("/sys/class/pwm/pwmchip0/export")


def test_pwm_export_denied_for_octopus():
    import pwd

    try:
        pwd.getpwnam("octopus")
    except KeyError:
        pytest.skip("octopus user not created yet")
    if not PWM_EXPORT.exists():
        pytest.skip("pwmchip0 export not present")
    if os.geteuid() == 0:
        # Root can write sysfs; the runtime proof is the octopus user + systemd DevicePolicy.
        rc = os.system("su -s /bin/sh octopus -c 'echo 0 > /sys/class/pwm/pwmchip0/export' 2>/dev/null")
        assert rc != 0
        return
    with pytest.raises(PermissionError):
        PWM_EXPORT.write_text("0", encoding="utf-8")
