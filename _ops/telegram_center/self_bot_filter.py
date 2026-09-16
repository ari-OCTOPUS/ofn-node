# -*- coding: utf-8 -*-
"""D15: skip ingest of the bot's own messages. Pure function."""
from __future__ import annotations


def is_self_bot_update(update: dict) -> bool:
    """True when message/edited_message/channel_post is from a bot.

    Callback queries are not skipped here (owner taps are not bot messages).
    """
    if not isinstance(update, dict):
        return False
    msg = update.get("message") or update.get("edited_message") or update.get("channel_post")
    if not isinstance(msg, dict):
        return False
    frm = msg.get("from")
    if not isinstance(frm, dict):
        return False
    return frm.get("is_bot") is True
