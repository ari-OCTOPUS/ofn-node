"""
memory/research_store.py — Persistent research workspace.

Stores the researcher's saved patterns, composed architectures,
and free-form notes. This is the 'lab notebook' that survives
across sessions.

Three tables:
    patterns       — saved parameter configurations + computed metrics
    architectures  — multi-pattern compositions (hierarchical)
    notes          — free-form research annotations
"""
from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from contextlib import contextmanager

from .store import DB_PATH, _ensure_db


@contextmanager
def _rconn(row_factory=None):
    """B5: اتصالِ ایمن — بسته‌شدنِ تضمینی حتی در مسیرِ خطا (try/finally).

    همان الگوی memory.store._conn؛ برای همه‌ی توابعِ این ماژول.
    """
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    if row_factory is not None:
        conn.row_factory = row_factory
    try:
        yield conn
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════════════
#  Schema initialization
# ════════════════════════════════════════════════════════════════════════

def _ensure_research_tables():
    """Create research tables if they don't exist (extends the main DB)."""
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        _ensure_research_tables_body(conn)
    finally:
        conn.close()


def _ensure_research_tables_body(conn) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS patterns (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            name        TEXT NOT NULL,
            rho         REAL,
            lam         REAL,
            se          REAL,
            sz          REAL,
            sd          REAL,
            delta_self  REAL,
            e_shadow    REAL,
            temporal_mi REAL DEFAULT 0,
            pcai        REAL,
            sms         REAL,
            detectable  INTEGER,
            note        TEXT DEFAULT '',
            tags        TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS architectures (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            parent_ids  TEXT DEFAULT '[]',
            config      TEXT DEFAULT '{}',
            note        TEXT DEFAULT '',
            status      TEXT DEFAULT 'draft'
        );

        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            title       TEXT DEFAULT '',
            content     TEXT NOT NULL,
            linked_pattern_id INTEGER,
            linked_arch_id    INTEGER
        );

        CREATE INDEX IF NOT EXISTS idx_pat_tags ON patterns(tags);
        CREATE INDEX IF NOT EXISTS idx_pat_name ON patterns(name);
        CREATE INDEX IF NOT EXISTS idx_arch_status ON architectures(status);
        CREATE INDEX IF NOT EXISTS idx_note_pattern ON notes(linked_pattern_id);

        -- Meta-research: autonomous self-improvement proposals
        CREATE TABLE IF NOT EXISTS research_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            topic       TEXT NOT NULL,
            direction   TEXT DEFAULT '',
            sources_found   INTEGER DEFAULT 0,
            insights    TEXT DEFAULT '',
            proposals   TEXT DEFAULT '[]',
            status      TEXT DEFAULT 'completed'
        );

        CREATE TABLE IF NOT EXISTS upgrade_proposals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            title       TEXT NOT NULL,
            description TEXT DEFAULT '',
            rationale   TEXT DEFAULT '',
            target_module TEXT DEFAULT '',
            priority    TEXT DEFAULT 'medium',
            effort      TEXT DEFAULT 'medium',
            code_sketch  TEXT DEFAULT '',
            ref_urls     TEXT DEFAULT '[]',
            session_id   INTEGER,
            status       TEXT DEFAULT 'proposed'
        );

        CREATE INDEX IF NOT EXISTS idx_prop_status ON upgrade_proposals(status);
        CREATE INDEX IF NOT EXISTS idx_prop_priority ON upgrade_proposals(priority);
    """)
    # B6: مهاجرتِ نسخه‌دار — تغییرِ ستون در DBهای موجود دیگر خطای خاموش نیست.
    # v2: ستونِ temporal_mi برای patterns (dedup هم‌جنسِ دقیق‌تر — MI بالاخره
    # persist می‌شود). ALTER ADD COLUMN در SQLite ارزان است.
    v = conn.execute("PRAGMA user_version").fetchone()[0]
    if v < 2:
        try:
            conn.execute("ALTER TABLE patterns ADD COLUMN temporal_mi REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # ستون از قبل هست (DB نوساخته با CREATE بالا)
        conn.execute("PRAGMA user_version = 2")
    conn.commit()


# ════════════════════════════════════════════════════════════════════════
#  Data classes
# ════════════════════════════════════════════════════════════════════════

@dataclass
class SavedPattern:
    """A saved parameter configuration with computed metrics."""
    name: str
    rho: float
    lam: float
    se: float
    sz: float
    sd: float
    delta_self: float = 0.0
    e_shadow: float = 0.0
    temporal_mi: float = 0.0
    pcai: float = 0.0
    sms: float = 0.0
    detectable: bool = False
    note: str = ""
    tags: str = ""
    id: Optional[int] = None
    timestamp: str = ""


@dataclass
class SavedArchitecture:
    """A composition of multiple patterns into a hierarchical architecture."""
    name: str
    description: str = ""
    parent_ids: list[int] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    note: str = ""
    status: str = "draft"    # draft / testing / validated
    id: Optional[int] = None
    timestamp: str = ""


@dataclass
class ResearchNote:
    """A free-form research annotation."""
    content: str
    title: str = ""
    linked_pattern_id: Optional[int] = None
    linked_arch_id: Optional[int] = None
    id: Optional[int] = None
    timestamp: str = ""


# ════════════════════════════════════════════════════════════════════════
#  CRUD: Patterns
# ════════════════════════════════════════════════════════════════════════

def save_pattern(p: SavedPattern) -> int:
    """Save a pattern. Returns the row ID."""
    _ensure_research_tables()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.execute(
            """INSERT INTO patterns
               (timestamp, name, rho, lam, se, sz, sd,
                delta_self, e_shadow, temporal_mi, pcai, sms, detectable, note, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), p.name,
             p.rho, p.lam, p.se, p.sz, p.sd,
             p.delta_self, p.e_shadow, p.temporal_mi, p.pcai, p.sms,
             int(p.detectable), p.note, p.tags)
        )
        row_id = cur.lastrowid
        conn.commit()
        return row_id
    finally:
        conn.close()


