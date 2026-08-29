from __future__ import annotations

NEEDLES = ("ignore previous", "exec_shell", "direct_motor_command")


def contains_untrusted_instruction(blob: str) -> bool:
    lowered = blob.lower()
    return any(needle in lowered for needle in NEEDLES)
