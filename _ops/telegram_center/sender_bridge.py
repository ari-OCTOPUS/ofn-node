#!/usr/bin/env python3
"""Single-owner Telegram sender bridge over the durable rate-limit queue.

Default-off. The live Center does not import this module; an owner-approved
canary wiring must attach it explicitly. The bridge never performs network I/O
itself — it drives an injected send_fn (fake transport in fixtures).
"""
from __future__ import annotations

import time
from typing import Callable


class SenderBridge:
    def __init__(self, queue, send_fn: Callable[[dict], dict], *,
                 clock=None, is_group: Callable[[str], bool] | None = None):
        self._queue = queue
        self._send_fn = send_fn
        self._clock = clock or time.time
        self._is_group = is_group or (lambda chat_hash: False)

    def run_once(self, *, limit: int = 10) -> dict:
        """One bounded pass over due items.

        For each due item:
          - admit() applies local policy (per-chat/group/global).
          - allowed  -> mark_delivery_attempt -> send_fn(item)
              ok+message_id        -> confirm
              retry_after present  -> defer(full)  (never early retry)
              exception            -> reconcile_sending -> DLQ (uncertain)
          - denied   -> defer until the policy's retry_not_before.
        Returns counts; never drops silently.
        """
        out = {"sent": 0, "deferred": 0, "dlq": 0, "rate_blocked": 0, "due": 0}
        for item in self._queue.due(limit=limit):
            out["due"] += 1
            key = item["message_key"]
            chat_hash = str(item["chat_hash"] or "")
            admitted = self._queue.admit(chat_hash=chat_hash,
                                         is_group=bool(self._is_group(chat_hash)))
            if not admitted["allowed"]:
                wait = max(0.0, float(admitted.get("retry_not_before")
                                      or float(self._clock())) - float(self._clock()))
                self._queue.defer(key, retry_after=wait)
                out["rate_blocked"] += 1
                continue
            if not self._queue.mark_delivery_attempt(key):
                out["dlq"] += 1
                continue
            try:
                result = self._send_fn(item) or {}
            except Exception:  # noqa: BLE001 — crash after transport attempt
                self._queue.reconcile_sending(key)
                out["dlq"] += 1
                continue
            if result.get("ok") and result.get("message_id") is not None:
                self._queue.confirm(key, message_id=int(result["message_id"]))
                out["sent"] += 1
                continue
            retry_after = result.get("retry_after")
            if retry_after is not None and float(retry_after) > 0:
                self._queue.defer(key, retry_after=float(retry_after))
                out["deferred"] += 1
                continue
            self._queue.dead_letter(key, reason="SEND_FAILED")
            out["dlq"] += 1
        return out
