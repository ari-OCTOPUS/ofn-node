"""health.py — unified heartbeat / نبض ارگانیسم.

معماری:
  • هر organ یک OrganHealth دارد که فایل .health.json خودش را می‌نویسد
  • OrganismHealth همه را جمع می‌کند
  • dead organ detection: timeout-based
  • event_bus publish روی "organ.heartbeat" و "organ.dead"

نقش در استعاره: نبض سه قلب و سلامت بازوها — اگر یکی نایستد، موجود زنده ولی قابل اتکا نیست.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional


class OrganHealth:
    """سلامت یک اندام (مثلاً یک worker، یک brain، یک heart)."""

    def __init__(self, name: str, path: Path):
        self.name = name
        self._path = Path(path)
        self._state: dict = {"name": name, "status": "unknown", "last_beat": 0, "details": {}}
        if self._path.exists():
            try:
                self._state = json.loads(self._path.read_text("utf-8"))
            except (OSError, json.JSONDecodeError):
                pass

    def beat(self, status: str = "healthy", details: Optional[dict] = None) -> None:
        """یک ضربان ثبت می‌کند."""
        self._state.update({
            "name": self.name,
            "status": status,
            "last_beat": time.time(),
            "details": details or {},
        })
        try:
            self._path.write_text(json.dumps(self._state, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def is_alive(self, timeout_sec: float = 300.0) -> bool:
        """اگر status=dead باشد قطعاً مرده؛ وگرنه timeout را بررسی کن."""
        if self._state.get("status") == "dead":
            return False
        return (time.time() - self._state.get("last_beat", 0)) < timeout_sec

    def to_dict(self) -> dict:
        return dict(self._state)


class OrganismHealth:
    """سلامت کل ارگانیسم — همهٔ اندام‌ها."""

    def __init__(self, persist_dir: Path, bus=None):
        self._dir = Path(persist_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._organs: Dict[str, OrganHealth] = {}
        self._bus = bus  # optional event_bus

    def register(self, name: str) -> OrganHealth:
        """یک اندام ثبت می‌کند (اگر قبلاً نبود)."""
        if name not in self._organs:
            self._organs[name] = OrganHealth(name, self._dir / f"{name}.health.json")
        return self._organs[name]

    def beat(self, name: str, status: str = "healthy", details: Optional[dict] = None) -> None:
        """یک ضربان برای اندام خاص."""
        organ = self.register(name)
        organ.beat(status=status, details=details)
        if self._bus:
            try:
                self._bus.publish("organ.heartbeat",
                                  {"organ": name, "status": status, "details": details or {}},
                                  source="health.py")
            except Exception:
                pass

    def status(self) -> List[dict]:
        return [o.to_dict() for o in self._organs.values()]

    def dead_organs(self, timeout_sec: float = 300.0) -> List[str]:
        return [name for name, o in self._organs.items() if not o.is_alive(timeout_sec)]

    def is_healthy(self, timeout_sec: float = 300.0) -> bool:
        return len(self.dead_organs(timeout_sec)) == 0

    def check_and_alert(self, timeout_sec: float = 300.0) -> List[dict]:
        """dead organs را بررسی و event publish می‌کند."""
        dead = self.dead_organs(timeout_sec)
        alerts = []
        for name in dead:
            organ = self._organs[name]
            alert = {
                "organ": name,
                "last_beat": organ.to_dict().get("last_beat"),
                "alert": "organ_dead",
                "ts": time.time(),
            }
            alerts.append(alert)
            if self._bus:
                try:
                    self._bus.publish("organ.dead", alert, source="health.py")
                except Exception:
                    pass
        return alerts


class HeartBeat:
    """پیاده‌سازی سادهٔ ضربان برای workerهایی که loop دارند."""

    def __init__(self, organism: OrganismHealth, organ_name: str,
                 interval_sec: float = 60.0, timeout_sec: float = 300.0):
        self.organism = organism
        self.organ_name = organ_name
        self.interval_sec = interval_sec
        self.timeout_sec = timeout_sec
        self._last_beat = 0.0

    def tick(self, status: str = "healthy", details: Optional[dict] = None) -> None:
        now = time.time()
        if now - self._last_beat >= self.interval_sec:
            self.organism.beat(self.organ_name, status=status, details=details)
            self._last_beat = now

    def is_alive(self) -> bool:
        organ = self.organism.register(self.organ_name)
        return organ.is_alive(self.timeout_sec)
