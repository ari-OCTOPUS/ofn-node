"""Command allow/deny — GATEWAY ALLOWLIST FREEZE v1 (EDGE-NEXT 2026-08-23).

ALLOWED (executable readonly): COLLECT_DIAGNOSTICS, REQUEST_DIAGNOSTIC only.
All other former allowlist entries are NOT_ALLOWLISTED at freeze v1.
"""

from __future__ import annotations

ALLOWLIST_VERSION = "gateway-allowlist-freeze-v1-20260823"

ALLOWED_COMMANDS = {
    "REQUEST_DIAGNOSTIC",
    "COLLECT_DIAGNOSTICS",
}

FORBIDDEN_COMMANDS = {
    "EXEC_SHELL",
    "RUN_REMOTE_CODE",
    "DOWNLOAD_AND_EXECUTE",
    "WRITE_ARBITRARY_FILE",
    "DISABLE_SAFETY",
    "RELEASE_STO",
    "DIRECT_MOTOR_COMMAND",
    "BYPASS_POLICY",
    "ERASE_AUDIT_LOG",
    "EXPORT_CREDENTIALS",
    # Explicit arm/mutate family (never allowlisted at freeze v1)
    "ARM",
    "DISARM",
    "SET_ARMED",
    "ENABLE_ACTUATOR",
    "PWM_WRITE",
    "GPIO_WRITE",
    "MOTOR_COMMAND",
}

REQUIRED_COMMAND_FIELDS = (
    "sender_id",
    "signature",
    "role",
    "permission",
    "timestamp",
    "expiry",
    "nonce",
    "command",
)


def classify(command: str) -> str:
    if command in FORBIDDEN_COMMANDS:
        return "FORBIDDEN"
    if command in ALLOWED_COMMANDS:
        return "ALLOWLISTED"
    return "NOT_ALLOWLISTED"