def get_patterns(tag_filter: str = "", name_filter: str = "",
                 limit: int = 100) -> list[dict]:
    """Query saved patterns."""
    _ensure_research_tables()
    query = "SELECT * FROM patterns WHERE 1=1"
    params: list = []
    if tag_filter:
        query += " AND tags LIKE ?"
        params.append(f"%{tag_filter}%")
    if name_filter:
        query += " AND name LIKE ?"
        params.append(f"%{name_filter}%")
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_pattern(pattern_id: int) -> Optional[dict]:
    """Get a single pattern by ID."""
    _ensure_research_tables()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM patterns WHERE id = ?", (pattern_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def count_patterns() -> int:
    """D2/D3 fix: تعدادِ کلِ الگوهای ذخیره‌شده (برای conclusions/stats).

    قبلاً conclusions فقط frontier را می‌دید، نه جدولِ patterns را. این تابع
    پلِ دومی است.
    """
    _ensure_research_tables()
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    try:
        return conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
    except sqlite3.Error:
        return 0
    finally:
        conn.close()


def delete_pattern(pattern_id: int):
    """Delete a pattern."""
    _ensure_research_tables()
    with _rconn() as conn:
        conn.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
        conn.commit()


def update_pattern_note(pattern_id: int, note: str, tags: str = None):
    """Update the note (and optionally tags) of a pattern."""
    _ensure_research_tables()
    with _rconn() as conn:
        if tags is not None:
            conn.execute(
                "UPDATE patterns SET note = ?, tags = ? WHERE id = ?",
                (note, tags, pattern_id)
            )
        else:
            conn.execute(
                "UPDATE patterns SET note = ? WHERE id = ?",
                (note, pattern_id)
            )
        conn.commit()


# ════════════════════════════════════════════════════════════════════════
#  CRUD: Architectures
# ════════════════════════════════════════════════════════════════════════

