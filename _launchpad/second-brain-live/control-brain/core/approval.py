# -*- coding: utf-8 -*-
"""صف تأیید مرکزی لایه ۰ (ADR-006: approve-first، fail-closed) + notifier ادمین.

- ApprovalQueueDB: پیاده‌سازی contracts.ApprovalQueue روی جدول outbox.
- Notifier (thread): هر ۲۰ ثانیه بریف‌های تازه و پیام‌های منتظر را به‌صورت کارت
  با دکمه‌های inline برای ادمین می‌فرستد (با HTTP خام — مستقل از loop ربات).
- لاگ کامل: logs/outbox.jsonl (append-only).
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.contracts import ApprovalQueue, Channel, OutboxMessage

_LOG = Path(__file__).resolve().parent.parent / "logs" / "outbox.jsonl"


def _log(event: str, **kw) -> None:
    _LOG.parent.mkdir(exist_ok=True)
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "event": event, **kw}
    with _LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class ApprovalQueueDB(ApprovalQueue):
    def __init__(self, memory, channels: Dict[str, Channel]):
        self.mem = memory
        self.channels = channels

    def submit(self, msg: OutboxMessage) -> int:
        msg.status = "pending"
        mid = self.mem.add_outbox(msg)
        _log("submit", id=mid, business=msg.business, channel=msg.channel, to=msg.to_ref)
        return mid

    def resolve(self, msg_id: int, decision: str, edited_text: Optional[str] = None) -> None:
        msg = self.mem.get_outbox(msg_id)
        if msg is None or msg.status not in ("pending",):
            _log("resolve-skip", id=msg_id, decision=decision)
            return
        if decision == "rejected":
            self.mem.set_outbox(msg_id, "rejected")
            _log("rejected", id=msg_id)
            return
        text = edited_text if edited_text else msg.text
        ch = self.channels.get(msg.channel)
        if ch is None or not ch.is_available():
            self.mem.set_outbox(msg_id, "failed", text=text, detail="کانال در دسترس نیست")
            _log("failed", id=msg_id, reason="no-channel")
            return
        ok = ch.send(msg.to_ref, text)
        self.mem.set_outbox(msg_id, "sent" if ok else "failed", text=text,
                            detail="" if ok else "send برگشت False")
        _log("sent" if ok else "failed", id=msg_id, edited=bool(edited_text))

    def pending(self) -> List[OutboxMessage]:
        return self.mem.pending_outbox()


class Notifier(threading.Thread):
    """کارت‌رسان ادمین — بریف تازه → کارت 👍/👎 · پیام pending → کارت ✅/✏️/❌"""

    def __init__(self, memory, tg_channel, admin_chat_id: int, interval: int = 20):
        super().__init__(daemon=True)
        self.mem = memory
        self.tg = tg_channel
        self.admin = admin_chat_id
        self.interval = interval
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def _push_briefs(self) -> None:
        for b in self.mem.unnotified_briefs():
            text = (f"🧠 بریف تازه — {b.business}\n\n📌 {b.title}\n\n"
                    f"💡 {b.opportunity}\n\n❓ چرا: {b.why}\n\n"
                    f"▶️ اقدام: {b.action}\n🔗 {b.source}")
            ok = self.tg.send_card(self.admin, text,
                                   [[("👍 مفید", f"fb:g:{b.id}"), ("👎 بی‌فایده", f"fb:b:{b.id}")]])
            if ok:
                self.mem.mark_brief_notified(b.id)

    def _push_outbox(self) -> None:
        for m in self.mem.unnotified_outbox():
            text = (f"📮 پیام منتظر تأیید — {m.business} → {m.to_ref} ({m.channel})\n"
                    f"――――――――――\n{m.text}")
            ok = self.tg.send_card(self.admin, text,
                                   [[("✅ بفرست", f"ap:ok:{m.id}"),
                                     ("✏️ ویرایش", f"ap:ed:{m.id}"),
                                     ("❌ رد", f"ap:no:{m.id}")]])
            if ok:
                self.mem.mark_outbox_notified(m.id)

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                self._push_briefs()
                self._push_outbox()
            except Exception:  # noqa: BLE001 — notifier هرگز نباید بمیرد
                pass
            self._stop.wait(self.interval)
