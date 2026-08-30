"""event_bus.py — سیستم عصبی اختاپوس (lightweight pub/sub, stdlib-only).

معماری:
  • topic-based pub/sub با threading.Lock + queue.Queue
  • correlation_id propagation در هر رویداد
  • file-based persistence (JSONL per topic) برای recovery و audit
  • zero dependency خارجی — فقط stdlib

نقش در استعارهٔ اختاپوس: سیستم عصبی — اتصال مغزها، قلب‌ها، بازوها و بادکش‌ها.
"""
from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


class EventBus:
    """سبک‌وزن، stdlib-only، topic-based event bus با persistence.

    Usage:
        bus = EventBus(persist_dir=Path("/tmp/octopus_bus"))
        sub_id = bus.subscribe("heart.truth", my_handler)
        bus.publish("heart.truth", {"stale": False}, correlation_id="abc-123")
    """

    def __init__(self, persist_dir: Optional[Path] = None):
        self._subs: Dict[str, List[Tuple[str, Callable]]] = {}
        self._lock = threading.Lock()
        self._persist_dir = Path(persist_dir) if persist_dir else None
        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)

    # ── subscribe / unsubscribe ────────────────────────────────────────────
    def subscribe(self, topic: str, handler: Callable[[dict], None]) -> str:
        """handler یک تابع است که یک dict (event) می‌گیرد. برمی‌گرداند sub_id."""
        sub_id = str(uuid.uuid4())[:12]
        with self._lock:
            self._subs.setdefault(topic, []).append((sub_id, handler))
        return sub_id

    def unsubscribe(self, topic: str, sub_id: str) -> bool:
        with self._lock:
            handlers = self._subs.get(topic, [])
            before = len(handlers)
            self._subs[topic] = [(sid, h) for sid, h in handlers if sid != sub_id]
            return len(self._subs[topic]) < before

    # ── publish ──────────────────────────────────────────────────────────────
    def publish(self, topic: str, payload: dict,
                correlation_id: Optional[str] = None,
                source: str = "anonymous") -> str:
        """یک رویداد منتشر می‌کند. برمی‌گرداند event_id."""
        cid = correlation_id or self._new_cid()
        event_id = f"EVT-{uuid.uuid4().hex[:12]}"
        event = {
            "event_id": event_id,
            "topic": topic,
            "payload": payload,
            "correlation_id": cid,
            "source": source,
            "ts": time.time(),
        }
        self._persist(event)
        with self._lock:
            handlers = list(self._subs.get(topic, []))
        for _sid, handler in handlers:
            try:
                handler(dict(event))
            except Exception:
                pass  # fail-soft: یک handler خطا نباید بقیه را بشکند
        return event_id

    # ── query (read-only audit) ──────────────────────────────────────────────
    def query(self, topic: Optional[str] = None, since: Optional[float] = None,
              correlation_id: Optional[str] = None, n: int = 100) -> List[dict]:
        """فایل‌های JSONL را می‌خواند و فیلتر می‌کند. read-only، هیچ side-effect ندارد."""
        results: List[dict] = []
        if not self._persist_dir or not self._persist_dir.exists():
            return results
        files = ([self._persist_dir / f"{topic}.jsonl"]
                 if topic else sorted(self._persist_dir.glob("*.jsonl")))
        for path in files:
            if not path.exists():
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            ev = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if since and ev.get("ts", 0) < since:
                            continue
                        if correlation_id and ev.get("correlation_id") != correlation_id:
                            continue
                        results.append(ev)
            except OSError:
                continue
        # مرتب‌سازی بر اساس ts و محدودسازی
        results.sort(key=lambda x: x.get("ts", 0))
        return results[-n:]

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _new_cid() -> str:
        return f"CID-{uuid.uuid4().hex[:12]}"

    def _persist(self, event: dict) -> None:
        if not self._persist_dir:
            return
        path = self._persist_dir / f"{event['topic']}.jsonl"
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError:
            pass


class SyncEventBus(EventBus):
    """ورثهٔ EventBus که از threading.Queue برای delivery synchronous استفاده می‌کند.
    مناسب برای workerهایی که می‌خواهند blocking consume کنند."""

    def __init__(self, persist_dir: Optional[Path] = None):
        super().__init__(persist_dir=persist_dir)
        self._queues: Dict[str, queue.Queue] = {}

    def subscribe_queue(self, topic: str, maxsize: int = 0) -> queue.Queue:
        """برای هر topic یک Queue می‌سازد. Worker می‌تواند q.get() کند."""
        q = queue.Queue(maxsize=maxsize)
        with self._lock:
            self._queues.setdefault(topic, q)
        return q

    def publish(self, topic: str, payload: dict,
                correlation_id: Optional[str] = None,
                source: str = "anonymous") -> str:
        event_id = super().publish(topic, payload, correlation_id=correlation_id, source=source)
        # Queue delivery
        with self._lock:
            q = self._queues.get(topic)
        if q is not None:
            try:
                q.put_nowait({"topic": topic, "payload": payload,
                              "correlation_id": correlation_id or self._new_cid(),
                              "source": source, "ts": time.time(), "event_id": event_id})
            except queue.Full:
                pass
        return event_id


def get_bus(persist_dir: Optional[Path] = None) -> EventBus:
    """singleton helper — اگر یک مسیر داده شود، همان را همیشه استفاده می‌کند."""
    return EventBus(persist_dir=persist_dir)
