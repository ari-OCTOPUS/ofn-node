#!/usr/bin/env python3
"""telegram_adapter — پلِ no-outbound برای ثبتِ تعاملات تلگرام.

این ماژول **هیچ پیامی ارسال نمی‌کند**. فقط تعاملاتِ ورودی/خروجی را
به intel_spine log می‌کند (وقتی flag روشن است).

استفاده:
  - در center.py، بعد از receive update: log_incoming(update)
  - قبل از send: log_outgoing(chat_id, text)

قواعد:
  - token/chat_id همیشه hash/redact می‌شود
  - هیچ network call
  - اگر logger fail کرد، caller نباید بشکند
  - /stop و kill همیشه اولویت دارند (logger-failure-independent)
"""
from __future__ import annotations
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import intel_spine


def log_incoming(update: dict, owner_id: int | None = None) -> str | None:
    """یک incoming Telegram update را ثبت کن.

    update: dict با کلیدهای message/callback_query (شکلِ Telegram Bot API)
    owner_id: اختیاری — برای actor_ref
    """
    try:
        msg = update.get("message") or update.get("callback_query", {}).get("message", {})
        text = msg.get("text", "")
        chat_id = msg.get("chat", {}).get("id")
        from_id = msg.get("from", {}).get("id") or owner_id

        # detect /stop یا kill — این‌ها همیشه allow، فقط log
        is_stop = text.strip().lower().startswith(("/stop", "/halt", "/kill"))

        return intel_spine.log_interaction(
            source="telegram",
            direction="in",
            actor=from_id,
            channel=chat_id,
            text=text,
            kind="command" if text.startswith("/") else "message",
            is_stop=is_stop,
            d_level="D0",
            safety_verdict="allow" if is_stop else "unknown",
        )
    except Exception:
        # logger نباید caller را بشکند
        return None


def log_outgoing(chat_id: int | str, text: str, stream: str = "") -> str | None:
    """یک outgoing Telegram send را ثبت کن (قبل از send واقعی).

    **نکته:** این تابع پیام ارسال نمی‌کند. فقط log می‌کند.
    """
    try:
        return intel_spine.log_interaction(
            source="telegram",
            direction="out",
            actor="organism",
            channel=chat_id,
            text=text,
            kind="response",
            stream=stream,
            d_level="D1",
            safety_verdict="allow",  # log-only، enforcement نه
        )
    except Exception:
        return None


def log_callback(callback_data: str, from_id: int | None = None,
                 chat_id: int | None = None) -> str | None:
    """یک callback button press را ثبت کن."""
    try:
        return intel_spine.log_interaction(
            source="telegram",
            direction="in",
            actor=from_id,
            channel=chat_id,
            text=callback_data,
            kind="callback",
            d_level="D2",
            safety_verdict="unknown",
        )
    except Exception:
        return None
