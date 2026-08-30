"""
tracing.py — چک‌لیست #۳: شفافیت، رصد و ممیزیِ غیرقابل‌دستکاری.

هر رویداد در یک فایل JSONL نوشته می‌شود و با یک «زنجیره‌ی هش» به رویداد قبلی
گره می‌خورد (tamper-evident audit log): اگر کسی یک خط را عوض کند، هش‌های بعدی
دیگر نمی‌خوانند و verify_chain() آن را لو می‌دهد.
"""
from __future__ import annotations
import json, hashlib, os, time
from typing import Any

import config


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


class AuditLog:
    def __init__(self, path: str = config.AUDIT_LOG_PATH, sink=None):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._prev_hash = self._last_hash()
        # قلاب اختیاری Langfuse (فاز ۲). اگر کلید نباشد، no-op است.
        if sink is None:
            try:
                from src.langfuse_sink import LangfuseSink
                sink = LangfuseSink()
            except Exception:
                sink = None
        self.sink = sink

    def _last_hash(self) -> str:
        if not os.path.exists(self.path):
            return "GENESIS"
        last = "GENESIS"
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last = json.loads(line)["hash"]
        return last

    def log(self, event: str, actor: str, **data: Any) -> dict:
        """یک رویداد را ثبت و چاپ می‌کند تا انسان لحظه‌ای ببیند هر ایجنت چه می‌کند."""
        record = {
            "ts": _now(),
            "event": event,      # مثل: agent_call, tool_call, hitl_request, halt
            "actor": actor,      # کدام ایجنت/مؤلفه
            "data": data,
            "prev": self._prev_hash,
        }
        payload = json.dumps(record, ensure_ascii=False, sort_keys=True)
        record["hash"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        self._prev_hash = record["hash"]
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        # ارسال اختیاری به Langfuse (هرگز اجرای اصلی را نمی‌شکند)
        if self.sink is not None:
            if event == "run_start":
                self.sink.start_run(data.get("topic", ""))
            self.sink.emit(event, actor, data)
            if event in ("run_done", "run_halted"):
                self.sink.flush()
        # شفافیت لحظه‌ای روی کنسول
        print(f"  📋 [{record['ts']}] {actor:<10} · {event:<14} {self._short(data)}")
        return record

    @staticmethod
    def _short(data: dict) -> str:
        s = json.dumps(data, ensure_ascii=False)
        return s if len(s) <= 90 else s[:87] + "..."

    def verify_chain(self) -> bool:
        """درستیِ زنجیره‌ی هش را بررسی می‌کند (آیا لاگ دستکاری شده؟)."""
        prev = "GENESIS"
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                stored = rec.pop("hash")
                if rec["prev"] != prev:
                    return False
                payload = json.dumps(rec, ensure_ascii=False, sort_keys=True)
                if hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16] != stored:
                    return False
                prev = stored
        return True
