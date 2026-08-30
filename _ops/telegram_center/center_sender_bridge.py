#!/usr/bin/env python3
"""Optional center-facing SenderBridge attach (default-off).

Center may import this module. It does NOT auto-send. Callers must inject
queue + send_fn. run_once is refused unless live_telegram_gate.send_allowed().
"""
from __future__ import annotations

from typing import Any, Callable

from sender_bridge import SenderBridge
import live_telegram_gate as gate


def build_bridge(queue, send_fn: Callable[[dict], dict], **kwargs) -> SenderBridge:
    return SenderBridge(queue, send_fn, **kwargs)


def run_once_if_allowed(bridge: SenderBridge, *, limit: int = 10, flag=None, lock=None, now=None) -> dict[str, Any]:
    status = gate.evaluate(flag=flag, lock=lock, now=now)
    if not status.get("send_allowed"):
        return {"ran": False, "blocked": True, "gate": status, "sent": 0, "deferred": 0, "dlq": 0, "rate_blocked": 0, "due": 0}
    counts = dict(bridge.run_once(limit=limit))
    counts["ran"] = True
    counts["blocked"] = False
    counts["gate"] = status
    return counts
