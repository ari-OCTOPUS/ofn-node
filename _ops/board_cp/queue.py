"""صف SQLite فرمان — stdlib-only. مسیر با OCTOPUS_BOARD_CP_DB قابلِ override."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path

from .schema import Command, CommandState, iso, now_utc, transition_allowed

_lock = threading.Lock()
_FORBIDDEN_NET = (":8796", "127.0.0.1:8796", "/api/v1/command", "/api/v1/brain/ask")


def _db_path() -> Path:
    override = str(os.environ.get("OCTOPUS_BOARD_CP_DB", "")).strip()
    if override:
        return Path(override)
    try:
        import opslib  # noqa: WPS433
        root = Path(opslib.STATE_DIR) / "board_cp"
    except Exception:  # noqa: BLE001
        root = Path(__file__).resolve().parents[1] / "state" / "board_cp"
    root.mkdir(parents=True, exist_ok=True)
    return root / "commands.sqlite"


def _connect() -> sqlite3.Connection:
    p = _db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p), timeout=5.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute(
        """CREATE TABLE IF NOT EXISTS commands (
            message_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            state TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_commands_state ON commands(state, created_at)"
    )
    return con


def insert(cmd: Command, *, kind: str, state: CommandState) -> dict:
    payload = json.dumps(cmd.to_json(), ensure_ascii=False)
    for bad in _FORBIDDEN_NET:
        if bad in payload:
            raise ValueError("payload-hits-forbidden-surface")
    now = iso(now_utc())
    with _lock:
        con = _connect()
        try:
            con.execute(
                "INSERT INTO commands(message_id, kind, state, payload_json, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?)",
                (cmd.message_id, kind, str(state), payload, now, now),
            )
            con.commit()
        finally:
            con.close()
    return {"message_id": cmd.message_id, "kind": kind, "state": str(state)}


def get(message_id: str) -> dict | None:
    with _lock:
        con = _connect()
        try:
            row = con.execute(
                "SELECT * FROM commands WHERE message_id=?", (message_id,)
            ).fetchone()
        finally:
            con.close()
    if not row:
        return None
    return dict(row)


def list_by_state(state: CommandState, *, limit: int = 8) -> list:
    with _lock:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT * FROM commands WHERE state=? ORDER BY created_at ASC LIMIT ?",
                (str(state), int(limit)),
            ).fetchall()
        finally:
            con.close()
    return [dict(r) for r in rows]


def set_state(message_id: str, to_state: CommandState) -> dict:
    row = get(message_id)
    if not row:
        raise KeyError("not-found")
    from_state = CommandState(row["state"])
    if not transition_allowed(from_state, to_state):
        raise ValueError(f"bad-transition:{from_state}->{to_state}")
    now = iso(now_utc())
    with _lock:
        con = _connect()
        try:
            con.execute(
                "UPDATE commands SET state=?, updated_at=? WHERE message_id=?",
                (str(to_state), now, message_id),
            )
            con.commit()
        finally:
            con.close()
    out = dict(row)
    out["state"] = str(to_state)
    out["updated_at"] = now
    return out
