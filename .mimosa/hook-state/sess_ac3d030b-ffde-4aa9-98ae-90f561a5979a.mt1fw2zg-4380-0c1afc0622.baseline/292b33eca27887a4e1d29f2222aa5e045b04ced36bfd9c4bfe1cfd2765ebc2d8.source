"""ذخیره‌سازِ ساده با پایگاه‌دادهٔ سبک (SQLite): شناسهٔ فرایندها، پرچم‌ها، دفتر رویدادها."""
import sqlite3
import time
from pathlib import Path
from typing import List, Optional, Tuple


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self) -> None:
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS proc (id TEXT PRIMARY KEY, pid INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS flags (k TEXT PRIMARY KEY, v TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS events (ts REAL, kind TEXT, project TEXT, detail TEXT, actor TEXT)")
            cols = [r[1] for r in c.execute("PRAGMA table_info(events)").fetchall()]
            if "actor" not in cols:
                c.execute("ALTER TABLE events ADD COLUMN actor TEXT")

    def set_pid(self, pid_id: str, pid: int) -> None:
        with self._conn() as c:
            c.execute("REPLACE INTO proc (id, pid) VALUES (?, ?)", (pid_id, pid))

    def get_pid(self, pid_id: str) -> Optional[int]:
        with self._conn() as c:
            row = c.execute("SELECT pid FROM proc WHERE id = ?", (pid_id,)).fetchone()
            return int(row["pid"]) if row else None

    def clear_pid(self, pid_id: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM proc WHERE id = ?", (pid_id,))

    def set_flag(self, k: str, v: str) -> None:
        with self._conn() as c:
            c.execute("REPLACE INTO flags (k, v) VALUES (?, ?)", (k, v))

    def get_flag(self, k: str, default: Optional[str] = None) -> Optional[str]:
        with self._conn() as c:
            row = c.execute("SELECT v FROM flags WHERE k = ?", (k,)).fetchone()
            return row["v"] if row else default

    def log(self, kind: str, project: str, detail: str = "", actor: str = "-") -> None:
        with self._conn() as c:
            c.execute("INSERT INTO events (ts, kind, project, detail, actor) VALUES (?, ?, ?, ?, ?)",
                      (time.time(), kind, project, detail, actor))

    def recent_events(self, n: int = 20) -> List[Tuple]:
        with self._conn() as c:
            rows = c.execute("SELECT ts, kind, project, detail, actor FROM events ORDER BY ts DESC LIMIT ?", (n,)).fetchall()
            return [(r["ts"], r["kind"], r["project"], r["detail"], r["actor"]) for r in rows]
