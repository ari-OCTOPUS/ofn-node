"""
memory/store.py — SQLite-backed experiment history.

Stores every experiment result, reflection, and hypothesis.
Enables 'learning from experience' — agents can query past experiments.
"""
from __future__ import annotations

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict


DB_PATH = Path(__file__).resolve().parent.parent / "outputs" / "4d_experiments.db"


@contextmanager
def _conn(row_factory=None):
    """B5: اتصالِ ایمن — بسته‌شدنِ تضمینی حتی در مسیرِ خطا (try/finally).

    قبلاً conn.close() فقط در مسیرِ موفق بود؛ هر exception وسطِ کوئری
    (به‌خصوص database is locked) اتصال و قفلش را نشت می‌داد.
    """
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    if row_factory is not None:
        conn.row_factory = row_factory
    try:
        yield conn
    finally:
        conn.close()


def _ensure_db():
    """Create the database and tables if they don't exist."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        _ensure_db_body(conn)
    finally:
        conn.close()


def _ensure_db_body(conn) -> None:
    # WAL در خودِ فایلِ DB ماندگار می‌شود → همه‌ی اتصال‌های بعدی (Streamlit + CLI
    # هم‌زمان) از خواننده/نویسنده‌ی هم‌روند سود می‌برند و «database is locked»
    # بسیار نادر می‌شود. additive — هیچ schema ای عوض نمی‌شود.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except sqlite3.Error:
        pass
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS experiments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            source      TEXT,
            n_points    INTEGER,
            delta_self  REAL,
            e_shadow    REAL,
            temporal_mi REAL,
            rho_hat     REAL,
            verdict     TEXT,
            confidence  TEXT,
            detectable  INTEGER,
            narrative   TEXT,
            reflection  TEXT,
            metadata    TEXT
        );

        CREATE TABLE IF NOT EXISTS hypotheses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            domain      TEXT,
            hypothesis  TEXT NOT NULL,
            rationale   TEXT,
            status      TEXT DEFAULT 'pending',
            tested      INTEGER DEFAULT 0,
            result      TEXT
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            thread_id   TEXT,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reflections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            experiment_id INTEGER,
            quality     TEXT,
            feedback    TEXT,
            score       REAL
        );

        CREATE TABLE IF NOT EXISTS rhythms (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            name        TEXT NOT NULL,
            source_type TEXT,
            n_points    INTEGER,
            mean        REAL,
            std         REAL,
            mi          REAL,
            rho_hat     REAL,
            detectable  INTEGER,
            file_path   TEXT,
            tags        TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_exp_source ON experiments(source);
        CREATE INDEX IF NOT EXISTS idx_exp_verdict ON experiments(verdict);
        -- کوئری‌های داغ ORDER BY timestamp DESC روی جدول‌های همیشه-درحال-رشد:
        CREATE INDEX IF NOT EXISTS idx_exp_ts ON experiments(timestamp);
        CREATE INDEX IF NOT EXISTS idx_hyp_ts ON hypotheses(timestamp);
        CREATE INDEX IF NOT EXISTS idx_hyp_status ON hypotheses(status);
        CREATE INDEX IF NOT EXISTS idx_conv_thread ON conversations(thread_id);
        CREATE INDEX IF NOT EXISTS idx_rhythm_name ON rhythms(name);
        CREATE INDEX IF NOT EXISTS idx_rhythm_tags ON rhythms(tags);
    """)
    conn.commit()


@dataclass
class ExperimentRecord:
    """A single experiment result, ready to store."""
    source: str
    n_points: int
    delta_self: float
    e_shadow: float
    temporal_mi: float
    rho_hat: float
    verdict: str
    confidence: str
    detectable: bool
    narrative: str
    reflection: str = ""
    metadata: dict = field(default_factory=dict)


def save_experiment(rec: ExperimentRecord) -> int:
    """Persist an experiment to SQLite. Returns the new row ID."""
    _ensure_db()
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO experiments
               (timestamp, source, n_points, delta_self, e_shadow, temporal_mi,
                rho_hat, verdict, confidence, detectable, narrative, reflection, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), rec.source, rec.n_points,
             rec.delta_self, rec.e_shadow, rec.temporal_mi, rec.rho_hat,
             rec.verdict, rec.confidence, int(rec.detectable),
             rec.narrative, rec.reflection, json.dumps(rec.metadata))
        )
        row_id = cur.lastrowid
        conn.commit()
        return row_id


