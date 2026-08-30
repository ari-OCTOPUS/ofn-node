"""تستِ WAL/busy_timeout و ایندکس‌های timestamp در memory.store (روی DB موقت)."""
from tests import _bootstrap  # noqa: F401

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import memory.store as store


class TestEnsureDbPragmasAndIndexes(unittest.TestCase):
    def test_wal_and_indexes_on_fresh_db(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            with mock.patch.object(store, "DB_PATH", db):
                store._ensure_db()
            conn = sqlite3.connect(str(db))
            try:
                mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
                self.assertEqual(str(mode).lower(), "wal")
                exp_idx = {r[1] for r in
                           conn.execute("PRAGMA index_list('experiments')")}
                self.assertIn("idx_exp_ts", exp_idx)
                hyp_idx = {r[1] for r in
                           conn.execute("PRAGMA index_list('hypotheses')")}
                self.assertIn("idx_hyp_ts", hyp_idx)
            finally:
                conn.close()

    def test_migration_user_version_and_mi_column(self):
        """B6: مهاجرتِ نسخه‌دار — user_version=2 و ستونِ temporal_mi موجود."""
        import memory.research_store as rs
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            with mock.patch.object(store, "DB_PATH", db), \
                 mock.patch.object(rs, "DB_PATH", db):
                rs._ensure_research_tables()
            conn = sqlite3.connect(str(db))
            try:
                v = conn.execute("PRAGMA user_version").fetchone()[0]
                self.assertEqual(v, 2)
                cols = {r[1] for r in conn.execute("PRAGMA table_info(patterns)")}
                self.assertIn("temporal_mi", cols)
            finally:
                conn.close()

    def test_migration_adds_column_to_legacy_db(self):
        """DB قدیمی (بدونِ ستون) → ALTER خودکار + user_version=2."""
        import memory.research_store as rs
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "legacy.db"
            conn = sqlite3.connect(str(db))
            conn.execute("CREATE TABLE patterns (id INTEGER PRIMARY KEY, "
                         "timestamp TEXT, name TEXT, delta_self REAL, tags TEXT)")
            conn.commit()
            conn.close()
            with mock.patch.object(store, "DB_PATH", db), \
                 mock.patch.object(rs, "DB_PATH", db):
                rs._ensure_research_tables()
            conn = sqlite3.connect(str(db))
            try:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(patterns)")}
                self.assertIn("temporal_mi", cols)
                self.assertEqual(
                    conn.execute("PRAGMA user_version").fetchone()[0], 2)
            finally:
                conn.close()

    def test_ensure_db_idempotent(self):
        """دوبار اجرا نباید خطا بدهد (CREATE ... IF NOT EXISTS)."""
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            with mock.patch.object(store, "DB_PATH", db):
                store._ensure_db()
                store._ensure_db()
            self.assertTrue(db.exists())


if __name__ == "__main__":
    unittest.main()
