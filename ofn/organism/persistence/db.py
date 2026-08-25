import os
import sqlite3
import threading
from pathlib import Path

DB_LOCK = threading.RLock()
LIVE_ORGANISM_DB = Path("/opt/octopus/lab/lab-data/organism.db")
ALLOW_LIVE_SCHEMA_ENV = "OCTOPUS_ALLOW_LIVE_SCHEMA"
ADDITIVE_MIGRATION_VERSION = "phase3-skin-1"
ADDITIVE_LIVE_TABLES = (
    "memory_read_receipts",
    "decision_evidence",
    "wan_fetches",
)
ADDITIVE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS memory_read_receipts (
      receipt_id TEXT PRIMARY KEY,
      purpose TEXT NOT NULL,
      decision_time REAL NOT NULL,
      recorded_at REAL NOT NULL,
      occurred_at REAL,
      created_at REAL,
      rows_returned INTEGER NOT NULL,
      future_use_count INTEGER NOT NULL CHECK (future_use_count = 0),
      ok INTEGER NOT NULL CHECK (ok IN (0,1)),
      error TEXT,
      query_json TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS memory_read_receipts_purpose ON memory_read_receipts(purpose)",
    """
    CREATE TABLE IF NOT EXISTS decision_evidence (
      evidence_id TEXT PRIMARY KEY,
      purpose TEXT NOT NULL,
      decision_time REAL NOT NULL,
      receipt_id TEXT NOT NULL,
      event_ids_json TEXT NOT NULL,
      episode_ids_json TEXT NOT NULL,
      created_at REAL NOT NULL,
      executable INTEGER NOT NULL CHECK (executable = 0)
    )
    """,
    "CREATE INDEX IF NOT EXISTS decision_evidence_purpose ON decision_evidence(purpose)",
    """
    CREATE TABLE IF NOT EXISTS wan_fetches (
      fetch_id TEXT PRIMARY KEY,
      created_at REAL NOT NULL,
      url TEXT NOT NULL,
      host TEXT NOT NULL,
      kind TEXT NOT NULL,
      status TEXT NOT NULL,
      claim_level TEXT NOT NULL,
      excerpt TEXT NOT NULL,
      response_hash TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS wan_fetches_created ON wan_fetches(created_at)",
)

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
CREATE TABLE IF NOT EXISTS self_models (
  version INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at REAL NOT NULL,
  source_event_id TEXT,
  state_json TEXT NOT NULL,
  state_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS world_hosts (
  host_id TEXT PRIMARY KEY,
  ip TEXT NOT NULL,
  label TEXT,
  status TEXT NOT NULL,
  last_change_at REAL,
  observations INTEGER NOT NULL DEFAULT 0,
  up_observations INTEGER NOT NULL DEFAULT 0,
  updated_at REAL NOT NULL,
  last_probe_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS utterances (
  utterance_id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  kind TEXT NOT NULL,
  text TEXT NOT NULL,
  source_event_id TEXT,
  grounded_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS growth_habits (
  habit_id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  parameter TEXT NOT NULL,
  baseline_json TEXT NOT NULL,
  candidate_json TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS lessons (
  lesson_id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  source TEXT NOT NULL,
  topic TEXT NOT NULL,
  fact TEXT NOT NULL,
  evidence TEXT NOT NULL,
  status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exams (
  exam_id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  prompt TEXT NOT NULL,
  expected_json TEXT NOT NULL,
  forbidden_json TEXT NOT NULL,
  answer TEXT,
  passed INTEGER NOT NULL,
  notes TEXT
);
CREATE TABLE IF NOT EXISTS inner_speech (
  speech_id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  prompt TEXT NOT NULL,
  answer TEXT NOT NULL,
  kind TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS school_courses (
  course_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  evidence TEXT NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS futures (
  path_id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  title TEXT NOT NULL,
  hypothesis TEXT NOT NULL,
  status TEXT NOT NULL,
  evidence TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS learned_topics (
  topic_id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  topic TEXT NOT NULL,
  summary TEXT NOT NULL,
  source TEXT NOT NULL,
  claim_level TEXT NOT NULL,
  evidence TEXT NOT NULL,
  response_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS learned_topics_created ON learned_topics(created_at);
CREATE TABLE IF NOT EXISTS memory_read_receipts (
  receipt_id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  decision_time REAL NOT NULL,
  recorded_at REAL NOT NULL,
  occurred_at REAL,
  created_at REAL,
  rows_returned INTEGER NOT NULL,
  future_use_count INTEGER NOT NULL CHECK (future_use_count = 0),
  ok INTEGER NOT NULL CHECK (ok IN (0,1)),
  error TEXT,
  query_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS memory_read_receipts_purpose ON memory_read_receipts(purpose);
CREATE TABLE IF NOT EXISTS decision_evidence (
  evidence_id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  decision_time REAL NOT NULL,
  receipt_id TEXT NOT NULL,
  event_ids_json TEXT NOT NULL,
  episode_ids_json TEXT NOT NULL,
  created_at REAL NOT NULL,
  executable INTEGER NOT NULL CHECK (executable = 0)
);
CREATE INDEX IF NOT EXISTS decision_evidence_purpose ON decision_evidence(purpose);
CREATE TABLE IF NOT EXISTS wan_fetches (
  fetch_id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  url TEXT NOT NULL,
  host TEXT NOT NULL,
  kind TEXT NOT NULL,
  status TEXT NOT NULL,
  claim_level TEXT NOT NULL,
  excerpt TEXT NOT NULL,
  response_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS wan_fetches_created ON wan_fetches(created_at);
CREATE INDEX IF NOT EXISTS inner_speech_created ON inner_speech(created_at);
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


def _is_live_organism_db(path: Path) -> bool:
    try:
        return path.expanduser().resolve() == LIVE_ORGANISM_DB.resolve()
    except OSError:
        return False


def _table_names(con: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def live_additive_schema_complete(con: sqlite3.Connection) -> bool:
    names = _table_names(con)
    return all(name in names for name in ADDITIVE_LIVE_TABLES)


def apply_additive_live_migration(con: sqlite3.Connection) -> str:
    """Create only new tables/indexes. Never DROP/rename. Transactional."""
    con.execute("BEGIN IMMEDIATE")
    try:
        for statement in ADDITIVE_STATEMENTS:
            con.execute(statement)
        con.execute(
            """
            INSERT INTO meta(k,v) VALUES(?,?)
            ON CONFLICT(k) DO UPDATE SET v=excluded.v
            """,
            ("schema_migration_version", ADDITIVE_MIGRATION_VERSION),
        )
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    return ADDITIVE_MIGRATION_VERSION


def _probe_live_additive_complete(path: Path) -> bool:
    probe = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        probe.execute("PRAGMA query_only=ON")
        return live_additive_schema_complete(probe)
    finally:
        probe.close()


def connect(path: Path) -> sqlite3.Connection:
    resolved = Path(path)
    live = _is_live_organism_db(resolved)
    allow_schema = os.environ.get(ALLOW_LIVE_SCHEMA_ENV) == "1"
    if live and not resolved.is_file():
        raise RuntimeError("live_database_missing")
    if live and not allow_schema and not _probe_live_additive_complete(resolved):
        raise RuntimeError(
            "live_schema_incomplete: OCTOPUS_ALLOW_LIVE_SCHEMA=1 required "
            "only to apply additive phase3-skin-1 tables"
        )
    if not live:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(resolved), isolation_level=None, check_same_thread=False)
    try:
        with DB_LOCK:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA synchronous=FULL")
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("PRAGMA busy_timeout=5000")
            if live:
                if allow_schema:
                    apply_additive_live_migration(con)
                elif not live_additive_schema_complete(con):
                    raise RuntimeError("live_schema_incomplete_after_open")
            else:
                con.executescript(SCHEMA)
                _ensure_episode_uniqueness(con)
    except Exception:
        con.close()
        raise
    return con
