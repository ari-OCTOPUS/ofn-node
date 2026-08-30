"""enqueue / pull / ack — بدون شبکه به برد."""
from __future__ import annotations

import json

from . import config
from .schema import Command, CommandState, build_command
from . import queue as q


def enqueue(*, kind: str, text: str, target_agent: str = "ofn",
            target_instance: str = "panel", source: str = "owner") -> dict:
    """صف کردن. task همیشه received (owner_required). بقیه اگر مسلح باشند authorized."""
    cmd = build_command(
        kind=kind, target_agent=target_agent,
        target_instance=target_instance, text=text, source=source,
    )
    k = str(kind).lower()
    if k == "task" or not config.is_armed():
        state = CommandState.RECEIVED
    else:
        state = CommandState.AUTHORIZED
    stored = q.insert(cmd, kind=k, state=state)
    stored["owner_required"] = k == "task" or state == CommandState.RECEIVED
    stored["armed"] = config.is_armed()
    stored["gate0"] = config.gate0_ready()
    stored["flag"] = config.flag_on()
    stored["pulled"] = False
    stored["external_effect"] = False
    return stored


def authorize(message_id: str) -> dict:
    """رأی مالک: received → authorized تا برد بتواند بکشد."""
    return q.set_state(message_id, CommandState.AUTHORIZED)


def pull(*, limit: int = 8) -> dict:
    if not config.flag_on():
        return {"ok": False, "reason": "flag_off", "commands": []}
    if not config.gate0_ready():
        return {"ok": False, "reason": "gate0", "commands": []}
    rows = q.list_by_state(CommandState.AUTHORIZED, limit=limit)
    out = []
    for row in rows:
        q.set_state(row["message_id"], CommandState.DISPATCHED)
        payload = json.loads(row["payload_json"])
        out.append(payload)
    return {"ok": True, "commands": out, "count": len(out)}


def ack(message_id: str, *, outcome: str) -> dict:
    if not config.flag_on():
        return {"ok": False, "reason": "flag_off"}
    key = str(outcome or "").strip().lower()
    row = q.get(message_id)
    if not row:
        return {"ok": False, "reason": "not-found"}
    cur = CommandState(row["state"])
    if key == "succeeded":
        if cur == CommandState.DISPATCHED:
            steps = [CommandState.ACCEPTED, CommandState.SUCCEEDED]
        elif cur in (CommandState.ACCEPTED, CommandState.RUNNING):
            steps = [CommandState.SUCCEEDED]
        else:
            steps = [CommandState.SUCCEEDED]
    elif key == "failed":
        steps = [CommandState.FAILED]
    elif key == "rejected":
        steps = [CommandState.REJECTED]
    elif key == "accepted":
        steps = [CommandState.ACCEPTED]
    elif key == "running":
        steps = [CommandState.RUNNING]
    elif key == "unknown_outcome":
        steps = [CommandState.UNKNOWN_OUTCOME]
    elif key == "cancelled":
        steps = [CommandState.CANCELLED]
    else:
        return {"ok": False, "reason": "bad-outcome"}
    try:
        for st in steps:
            row = q.set_state(message_id, st)
    except ValueError as exc:
        return {"ok": False, "reason": str(exc)}
    return {"ok": True, "message_id": message_id, "state": row["state"]}
