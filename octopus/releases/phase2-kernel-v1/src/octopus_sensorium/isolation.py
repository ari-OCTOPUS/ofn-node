"""Actuator isolation policy. Absence of a motor is not isolation."""

from __future__ import annotations

import os
import pathlib
from typing import Iterable

FORBIDDEN_IMPORTS = (
    "RPi.GPIO",
    "gpiozero",
    "gpiod",
    "periphery",
    "Adafruit_BBIO",
    "pigpio",
)

PWM_EXPORT_PATHS = (
    pathlib.Path("/sys/class/pwm/pwmchip0/export"),
    pathlib.Path("/sys/class/pwm/pwmchip1/export"),
)

WATCHDOG_PATHS = (
    pathlib.Path("/dev/watchdog"),
    pathlib.Path("/dev/watchdog0"),
)


class IsolationViolation(Exception):
    pass


def reject_actuator_manifest(manifest: dict) -> None:
    security = manifest.get("security") or {}
    if security.get("actuator_access") is True:
        raise IsolationViolation(
            f"plugin {manifest.get('sensor_id')} requested actuator_access=true"
        )
    if security.get("shell_access") is True:
        raise IsolationViolation(
            f"plugin {manifest.get('sensor_id')} requested shell_access=true"
        )
    if security.get("command_access") is True:
        raise IsolationViolation(
            f"plugin {manifest.get('sensor_id')} requested command_access=true"
        )


def assert_no_pwm_write(paths: Iterable[pathlib.Path] = PWM_EXPORT_PATHS) -> None:
    for path in paths:
        if not path.exists():
            continue
        try:
            fd = os.open(path, os.O_WRONLY)
        except PermissionError:
            continue
        except OSError as exc:
            if getattr(exc, "errno", None) in {1, 13, 30}:  # EPERM, EACCES, EROFS
                continue
            raise IsolationViolation(f"unexpected PWM open error on {path}: {exc}") from exc
        else:
            os.close(fd)
            raise IsolationViolation(f"PWM export is writable: {path}")


def assert_watchdog_not_opened_by_agent() -> None:
    # The agent must not hold the hardware watchdog. Existence is allowed.
    if os.environ.get("OCTOPUS_OPEN_WATCHDOG") == "1":
        raise IsolationViolation("agent attempted to open hardware watchdog")


def forbidden_import_detected(module_name: str) -> bool:
    return module_name in FORBIDDEN_IMPORTS