def query_experiments(source: str = "", verdict: str = "",
                      limit: int = 20) -> list[dict]:
    """Query past experiments by source or verdict."""
    _ensure_db()
    query = "SELECT * FROM experiments WHERE 1=1"
    params: list[Any] = []
    if source:
        query += " AND source LIKE ?"
        params.append(f"%{source}%")
    if verdict:
        query += " AND verdict LIKE ?"
        params.append(f"%{verdict}%")
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with _conn(row_factory=sqlite3.Row) as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def save_hypothesis(domain: str, hypothesis: str, rationale: str = "") -> int:
    """Store a new hypothesis for future testing.

    R16 (مصوب مالک 2026-08-16): ورود از سیاستِ صف می‌گذرد — dedup خانواده‌ای
    یا سقفِ ۱۰ ورودِ فعال در روز؛ ردیف همیشه نوشته می‌شود (حذف ممنوع)، فقط
    status برچسب می‌خورد. غیبتِ ماژولِ سیاست = رفتارِ قبل (fail-open به
    pending، ثبتِ خطا در لاگ) — سیاست نباید نوشتن را بکشد.

    Fail-open هرگز ستون‌های policy_tag/dedup_of را INSERT نمی‌کند: آن ستون‌ها
    را فقط classify_for_insert با ALTER می‌سازد؛ اگر سیاست بمیرد، INSERTِ
    قدیمی (بدون آن ستون‌ها) باید همچنان pending بنویسد نه OperationalError.
    timestamp و سقف روزانه هر دو از همان لحظهٔ UTC می‌آیند."""
    _ensure_db()
    now = datetime.now(timezone.utc)
    ts = now.isoformat(timespec="seconds")
    today = now.strftime("%Y-%m-%d")
    status = "pending"
    dedup_of = None
    tag = None
    extras = False
    try:
        from memory.hypothesis_policy import (classify_for_insert, DAILY_CAP,
                                              POLICY_VERSION)
        with _conn() as conn:
            status, dedup_of = classify_for_insert(
                conn, domain, hypothesis, today=today)
        if status == "dedup":
            tag = f"{POLICY_VERSION}:family:{dedup_of}"
        elif status == "deferred":
            tag = f"{POLICY_VERSION}:cap:{DAILY_CAP}"
        extras = True
    except Exception as e:  # noqa: BLE001 — سیاست fail-open است
        import logging
        logging.getLogger(__name__).warning("hypothesis_policy unavailable: %s", e)
        status = "pending"
        dedup_of = None
        tag = None
        extras = False
    with _conn() as conn:
        if extras:
            cur = conn.execute(
                "INSERT INTO hypotheses (timestamp, domain, hypothesis, rationale,"
                " status, policy_tag, dedup_of) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ts, domain, hypothesis, rationale, status, tag, dedup_of),
            )
        else:
            cur = conn.execute(
                "INSERT INTO hypotheses (timestamp, domain, hypothesis, rationale,"
                " status) VALUES (?, ?, ?, ?, ?)",
                (ts, domain, hypothesis, rationale, status),
            )
        row_id = cur.lastrowid
        conn.commit()
        return row_id


def get_pending_hypotheses(limit: int = 10) -> list[dict]:
    """صفِ فعال R16: فقط pendingِ تست‌نشده — dedup/deferred/dormant بیرون می‌مانند."""
    _ensure_db()
    with _conn(row_factory=sqlite3.Row) as conn:
        rows = conn.execute(
            "SELECT * FROM hypotheses WHERE tested = 0 AND status = 'pending'"
            " ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def save_conversation(thread_id: str, role: str, content: str):
    """Save a conversation message."""
    _ensure_db()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO conversations (timestamp, thread_id, role, content) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), thread_id, role, content)
        )
        conn.commit()


def load_conversation(thread_id: str, limit: int = 50) -> list[dict]:
    """Load conversation history for a thread."""
    _ensure_db()
    with _conn(row_factory=sqlite3.Row) as conn:
        rows = conn.execute(
            "SELECT role, content FROM conversations WHERE thread_id = ? ORDER BY timestamp ASC LIMIT ?",
            (thread_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def save_reflection(experiment_id: int, quality: str, feedback: str,
                    score: float):
    """Save a self-reflection on an experiment."""
    _ensure_db()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO reflections (timestamp, experiment_id, quality, feedback, score)
               VALUES (?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), experiment_id, quality, feedback, score)
        )
        conn.commit()


def get_stats() -> dict:
    """Summary statistics for the UI."""
    _ensure_db()
    with _conn() as conn:
        stats = {}
        stats["experiments"] = conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
        stats["hypotheses"] = conn.execute("SELECT COUNT(*) FROM hypotheses").fetchone()[0]
        stats["pending_hyp"] = conn.execute(
            "SELECT COUNT(*) FROM hypotheses WHERE tested=0 AND status='pending'"
        ).fetchone()[0]
        stats["conversations"] = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        stats["reflections"] = conn.execute("SELECT COUNT(*) FROM reflections").fetchone()[0]

        # average metrics from experiments
        row = conn.execute(
            "SELECT AVG(e_shadow), AVG(delta_self), AVG(temporal_mi) FROM experiments"
        ).fetchone()
        stats["avg_e_shadow"] = row[0] or 0.0
        stats["avg_delta_self"] = row[1] or 0.0
        stats["avg_temporal_mi"] = row[2] or 0.0
        return stats


if __name__ == "__main__":
    _ensure_db()
    print(f"✓ SQLite database initialized at {DB_PATH}")

    # Quick test
    rec = ExperimentRecord(
        source="test", n_points=1000, delta_self=0.12, e_shadow=0.01,
        temporal_mi=0.005, rho_hat=0.3, verdict="TEST",
        confidence="high", detectable=True, narrative="test run"
    )
    rid = save_experiment(rec)
    print(f"✓ Saved experiment #{rid}")

    results = query_experiments(limit=5)
    print(f"✓ Queried {len(results)} experiments")

    stats = get_stats()
    print(f"✓ Stats: {stats}")
