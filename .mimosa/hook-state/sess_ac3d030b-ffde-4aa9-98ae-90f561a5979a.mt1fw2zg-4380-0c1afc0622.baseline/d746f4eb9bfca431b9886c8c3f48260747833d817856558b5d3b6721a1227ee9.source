"""
Database -- Brushline SQLite setup.

PHASE 0 INVARIANT: This database is SEPARATE from LANGAR.
- Different file path (BRUSHLINE_DB_PATH env var)
- Tables prefixed with no shared namespace
- No foreign key references to LANGAR tables

Cross-system data sharing (e.g. shared lead IDs) happens via application-level
JOIN, not at the DB level -- preserving full separation (Phase 0 gate test).
"""
import sqlite3
import threading
from pathlib import Path

from .config import config


def get_db_path() -> str:
    """
    Return Brushline's database path.
    CRITICAL: verify this is never the same as LANGAR's DB path.
    """
    return config.DB_PATH


def init_db() -> None:
    """
    Create all Brushline tables. Idempotent (safe to call on every startup).
    Schema matches data model in MVP s4 and models.py.
    """
    db_path = get_db_path()

    # Create parent directory if needed (skip for :memory:)
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        -- -- leads -----------------------------------------------------------
        CREATE TABLE IF NOT EXISTS leads (
            id           TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            phone        TEXT NOT NULL,        -- PII: never in audit payload
            email        TEXT,                 -- PII: only with express consent
            suburb       TEXT NOT NULL,
            service_type TEXT NOT NULL,
            source_channel TEXT NOT NULL,
            consent_status TEXT,
            notes        TEXT DEFAULT '',
            created_at   TEXT NOT NULL
        );

        -- -- consent_records ----------------------------------------------------
        CREATE TABLE IF NOT EXISTS consent_records (
            id        TEXT PRIMARY KEY,
            lead_id   TEXT NOT NULL REFERENCES leads(id),
            method    TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            evidence  TEXT NOT NULL
        );

        -- -- drafts ---------------------------------------------------------------
        CREATE TABLE IF NOT EXISTS drafts (
            id          TEXT PRIMARY KEY,
            lead_id     TEXT REFERENCES leads(id),
            draft_type  TEXT NOT NULL,
            content     TEXT NOT NULL,
            agent_id    TEXT NOT NULL,
            model_used  TEXT NOT NULL,
            tokens_in   INTEGER DEFAULT 0,
            tokens_out  INTEGER DEFAULT 0,
            cost_usd    REAL DEFAULT 0.0,
            created_at  TEXT NOT NULL
        );

        -- -- gate_results -----------------------------------------------------
        CREATE TABLE IF NOT EXISTS gate_results (
            id               TEXT PRIMARY KEY,
            draft_id         TEXT NOT NULL REFERENCES drafts(id),
            status           TEXT NOT NULL,
            acl_ok           INTEGER NOT NULL DEFAULT 1,
            spam_consent_ok  INTEGER NOT NULL DEFAULT 1,
            sender_id_ok     INTEGER NOT NULL DEFAULT 1,
            privacy_ok       INTEGER NOT NULL DEFAULT 1,
            sovereignty_ok   INTEGER NOT NULL DEFAULT 1,
            flags            TEXT DEFAULT '[]',
            round_num        INTEGER DEFAULT 1,
            checked_at       TEXT NOT NULL
        );

        -- -- approval_actions --------------------------------------------------
        CREATE TABLE IF NOT EXISTS approval_actions (
            id               TEXT PRIMARY KEY,
            draft_id         TEXT NOT NULL REFERENCES drafts(id),
            status           TEXT NOT NULL DEFAULT 'pending',
            operator_chat_id INTEGER,
            edited_content   TEXT,
            reason           TEXT,
            acted_at         TEXT,
            created_at       TEXT NOT NULL,
            priority         TEXT NOT NULL DEFAULT 'low',
            sla_deadline     TEXT,
            expired          INTEGER NOT NULL DEFAULT 0,
            regate_status    TEXT,
            regate_draft_id  TEXT
        );

        -- -- audit_entries (hash-chained, append-only) -------------------------
        CREATE TABLE IF NOT EXISTS audit_entries (
            id          TEXT PRIMARY KEY,
            prev_hash   TEXT NOT NULL,
            entry_hash  TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            entity_id   TEXT NOT NULL,
            payload     TEXT NOT NULL,   -- JSON, no raw PII (INV-2)
            timestamp   TEXT NOT NULL
        );

        -- -- sync_jobs ----------------------------------------------------------
        CREATE TABLE IF NOT EXISTS sync_jobs (
            id                 TEXT PRIMARY KEY,
            lead_id            TEXT NOT NULL REFERENCES leads(id),
            target_system      TEXT NOT NULL,
            status             TEXT NOT NULL DEFAULT 'pending',
            external_client_id TEXT,
            external_job_id    TEXT,
            synced_at          TEXT,
            created_at         TEXT NOT NULL
        );

        -- -- cost_events ----------------------------------------------------------
        CREATE TABLE IF NOT EXISTS cost_events (
            id         TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            agent_id   TEXT NOT NULL,
            model      TEXT NOT NULL,
            cost_usd   REAL NOT NULL,
            cost_aud   REAL NOT NULL,
            tokens_in  INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            timestamp  TEXT NOT NULL
        );

        -- -- brushline_meta -----------------------------------------------------
        -- Identifies this DB as Brushline's (used in Phase 0 gate test)
        CREATE TABLE IF NOT EXISTS brushline_meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        INSERT OR IGNORE INTO brushline_meta VALUES
            ('system',         'brushline'),
            ('schema_version', '1.2'),
            ('phase',          '5');

        -- -- indexes (arch review 2026-07-02): hot-path queries ------------------
        -- check_and_enforce sums cost_events on EVERY external action; without
        -- an index that is a full table scan that grows with history.
        CREATE INDEX IF NOT EXISTS idx_cost_events_ts
            ON cost_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_approval_status
            ON approval_actions(status, priority);
        CREATE INDEX IF NOT EXISTS idx_approval_draft
            ON approval_actions(draft_id, status);
        CREATE INDEX IF NOT EXISTS idx_gate_results_draft
            ON gate_results(draft_id, checked_at);
        CREATE INDEX IF NOT EXISTS idx_consent_lead
            ON consent_records(lead_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_sync_jobs_lead
            ON sync_jobs(lead_id);
        CREATE INDEX IF NOT EXISTS idx_drafts_lead
            ON drafts(lead_id);
        CREATE INDEX IF NOT EXISTS idx_audit_entity
            ON audit_entries(entity_id, event_type);
    """)

    # -- Migration guard: older on-disk DBs (Phase 0/1/2) created
    # approval_actions before priority/sla_deadline/expired/regate_* existed.
    # ALTER TABLE ADD COLUMN is idempotent here via duplicate-column guard.
    _existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(approval_actions)")}
    _new_cols = {
        "priority":        "TEXT NOT NULL DEFAULT 'low'",
        "sla_deadline":    "TEXT",
        "expired":         "INTEGER NOT NULL DEFAULT 0",
        "regate_status":   "TEXT",
        "regate_draft_id": "TEXT",
    }
    for col, ddl in _new_cols.items():
        if col not in _existing_cols:
            conn.execute(f"ALTER TABLE approval_actions ADD COLUMN {col} {ddl}")

    conn.commit()
    conn.close()


# -- Connection pool (P9): one cached connection per thread ------------------
# SQLite connections are not shareable across threads, so we key the cache by
# thread. Returned connections are wrapped so caller `.close()` becomes a no-op
# (the connection returns to the pool instead of being torn down). This cuts the
# open/close churn on the hot path (every audit.append / gate / governance call
# opened + closed its own connection).
_local = threading.local()
_pool_enabled = True
_connect_count = 0
_count_lock = threading.Lock()


class _PooledConnection:
    """Proxy over a real sqlite3.Connection whose close() returns it to the pool
    (no-op) instead of closing it. All other attributes delegate to the real
    connection, so existing `conn.execute(...)` / `conn.commit()` code is
    unchanged."""

    __slots__ = ("_real",)

    def __init__(self, real: sqlite3.Connection) -> None:
        object.__setattr__(self, "_real", real)

    def close(self) -> None:  # pooled: do NOT actually close
        # Arch review 2026-07-02: a real close() discards an uncommitted
        # transaction; the pooled no-op used to LEAK it to the next caller on
        # this thread. Roll back anything uncommitted at hand-back instead.
        real = object.__getattribute__(self, "_real")
        try:
            if real.in_transaction:
                real.rollback()
        except Exception:
            pass
        return None

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_real"), name, value)

    def __enter__(self):
        object.__getattribute__(self, "_real").__enter__()
        return self

    def __exit__(self, *exc):
        return object.__getattribute__(self, "_real").__exit__(*exc)


def _raw_connect() -> sqlite3.Connection:
    global _connect_count
    with _count_lock:
        _connect_count += 1
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_connection():
    """
    Return a database connection. When pooling is enabled (default) this is a
    per-thread cached connection whose close() is a no-op; otherwise a fresh
    real connection (legacy behaviour). Caller may still call .close() safely.
    """
    if not _pool_enabled:
        return _raw_connect()
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _raw_connect()
        _local.conn = conn
    return _PooledConnection(conn)


def reset_pool() -> None:
    """Close and drop this thread's pooled connection (teardown / tests)."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        _local.conn = None


def set_pool_enabled(flag: bool) -> None:
    """Toggle pooling (used by the P9 benchmark / for debugging)."""
    global _pool_enabled
    _pool_enabled = bool(flag)
    if not flag:
        reset_pool()


def connection_count() -> int:
    """Total real sqlite connections opened since the last reset (benchmark)."""
    return _connect_count


def reset_connection_count() -> None:
    global _connect_count
    with _count_lock:
        _connect_count = 0
