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
    _emit_owner_inbound(d, text)   # #14A F2: emitter دوزمانی مسیر canonical
    from . import local_commands
    _handled, _reply = local_commands.handle_local(text)
    if _handled:
        return {"handled": True, "reason": "local-command", "reply": _reply}
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


_BOT_ID_CACHE: dict = {}


def _bot_id() -> "int | None":
    """bot_id عددی از TG_CENTER_BOT_TOKEN — یک‌بار getMe، کش ماژولی."""
    import os as _os2
    if _BOT_ID_CACHE:
        return _BOT_ID_CACHE.get("id")
    tok = _os2.environ.get("TG_CENTER_BOT_TOKEN", "")
    if not tok:
        return None
    try:
        import urllib.request as _ur
        with _ur.urlopen(f"https://api.telegram.org/bot{tok}/getMe", timeout=10) as r:
            _BOT_ID_CACHE.update(json.loads(r.read().decode()).get("result", {}))
    except Exception:  # noqa: BLE001
        _BOT_ID_CACHE["id"] = None
    return _BOT_ID_CACHE.get("id")


def _emit_owner_inbound(decision: dict, text: str) -> None:
    """#14A F2 (2026-08-20): رویداد spine دوزمانی برای پیام مالک در مسیر
    canonical inbound (owner-console seam). flags: OCTOPUS_T48_EVENT_TIME +
    OCTOPUS_WIRE_SPINE؛ بدون message.date رویداد ساخته نمی‌شود (نه تزریق ساعت)."""
    import os as _os
    if _os.environ.get("OCTOPUS_T48_EVENT_TIME", "1").strip().lower() not in ("1", "true", "yes", "on"):
        return
    try:
        import sys as _sys
        from pathlib import Path as _P
        _sp = str(_P(__file__).resolve().parents[1] / "spine")
        if _sp not in _sys.path:
            _sys.path.insert(0, _sp)
        import spine_adapters as _sa
        date = decision.get("message_date")
        if not date:
            return
        from datetime import datetime, timezone as _tz
        occ = datetime.fromtimestamp(int(date), tz=_tz.utc).isoformat(timespec="seconds")
        _sa.emit_event(
            event_type="delivered", domain="telegram",
            correlation_id=f"tg-{decision.get('chat_id')}-{date}",
            subject="owner_message", producer="owner_console_seam",
            trust="DETERMINISTIC", occurred_at=occ,
            event_time_source="telegram_message_date", time_precision="1s",
            payload={"mode": decision.get("mode"), "reason": decision.get("reason"),
                     "bot_id": _bot_id()},
            idempotency_key=f"tg-{decision.get('chat_id')}-{date}-{decision.get('update_id')}|owner-console")
    except Exception:  # noqa: BLE001 — seam هرگز مسیر مرکز را نمی‌کشد
        pass
