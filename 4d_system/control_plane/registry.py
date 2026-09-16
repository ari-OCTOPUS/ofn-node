"""
control_plane/registry.py — بارگذاری/اعتبارسنجی registry + آینه‌ی SQLite.

تصمیمِ مالک (2026-07-11): source of truth = YAML (خوانا)، mirror = SQLite
جداگانه در outputs/control_plane/control_plane.db — **هرگز** داخلِ DB اصلیِ
پروژه (4d_experiments.db) نمی‌نویسیم؛ سطحِ مشاهده نباید storeی مشاهده‌شده را
آلوده کند.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
DEFAULT_REGISTRY = _HERE / "registry.yaml"

VALID_STATUS = {"CONNECTED", "PARTIAL", "MISSING", "UNKNOWN"}
VALID_AUTHORITY = {"observe-only", "approve", "pause-resume", "kill-switch"}
VALID_RISK = {"low", "medium", "high"}


@dataclass
class Registry:
    version: int
    project: dict[str, Any]
    subsystems: list[dict[str, Any]] = field(default_factory=list)
    channels: list[dict[str, Any]] = field(default_factory=list)
    source_path: str = ""

    # ── دسترسی ──────────────────────────────────────────────────────────
    def subsystem(self, sid: str) -> dict | None:
        return next((s for s in self.subsystems if s.get("id") == sid), None)

    def channel(self, cid: str) -> dict | None:
        return next((c for c in self.channels if c.get("id") == cid), None)

    def tcb_ids(self) -> list[str]:
        return [s["id"] for s in self.subsystems if s.get("tcb")]

    # ── اعتبارسنجی ──────────────────────────────────────────────────────
    def validate(self) -> list[str]:
        """لیستِ مشکلات (خالی = سالم). UNKNOWN مجاز است؛ فیلدِ غایب مشکل است."""
        problems: list[str] = []
        seen: set[str] = set()
        for s in self.subsystems:
            sid = s.get("id", "?")
            if sid in seen:
                problems.append(f"subsystem تکراری: {sid}")
            seen.add(sid)
            for req in ("id", "name", "path", "owner", "risk_tier", "authority"):
                if not s.get(req):
                    problems.append(f"subsystem {sid}: فیلد غایب '{req}'")
            if s.get("risk_tier") not in VALID_RISK:
                problems.append(f"subsystem {sid}: risk_tier نامعتبر {s.get('risk_tier')!r}")
            if s.get("authority") not in VALID_AUTHORITY:
                problems.append(f"subsystem {sid}: authority نامعتبر {s.get('authority')!r}")
        cseen: set[str] = set()
        for c in self.channels:
            cid = c.get("id", "?")
            if cid in cseen:
                problems.append(f"channel تکراری: {cid}")
            cseen.add(cid)
            for req in ("id", "name", "source", "sink", "risk_tier", "authority", "status"):
                if c.get(req) in (None, ""):
                    problems.append(f"channel {cid}: فیلد غایب '{req}'")
            if c.get("status") not in VALID_STATUS:
                problems.append(f"channel {cid}: status نامعتبر {c.get('status')!r}")
            if c.get("risk_tier") not in VALID_RISK:
                problems.append(f"channel {cid}: risk_tier نامعتبر {c.get('risk_tier')!r}")
            if c.get("authority") not in VALID_AUTHORITY:
                problems.append(f"channel {cid}: authority نامعتبر {c.get('authority')!r}")
        return problems


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> Registry:
    """YAML → Registry. (pyyaml از وابستگی‌های موجودِ langchain در دسترس است.)"""
    import yaml  # transitively موجود؛ در requirements هم صریح شد
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Registry(
        version=int(data.get("version", 0)),
        project=data.get("project", {}),
        subsystems=data.get("subsystems", []) or [],
        channels=data.get("channels", []) or [],
        source_path=str(p),
    )


# ── آینه‌ی SQLite (runtime mirror، نه source of truth) ────────────────────
def mirror_to_sqlite(reg: Registry, db_path: str | Path) -> dict:
    """registry را در SQLite جداگانه آینه می‌کند. idempotent (replace)."""
    dbp = Path(db_path)
    dbp.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(dbp))
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS registry_meta (
                key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS registry_subsystems (
                id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS registry_channels (
                id TEXT PRIMARY KEY, data TEXT NOT NULL);
        """)
        conn.execute("DELETE FROM registry_subsystems")
        conn.execute("DELETE FROM registry_channels")
        for s in reg.subsystems:
            conn.execute("INSERT OR REPLACE INTO registry_subsystems VALUES (?,?)",
                         (s.get("id"), json.dumps(s, ensure_ascii=False)))
        for c in reg.channels:
            conn.execute("INSERT OR REPLACE INTO registry_channels VALUES (?,?)",
                         (c.get("id"), json.dumps(c, ensure_ascii=False)))
        now = datetime.now().isoformat(timespec="seconds")
        for k, v in (("version", str(reg.version)),
                     ("mirrored_at", now),
                     ("source", reg.source_path)):
            conn.execute("INSERT OR REPLACE INTO registry_meta VALUES (?,?)", (k, v))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "subsystems": len(reg.subsystems),
            "channels": len(reg.channels), "db": str(dbp)}


def read_mirror(db_path: str | Path) -> dict:
    """خواندنِ آینه (برای UI/گزارش)."""
    dbp = Path(db_path)
    if not dbp.exists():
        return {"ok": False, "reason": "mirror وجود ندارد", "subsystems": [], "channels": []}
    conn = sqlite3.connect(str(dbp))
    try:
        subs = [json.loads(r[0]) for r in
                conn.execute("SELECT data FROM registry_subsystems").fetchall()]
        chans = [json.loads(r[0]) for r in
                 conn.execute("SELECT data FROM registry_channels").fetchall()]
        meta = dict(conn.execute("SELECT key, value FROM registry_meta").fetchall())
    finally:
        conn.close()
    return {"ok": True, "meta": meta, "subsystems": subs, "channels": chans}
