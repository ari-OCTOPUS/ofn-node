"""Policy boundary. Sensorium never grants actuator, PWM, STO, or leg execute."""

from __future__ import annotations

FORBIDDEN_ACTIONS = (
    "DIRECT_MOTOR_COMMAND",
    "RELEASE_STO",
    "DISABLE_SAFETY",
    "PWM_WRITE",
    "GPIO_ACTUATE",
    "TORQUE_COMMAND",
    "CURRENT_COMMAND",
    "MQTT_ENABLE",
    "LEG_AUTHORIZE",
)


def may_actuate() -> bool:
    return False


def deny(action: str) -> dict[str, str | bool]:
    return {
        "allowed": False,
        "action": action,
        "reason": "WAVE0_OBSERVE_ONLY",
        "actuator_authority": "NONE",
        "human_approval_required": True,
    }
