#!/usr/bin/env python3
"""Pure seam for telegram_center after input_surface_policy has authorized Outer DM.

It does not inspect tokens, owner IDs, chats or send messages. The caller must pass the already
computed surface decision. This avoids re-inferring owner/surface and the regression that previously
swallowed valid owner messages.

Talk Discovery Phase B: when OCTOPUS_WIRE_COLLAB=1, route through collaborator.handle
(same brain as MiniApp /api/collab). Otherwise keep conversation.handle.
"""
from __future__ import annotations

import os

from . import conversation


def _collab_armed() -> bool:
    return os.environ.get("OCTOPUS_WIRE_COLLAB", "0") == "1"


def handle_message(text: str, *, surface_decision: dict) -> dict:
    d = dict(surface_decision or {})
    if not (d.get("allow") is True and d.get("mode") == "core_conversation"):
        return {"handled": False, "reason": "not-authorized-outer-core-conversation",
                "reply": None}
    if _collab_armed():
        from . import collaborator
        return {"handled": True, "reason": "collaborator",
                "reply": collaborator.handle(text)}
    return {"handled": True, "reason": "owner-console", "reply": conversation.handle(text)}


def handle_callback(data: str, *, surface_decision: dict) -> dict:
    d = dict(surface_decision or {})
    if not (d.get("allow") is True and d.get("mode") == "core_conversation"):
        return {"handled": False, "reason": "not-authorized-outer-core-conversation",
                "reply": None}
    if not str(data or "").startswith("oc:"):
        return {"handled": False, "reason": "not-owner-console-callback", "reply": None}
    if _collab_armed():
        from . import collaborator
        return {"handled": True, "reason": "collaborator",
                "reply": collaborator.callback(data)}
    return {"handled": True, "reason": "owner-console", "reply": conversation.callback(data)}
