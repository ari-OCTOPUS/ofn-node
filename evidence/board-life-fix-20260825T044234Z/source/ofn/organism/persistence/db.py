
import sqlite3
import threading
from pathlib import Path

DB_LOCK = threading.RLock()

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  priority INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  created_at REAL NOT NULL,
  schema_version INTEGER NOT NULL,
  hash TEXT NOT NULL UNIQUE,
  node_seq INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
  delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL REFERENCES events(event_id),
  hash TEXT NOT NULL,
  status TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  created_at REAL NOT NULL,
  done_at REAL
);
CREATE TABLE IF NOT EXISTS identity_heartbeat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  body_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS identity_ledger (
  sequence INTEGER PRIMARY KEY,
  organism_id TEXT NOT NULL,
  boot_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_ns INTEGER NOT NULL,
  previous_hash TEXT NOT NULL,
  entry_hash TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS episodes (
  episode_id TEXT PRIMARY KEY,
  source_event_id TEXT NOT NULL REFERENCES events(event_id),
  event_type TEXT NOT NULL,
  salience REAL NOT NULL,
  outcome TEXT,
  body_json TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ask_cache (
  request_hash TEXT PRIMARY KEY,
  response_text TEXT NOT NULL,
  source_route TEXT NOT NULL,
  source_response_hash TEXT NOT NULL,
  created_at REAL NOT NULL,
  last_used_at REAL NOT NULL,
  hits INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS outbox_status ON outbox(status);
CREATE INDEX IF NOT EXISTS identity_ledger_boot_id ON identity_ledger(boot_id);
CREATE INDEX IF NOT EXISTS episodes_created_at ON episodes(created_at);
"""


def _ensure_episode_uniqueness(con: sqlite3.Connection) -> None:
    duplicates = con.execute(
        """
        SELECT source_event_id, event_type, COUNT(*)
        FROM episodes
        GROUP BY source_event_id, event_type
        HAVING COUNT(*) > 1
        LIMIT 1
        """
    ).fetchone()
    if duplicates:
        raise RuntimeError(
            "episode_uniqueness_migration_requires_owner_data_decision"
        )
    con.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS episodes_source_event
        ON episodes(source_event_id, event_type)
        """
    )


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
    try:
        with DB_LOCK:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA synchronous=FULL")
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("PRAGMA busy_timeout=5000")
            con.executescript(SCHEMA)
            _ensure_episode_uniqueness(con)
    except Exception:
        con.close()
        raise
    return con
