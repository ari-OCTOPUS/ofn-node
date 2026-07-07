# -*- coding: utf-8 -*-
"""کانال‌های رکن B (ADR-005) — تلگرام کامل، واتساپ stub روی همان interface.

TelegramChannel با HTTP خام (urllib) کار می‌کند تا مستقل از event-loop ربات ادمین
باشد (notifier در thread جدا هم می‌تواند بفرستد). rate-limit ساده: حداقل فاصله بین
ارسال‌ها. to_ref = id کاربر در users.yaml — resolve به chat_id از authz (نه شماره خام).
"""
from __future__ import annotations

import json
import threading
import time
import urllib.parse
import urllib.request
from typing import Callable, Optional

from core.contracts import Channel


class TelegramChannel(Channel):
    name = "telegram"

    def __init__(self, token: str, resolve_chat_id: Callable[[str], Optional[int]],
                 min_interval: float = 1.5):
        self._token = token
        self._resolve = resolve_chat_id
        self._min_interval = min_interval
        self._last = 0.0
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return bool(self._token)

    def _throttle(self) -> None:
        with self._lock:
            wait = self._min_interval - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()

    def _api(self, method: str, payload: dict) -> dict:
        self._throttle()
        url = f"https://api.telegram.org/bot{self._token}/{method}"
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8", "replace"))

    def send(self, to_ref: str, text: str) -> bool:
        chat_id = self._resolve(to_ref)
        if not chat_id:
            return False
        try:
            data = self._api("sendMessage", {"chat_id": chat_id, "text": text[:4000]})
            return bool(data.get("ok"))
        except Exception:  # noqa: BLE001
            return False

    def send_card(self, chat_id: int, text: str, buttons: list) -> bool:
        """کارت با دکمه‌های inline — buttons=[[(label, callback_data),...],...]"""
        markup = {"inline_keyboard": [
            [{"text": lb, "callback_data": cb} for lb, cb in row] for row in buttons]}
        try:
            data = self._api("sendMessage", {"chat_id": chat_id, "text": text[:4000],
                                             "reply_markup": markup})
            return bool(data.get("ok"))
        except Exception:  # noqa: BLE001
            return False


class WhatsAppChannel(Channel):
    """جای‌نگه‌دار — WhatsApp Cloud API نیازمند شماره/Meta Business است (ADR-005).
    وقتی فعال شد فقط send() این کلاس پیاده می‌شود؛ رکن B هیچ تغییری نمی‌خواهد."""

    name = "whatsapp"

    def is_available(self) -> bool:
        return False

    def send(self, to_ref: str, text: str) -> bool:  # noqa: ARG002
        return False
