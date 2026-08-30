"""capability_registry.py — قابلیت‌نامهٔ داینامیک (dynamic capability registry).

معماری:
  • هر ماژول/organ در startup خودش را advertise می‌کند
  • UI قبل از render می‌خواند: control اگر executable نیست → disabled با reason
  • revocation: اگر capability از کار افتاد، غیرفعال می‌شود
  • persist به JSON — stdlib-only

نقش در استعاره: هر بازو/organ باید بگوید "من چه می‌توانم، در چه وضعیتی".
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional


class CapabilityRegistry:
    """Registry داینامیک برای قابلیت‌های هر اندام اختاپوس.

    Fields per capability:
      name        — شناسهٔ یکتا (مثلاً "s:drafts", "/status")
      category    — "ui", "api", "brain", "heart", "arm", "sensor"
      executable  — bool: آیا الان قابل اجراست؟
      reason      — str: اگر executable=False، چرا؟
      organ       — str: کدام اندام این قابلیت را ثبت کرده
      meta        — dict: اطلاعات اضافی (مثلاً cost_aud, timeout_sec)
    """

    def __init__(self, path: Optional[Path] = None):
        self._path = Path(path) if path else None
        self._caps: Dict[str, dict] = {}
        self._lock = threading.Lock()
        if self._path and self._path.exists():
            self._load()

    # ── registration ─────────────────────────────────────────────────────────
    def register(self, name: str, category: str, organ: str,
                 executable: bool = True, reason: str = "",
                 meta: Optional[dict] = None) -> None:
        with self._lock:
            self._caps[name] = {
                "name": name,
                "category": category,
                "organ": organ,
                "executable": executable,
                "reason": reason,
                "registered_at": time.time(),
                "last_heartbeat": time.time(),
                "meta": meta or {},
            }
            self._save()

    def revoke(self, name: str, reason: str = "revoked") -> bool:
        """capability را غیرفعال می‌کند (نه حذف)."""
        with self._lock:
            cap = self._caps.get(name)
            if not cap:
                return False
            cap["executable"] = False
            cap["reason"] = reason
            cap["revoked_at"] = time.time()
            self._save()
            return True

    def heartbeat(self, name: str) -> bool:
        """organ باید heartbeat بزند تا بدانیم زنده است."""
        with self._lock:
            cap = self._caps.get(name)
            if not cap:
                return False
            cap["last_heartbeat"] = time.time()
            self._save()
            return True

    # ── queries ──────────────────────────────────────────────────────────────
    def can_execute(self, name: str) -> tuple[bool, str]:
        """برمی‌گرداند (executable, reason). اگر capability نامعتبر است → (False, not registered)."""
        with self._lock:
            cap = self._caps.get(name)
            if not cap:
                return False, "capability not registered"
            if not cap["executable"]:
                return False, cap.get("reason") or "disabled"
            return True, ""

    def is_stale(self, name: str, timeout_sec: float = 300.0) -> bool:
        """آیا heartbeat این capability قدیمی است؟"""
        with self._lock:
            cap = self._caps.get(name)
            if not cap:
                return True
            return (time.time() - cap.get("last_heartbeat", 0)) > timeout_sec

    def list_all(self) -> List[dict]:
        with self._lock:
            return [dict(c) for c in self._caps.values()]

    def list_by_category(self, category: str) -> List[dict]:
        with self._lock:
            return [dict(c) for c in self._caps.values() if c["category"] == category]

    def list_by_organ(self, organ: str) -> List[dict]:
        with self._lock:
            return [dict(c) for c in self._caps.values() if c["organ"] == organ]

    def render_menu(self, category: str, prefix_filter: Optional[str] = None) -> List[dict]:
        """برای UI: فقط آن‌هایی که executable هستند یا disabled با reason."""
        items = self.list_by_category(category)
        out = []
        for c in items:
            if prefix_filter and not c["name"].startswith(prefix_filter):
                continue
            ok, reason = c["executable"], c.get("reason", "")
            out.append({
                "name": c["name"],
                "executable": ok,
                "reason": reason if not ok else "",
                "stale": self.is_stale(c["name"]),
                "organ": c["organ"],
                "meta": c.get("meta", {}),
            })
        return out

    # ── persistence ──────────────────────────────────────────────────────────
    def _save(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._path.write_text(
                json.dumps({"caps": self._caps, "saved_at": time.time()},
                           ensure_ascii=False, indent=2),
                encoding="utf-8")
        except OSError:
            pass

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text("utf-8"))
            self._caps = data.get("caps", {})
        except (OSError, json.JSONDecodeError):
            self._caps = {}


class CapabilityRegistrySync:
    """Registry سادهٔ sync برای محیط‌های بدون threading."""

    def __init__(self, path: Optional[Path] = None):
        self._path = Path(path) if path else None
        self._caps: Dict[str, dict] = {}
        if self._path and self._path.exists():
            self._load()

    def register(self, name: str, category: str, organ: str,
                 executable: bool = True, reason: str = "",
                 meta: Optional[dict] = None) -> None:
        self._caps[name] = {
            "name": name, "category": category, "organ": organ,
            "executable": executable, "reason": reason,
            "registered_at": time.time(), "last_heartbeat": time.time(),
            "meta": meta or {},
        }
        self._save()

    def can_execute(self, name: str) -> tuple[bool, str]:
        cap = self._caps.get(name)
        if not cap:
            return False, "capability not registered"
        if not cap["executable"]:
            return False, cap.get("reason") or "disabled"
        return True, ""

    def revoke(self, name: str, reason: str = "revoked") -> bool:
        cap = self._caps.get(name)
        if not cap:
            return False
        cap["executable"] = False
        cap["reason"] = reason
        cap["revoked_at"] = time.time()
        self._save()
        return True

    def list_by_category(self, category: str) -> List[dict]:
        return [dict(c) for c in self._caps.values() if c["category"] == category]

    def _save(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._path.write_text(
                json.dumps({"caps": self._caps, "saved_at": time.time()},
                           ensure_ascii=False, indent=2),
                encoding="utf-8")
        except OSError:
            pass

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text("utf-8"))
            self._caps = data.get("caps", {})
        except (OSError, json.JSONDecodeError):
            self._caps = {}
