"""Shadow-mode policy. Derived evidence must not change belief, readiness, or actuators."""

from __future__ import annotations

from typing import Any

SHADOW_POLICY = {
    "shadow_mode": True,
    "actionable": False,
    "may_change_readiness": False,
    "may_quarantine": False,
    "may_execute": False,
    "may_resolve_belief": False,
}

DENY_092 = (
    "octopus.sensor.anomaly.",
    "octopus.world.contradiction",
    "octopus.command.",
    "octopus.actuator.",
)

DENY_095_LOOP = (
    "octopus.world.contradiction",
    "octopus.command.",
    "octopus.actuator.",
)


def assert_shadow_manifest(manifest: dict[str, Any]) -> None:
    pub = manifest.get("publication") or {}
    sec = manifest.get("security") or {}
    if pub.get("can_change_readiness") or pub.get("can_quarantine") or pub.get("can_execute"):
        raise ValueError(f"{manifest.get('sensor_id')} shadow plugin cannot have enforcement flags")
    if sec.get("actuator_access") or sec.get("command_access") or sec.get("shell_access"):
        raise ValueError(f"{manifest.get('sensor_id')} meta sensor cannot have actuator/command/shell access")
    if manifest.get("mode") != "shadow":
        raise ValueError(f"{manifest.get('sensor_id')} must start in mode=shadow")


def denied_subject(subject: str, prefixes: tuple[str, ...]) -> bool:
    return any(subject.startswith(p) for p in prefixes)
