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

        _emit_t48_spine_event(msg, from_id=from_id, chat_id=chat_id,
                              kind="command" if text.startswith("/") else "message")

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


def _emit_t48_spine_event(msg: dict, *, from_id, chat_id, kind: str) -> None:
    """T48 producer_2 (دستور #۸ §۳): رویداد spine با event-time واقعی.

    occurred_at = msg['date'] — **ساعتِ سرورِ تلگرام** (unix seconds، دقت ۱s)؛
    recorded_at = زمان ingest محلی. تأخیر طبیعی انسانی + اختلاف ساعت دو سرور
    (skew>0 ⇒ CLOCK_SKEW_SUSPECTED خودکار در publish). fail-soft مطلق؛
    rollback: OCTOPUS_T48_EVENT_TIME=0."""
    import os as _os
    if str(_os.environ.get("OCTOPUS_T48_EVENT_TIME", "1")).strip().lower() not in ("1", "true", "yes", "on"):
        return
    try:
        from datetime import datetime, timezone as _tz
        date = msg.get("date")
        if not date:
            return   # بدون منبع واقعی، رویداد منتشر نمی‌شود (نه تزریق ساعت نوشتن)
        occ = datetime.fromtimestamp(int(date), tz=_tz.utc).isoformat(timespec="seconds")
        import spine_adapters as _sa   # path زندهٔ center (همان import provider_adapter)
        _sa.emit_event(
            event_type="delivered", domain="telegram",
            correlation_id=f"tg-{from_id}-{int(date)}",
            subject=str(chat_id)[:64],
            producer="telegram_adapter_t48", trust="DETERMINISTIC",
            occurred_at=occ,
            event_time_source="telegram_message_date", time_precision="1s",
            payload={"kind": kind, "actor": str(from_id)[:24]},
            idempotency_key=f"tg-{from_id}-{int(date)}|t48-incoming")
    except Exception:  # noqa: BLE001 — هرگز receive loop تلگرام را نمی‌کشد
        pass


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
