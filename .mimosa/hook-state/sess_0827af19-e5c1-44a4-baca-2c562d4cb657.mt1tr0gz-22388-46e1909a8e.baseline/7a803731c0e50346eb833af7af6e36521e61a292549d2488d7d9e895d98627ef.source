#!/usr/bin/env python3
"""Pure seam for telegram_center after input_surface_policy has authorized Outer DM.

It does not inspect tokens, owner IDs, chats or send messages. The caller must pass the already
computed surface decision. This avoids re-inferring owner/surface and the regression that previously
swallowed valid owner messages.
"""
from __future__ import annotations

from . import conversation


def handle_message(text: str, *, surface_decision: dict) -> dict:
    d = dict(surface_decision or {})
    if not (d.get("allow") is True and d.get("mode") == "core_conversation"):
        return {"handled": False, "reason": "not-authorized-outer-core-conversation",
                "reply": None}
    return {"handled": True, "reason": "owner-console", "reply": conversation.handle(text)}


def handle_callback(data: str, *, surface_decision: dict) -> dict:
    d = dict(surface_decision or {})
    if not (d.get("allow") is True and d.get("mode") == "core_conversation"):
        return {"handled": False, "reason": "not-authorized-outer-core-conversation",
                "reply": None}
    if not str(data or "").startswith("oc:"):
        return {"handled": False, "reason": "not-owner-console-callback", "reply": None}
    return {"handled": True, "reason": "owner-console", "reply": conversation.callback(data)}