def save_architecture(a: SavedArchitecture) -> int:
    """Save a composed architecture."""
    _ensure_research_tables()
    with _rconn() as conn:
        cur = conn.execute(
            """INSERT INTO architectures
               (timestamp, name, description, parent_ids, config, note, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), a.name, a.description,
             json.dumps(a.parent_ids), json.dumps(a.config),
             a.note, a.status)
        )
        row_id = cur.lastrowid
        conn.commit()
        return row_id


def get_architectures(status_filter: str = "", limit: int = 50) -> list[dict]:
    """Query architectures."""
    _ensure_research_tables()
    query = "SELECT * FROM architectures WHERE 1=1"
    params: list = []
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with _rconn(row_factory=sqlite3.Row) as conn:
        rows = conn.execute(query, params).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        d["parent_ids"] = json.loads(d.get("parent_ids", "[]"))
        d["config"] = json.loads(d.get("config", "{}"))
        results.append(d)
    return results


def update_architecture_status(arch_id: int, status: str):
    """Update status: draft → testing → validated."""
    _ensure_research_tables()
    with _rconn() as conn:
        conn.execute(
            "UPDATE architectures SET status = ? WHERE id = ?",
            (status, arch_id)
        )
        conn.commit()


def delete_architecture(arch_id: int):
    _ensure_research_tables()
    with _rconn() as conn:
        conn.execute("DELETE FROM architectures WHERE id = ?", (arch_id,))
        conn.commit()


# ════════════════════════════════════════════════════════════════════════
#  CRUD: Notes
# ════════════════════════════════════════════════════════════════════════

def save_note(n: ResearchNote) -> int:
    _ensure_research_tables()
    with _rconn() as conn:
        cur = conn.execute(
            """INSERT INTO notes
               (timestamp, title, content, linked_pattern_id, linked_arch_id)
               VALUES (?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), n.title, n.content,
             n.linked_pattern_id, n.linked_arch_id)
        )
        row_id = cur.lastrowid
        conn.commit()
        return row_id


def get_notes(search: str = "", limit: int = 50) -> list[dict]:
    _ensure_research_tables()
    query = "SELECT * FROM notes WHERE 1=1"
    params: list = []
    if search:
        query += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    with _rconn(row_factory=sqlite3.Row) as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def delete_note(note_id: int):
    _ensure_research_tables()
    with _rconn() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()


# ════════════════════════════════════════════════════════════════════════
#  Utility: all tags
# ════════════════════════════════════════════════════════════════════════

def get_all_tags() -> list[str]:
    """Get all unique tags across patterns."""
    _ensure_research_tables()
    with _rconn() as conn:
        rows = conn.execute("SELECT tags FROM patterns WHERE tags != ''").fetchall()
    tags = set()
    for (tag_str,) in rows:
        for t in tag_str.split(","):
            t = t.strip()
            if t:
                tags.add(t)
    return sorted(tags)


def get_research_stats() -> dict:
    """Summary statistics for the research workspace."""
    _ensure_research_tables()
    with _rconn() as conn:
        return {
            "patterns": conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0],
            "architectures": conn.execute("SELECT COUNT(*) FROM architectures").fetchone()[0],
            "notes": conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
            "validated": conn.execute(
                "SELECT COUNT(*) FROM architectures WHERE status='validated'"
            ).fetchone()[0],
        }


# ════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════
#  Meta-research: upgrade proposals & research sessions
# ════════════════════════════════════════════════════════════════════════

@dataclass
class UpgradeProposal:
    """A proposal to upgrade the system itself."""
    title: str
    description: str = ""
    rationale: str = ""
    target_module: str = ""       # e.g. "brain/autoloop.py"
    priority: str = "medium"      # low|medium|high|critical
    effort: str = "medium"        # low|medium|high
    code_sketch: str = ""         # pseudo-code or actual snippet
    references: list = field(default_factory=list)  # URLs
    session_id: Optional[int] = None
    status: str = "proposed"      # proposed|approved|implemented|rejected


