"""Incremental local content index (SQLite; Python stdlib only).

Eager on data, lazy on reasoning: on each file event we (re)index just the one
note. Full-text search via SQLite FTS5 when available, with a LIKE fallback so
it also runs where FTS5 is not compiled in. Security: only an explicit
allowlist of text extensions is ever read -- the perception privacy boundary.

Semantic-search hook: to add vectors later, embed the text in `_upsert` and
store it (sqlite-vec or a numpy sidecar). The public API does not change.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_EXTS = {".md", ".markdown", ".txt", ".rst", ".org", ".text"}


class Indexer:
    def __init__(self, db_path: str | Path, exts: set[str] | None = None) -> None:
        self.db_path = str(db_path)
        self.exts = set(exts or DEFAULT_EXTS)
        self.conn = sqlite3.connect(self.db_path)
        self.fts = self._has_fts5()
        self._init_schema()

    # --- setup -----------------------------------------------------------
    def _has_fts5(self) -> bool:
        try:
            self.conn.execute("CREATE VIRTUAL TABLE temp.__probe USING fts5(x)")
            self.conn.execute("DROP TABLE temp.__probe")
            return True
        except sqlite3.OperationalError:
            return False

    def _init_schema(self) -> None:
        c = self.conn
        c.execute("CREATE TABLE IF NOT EXISTS files("
                  "path TEXT PRIMARY KEY, mtime REAL, sha TEXT, size INT, indexed_at TEXT)")
        if self.fts:
            c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5(path, content)")
        else:
            c.execute("CREATE TABLE IF NOT EXISTS notes(path TEXT PRIMARY KEY, content TEXT)")
        c.commit()

    def _allowed(self, p: Path) -> bool:
        return p.suffix.lower() in self.exts

    # --- write -----------------------------------------------------------
    def index_file(self, path: str | Path) -> str:
        """Returns 'indexed' | 'reindexed' | 'unchanged' | 'skipped'."""
        p = Path(path)
        if not p.is_file() or not self._allowed(p):
            return "skipped"
        data = p.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        row = self.conn.execute("SELECT sha FROM files WHERE path=?", (str(p),)).fetchone()
        if row and row[0] == sha:
            return "unchanged"                      # incremental: nothing to do
        self._upsert(str(p), data.decode("utf-8", "replace"), p.stat().st_mtime, sha, len(data))
        return "reindexed" if row else "indexed"

    def _upsert(self, path: str, text: str, mtime: float, sha: str, size: int) -> None:
        c = self.conn
        if self.fts:
            c.execute("DELETE FROM notes WHERE path=?", (path,))
            c.execute("INSERT INTO notes(path, content) VALUES(?, ?)", (path, text))
        else:
            c.execute("INSERT OR REPLACE INTO notes(path, content) VALUES(?, ?)", (path, text))
        c.execute("INSERT OR REPLACE INTO files(path, mtime, sha, size, indexed_at) "
                  "VALUES(?, ?, ?, ?, ?)",
                  (path, mtime, sha, size, datetime.now(timezone.utc).isoformat()))
        c.commit()

    def index_dir(self, root: str | Path) -> dict[str, int]:
        stats = {"indexed": 0, "reindexed": 0, "unchanged": 0, "skipped": 0}
        for p in Path(root).rglob("*"):
            if p.is_file():
                stats[self.index_file(p)] += 1
        return stats

    def remove(self, path: str | Path) -> None:
        c = self.conn
        c.execute("DELETE FROM notes WHERE path=?", (str(path),))
        c.execute("DELETE FROM files WHERE path=?", (str(path),))
        c.commit()

    # --- read ------------------------------------------------------------
    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        c = self.conn
        if self.fts:
            try:
                rows = c.execute(
                    "SELECT path, snippet(notes, 1, '[', ']', '...', 10) "
                    "FROM notes WHERE notes MATCH ? LIMIT ?", (query, k)).fetchall()
                return [{"path": r[0], "snippet": r[1]} for r in rows]
            except sqlite3.OperationalError:
                pass  # malformed MATCH -> fall through to LIKE
        rows = c.execute(
            "SELECT path, substr(content, 1, 140) FROM notes WHERE content LIKE ? LIMIT ?",
            (f"%{query}%", k)).fetchall()
        return [{"path": r[0], "snippet": r[1]} for r in rows]

    def stats(self) -> dict[str, Any]:
        n = self.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        return {"files": n, "fts5": self.fts}

    def close(self) -> None:
        self.conn.close()


if __name__ == "__main__":  # python indexer.py <index.db> <vault_dir> [query]
    import sys
    ix = Indexer(sys.argv[1])
    if len(sys.argv) > 2:
        print("indexed:", ix.index_dir(sys.argv[2]), ix.stats())
    if len(sys.argv) > 3:
        for hit in ix.search(sys.argv[3]):
            print(" ", hit["path"], "->", hit["snippet"])
