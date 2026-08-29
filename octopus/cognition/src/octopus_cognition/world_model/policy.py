"""WAVE0 policy consumer.

May read a metacontrol advisory file. Must not import persistence, planner,
or the WorldModel protocol. Skill does not grant authority.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ADVISORY = Path("/var/lib/octopus/state/metacontrol/latest.json")


def last_advisory() -> dict[str, Any]:
    if not ADVISORY.is_file():
        return {"recommendation": "DENY", "executable": False, "reason": "no_advisory"}
    try:
        return json.loads(ADVISORY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"recommendation": "DENY", "executable": False, "reason": "advisory_unreadable"}


def choose_action(_state: dict[str, Any] | None = None) -> str:
    advisory = last_advisory()
    if advisory.get("executable") is True:
        return "NO_ACTION_OBSERVE_ONLY"
    return "NO_ACTION_OBSERVE_ONLY"