def save_proposal(p: UpgradeProposal) -> int:
    """Save an upgrade proposal. Returns its ID."""
    _ensure_research_tables()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.execute(
            """INSERT INTO upgrade_proposals
               (timestamp, title, description, rationale, target_module,
                priority, effort, code_sketch, ref_urls, session_id, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), p.title, p.description,
             p.rationale, p.target_module, p.priority, p.effort,
             p.code_sketch, json.dumps(p.references), p.session_id, p.status)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_proposals(limit: int = 50, status: str = None) -> list[dict]:
    """Retrieve upgrade proposals."""
    _ensure_research_tables()
    with _rconn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM upgrade_proposals WHERE status=? ORDER BY id DESC LIMIT ?",
                (status, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM upgrade_proposals ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM upgrade_proposals LIMIT 0").description]
    result = []
    for row in rows:
        d = dict(zip(cols, row))
        d["references"] = json.loads(d.get("ref_urls") or "[]")
        result.append(d)
    return result


def update_proposal_status(proposal_id: int, status: str):
    """Update the status of a proposal."""
    _ensure_research_tables()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("UPDATE upgrade_proposals SET status=? WHERE id=?", (status, proposal_id))
        conn.commit()
    finally:
        conn.close()


def save_research_session(topic: str, direction: str, sources_found: int,
                          insights: str, proposals: list[int]) -> int:
    """Save a meta-research session."""
    _ensure_research_tables()
    with _rconn() as conn:
        cur = conn.execute(
            """INSERT INTO research_sessions
               (timestamp, topic, direction, sources_found, insights, proposals, status)
               VALUES (?, ?, ?, ?, ?, ?, 'completed')""",
            (datetime.now().isoformat(), topic, direction,
             sources_found, insights, json.dumps(proposals))
        )
        conn.commit()
        return cur.lastrowid


def get_research_sessions(limit: int = 20) -> list[dict]:
    """Retrieve meta-research sessions."""
    _ensure_research_tables()
    with _rconn() as conn:
        rows = conn.execute(
            "SELECT * FROM research_sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM research_sessions LIMIT 0").description]
    result = []
    for row in rows:
        d = dict(zip(cols, row))
        d["proposals"] = json.loads(d.get("proposals") or "[]")
        result.append(d)
    return result


# ════════════════════════════════════════════════════════════════════════
#  Self-test
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    _ensure_research_tables()
    print(f"✓ Research tables initialized at {DB_PATH}")

    # Test pattern save
    p = SavedPattern(
        name="high-memory-config", rho=0.8, lam=0.6, se=0.1, sz=0.05, sd=0.1,
        delta_self=0.15, e_shadow=0.02, pcai=0.88, sms=0.15,
        detectable=True, note="حافظه‌ی قوی، نشت متوسط", tags="memory,strong"
    )
    pid = save_pattern(p)
    print(f"✓ Saved pattern #{pid}")

    # Test architecture save
    a = SavedArchitecture(
        name="dual-layer-shadow",
        description="ترکیب لایه‌ی حافظه‌دار با لایه‌ی نشت‌پذیر",
        parent_ids=[pid],
        config={"layers": 2, "coupling": "serial"},
        note="آزمایش ترکیبی"
    )
    aid = save_architecture(a)
    print(f"✓ Saved architecture #{aid}")

    # Test note
    n = ResearchNote(
        title="کشف مهم",
        content="وقتی ρ بالاست و λ متوسط، PCAI بالاترین است",
        linked_pattern_id=pid
    )
    nid = save_note(n)
    print(f"✓ Saved note #{nid}")

    # Query
    patterns = get_patterns()
    print(f"\n✓ Retrieved {len(patterns)} patterns")
    archs = get_architectures()
    print(f"✓ Retrieved {len(archs)} architectures")
    notes = get_notes()
    print(f"✓ Retrieved {len(notes)} notes")

    stats = get_research_stats()
    print(f"\n✓ Stats: {stats}")
    print(f"✓ Tags: {get_all_tags()}")
