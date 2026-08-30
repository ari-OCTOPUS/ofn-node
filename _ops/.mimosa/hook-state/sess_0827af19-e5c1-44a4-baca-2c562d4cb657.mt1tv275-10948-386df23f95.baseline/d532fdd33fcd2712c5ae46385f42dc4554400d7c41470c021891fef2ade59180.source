"""قرارداد نوع: همان Command برد (octopus_bridge.models) + kind صف."""
from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BRIDGE = _ROOT / "octopus-bridge"
if str(_BRIDGE) not in sys.path:
    sys.path.insert(0, str(_BRIDGE))

from octopus_bridge.models import (  # noqa: E402
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    Command,
    CommandState,
    iso,
    new_id,
    now_utc,
    parse_iso,
    transition_allowed,
)

from .config import KINDS, TARGET_AGENTS, TARGET_INSTANCES

__all__ = [
    "ALLOWED_TRANSITIONS",
    "Command",
    "CommandState",
    "KINDS",
    "TERMINAL_STATES",
    "build_command",
    "iso",
    "new_id",
    "now_utc",
    "parse_iso",
    "transition_allowed",
]


def build_command(*, kind: str, target_agent: str, target_instance: str,
                  text: str, source: str = "owner") -> Command:
    k = str(kind or "").strip().lower()
    agent = str(target_agent or "ofn").strip().lower()
    inst = str(target_instance or "panel").strip().lower()
    if k not in KINDS:
        raise ValueError("bad-kind")
    if agent not in TARGET_AGENTS:
        raise ValueError("bad-target-agent")
    if inst not in TARGET_INSTANCES:
        raise ValueError("bad-target-instance")
    if agent == "hypno" and inst != "hypno":
        inst = "hypno"
    now = now_utc()
    op = {
        "ask": "ofn.ask",
        "status": "ofn.status.owner",
        "panel": "ofn.panel.act",
        "task": "ofn.task.start",
    }[k]
    return Command(
        message_id=new_id(),
        operation=op,
        source_principal=source,
        target_agent=agent,
        target_instance=inst,
        issued_at=now,
        expires_at=now + timedelta(hours=6),
        policy_version="board-cp-1",
        correlation_id=new_id(),
        idempotency_key=None,
        parameters={"kind": k, "text": str(text or "")[:2000]},
    )
