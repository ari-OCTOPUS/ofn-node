"""تستِ سقفِ فایل‌های خطیِ append-only (فیکسِ رشدِ بی‌نهایت) + آرشیوِ جدول."""
from tests import _bootstrap  # noqa: F401

import sqlite3
import tempfile
import unittest
from pathlib import Path

import memory.store
from brain.housekeeping import trim_textfile, _archive_rows


class TestTrimTextfile(unittest.TestCase):
    def test_trims_and_archives(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "packets.jsonl"
            p.write_text("".join(f'{{"i": {i}}}\n' for i in range(30)),
                         encoding="utf-8")
            moved = trim_textfile(p, cap=10)
            self.assertEqual(moved, 20)
            kept = p.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(kept), 10)
            self.assertEqual(kept[-1], '{"i": 29}')       # جدیدترها ماندند
            arch = Path(td) / "packets_archive.jsonl"
            self.assertTrue(arch.exists())                 # آرشیو، نه حذف
            self.assertEqual(len(arch.read_text(encoding="utf-8").splitlines()), 20)

    def test_idempotent_when_under_cap(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ideas.md"
            p.write_text("- a\n- b\n", encoding="utf-8")
            self.assertEqual(trim_textfile(p, cap=10), 0)
            self.assertEqual(p.read_text(encoding="utf-8"), "- a\n- b\n")

    def test_missing_file_and_bad_cap_are_noop(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(trim_textfile(Path(td) / "nope.md", cap=10), 0)
            p = Path(td) / "x.md"
            p.write_text("line\n", encoding="utf-8")
            self.assertEqual(trim_textfile(p, cap=0), 0)   # cap نامعتبر → دست نزن

    def test_archive_accumulates_across_runs(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "log.md"
            p.write_text("".join(f"l{i}\n" for i in range(15)), encoding="utf-8")
            trim_textfile(p, cap=10)                       # 5 → آرشیو
            p.write_text(p.read_text(encoding="utf-8")
                         + "".join(f"n{i}\n" for i in range(10)), encoding="utf-8")
            trim_textfile(p, cap=10)                       # 10 دیگر → آرشیو
            arch = Path(td) / "log_archive.md"
            self.assertEqual(len(arch.read_text(encoding="utf-8").splitlines()), 15)


class TestArchiveRowsSchemaDrift(unittest.TestCase):
    """B: جدولِ زنده ستونِ جدید گرفت (مهاجرت) ولی آرشیوِ قدیمی نه →
    قبلاً INSERT SELECT * با «۱۵ ستون/۱۶ مقدار» می‌شکست و سقف اعمال نمی‌شد."""

    def setUp(self):
        self._orig_db = memory.store.DB_PATH   # بازگردانی در tearDown (تستِ بعدی نشکند)

    def tearDown(self):
        memory.store.DB_PATH = self._orig_db

    def _mkdb(self, td: str):
        db = Path(td) / "t.db"
        conn = sqlite3.connect(str(db))
        # جدولِ زنده: id + دو ستونِ داده + ستونِ «مهاجرت‌شده»
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, a, b, migrated)")
        for i in range(30):
            conn.execute("INSERT INTO t (a,b,migrated) VALUES (?,?,?)",
                         (i, i * 2, i * 3))
        # آرشیوِ کهنه: بدونِ ستونِ migrated (drift عمدی)
        conn.execute("CREATE TABLE t_archive (id INTEGER PRIMARY KEY, a, b)")
        conn.commit(); conn.close()
        memory.store.DB_PATH = db          # _archive_rows این را در زمانِ صدا می‌خواند
        return db

    def test_drift_is_healed_cap_enforced_nothing_lost(self):
        with tempfile.TemporaryDirectory() as td:
            db = self._mkdb(td)
            moved = _archive_rows("t", cap=10, archive_table="t_archive")
            self.assertEqual(moved, 20)                     # ۳۰ − سقفِ ۱۰
            conn = sqlite3.connect(str(db))
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM t").fetchone()[0], 10)
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM t_archive").fetchone()[0], 20)
            arch_cols = {r[1] for r in conn.execute(
                "PRAGMA table_info(t_archive)").fetchall()}
            self.assertIn("migrated", arch_cols)            # ستون هم‌تراز شد
            # دادهٔ ستونِ مهاجرت‌شده واقعاً منتقل شد (نه NULL)
            row = conn.execute(
                "SELECT migrated FROM t_archive ORDER BY id LIMIT 1").fetchone()
            self.assertEqual(row[0], 0)                     # اولین ردیف: migrated=0
            conn.close()

    def test_idempotent_second_run(self):
        with tempfile.TemporaryDirectory() as td:
            self._mkdb(td)
            _archive_rows("t", cap=10, archive_table="t_archive")
            self.assertEqual(
                _archive_rows("t", cap=10, archive_table="t_archive"), 0)

    def test_creates_archive_when_absent(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            conn = sqlite3.connect(str(db))
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, a)")
            for i in range(15):
                conn.execute("INSERT INTO t (a) VALUES (?)", (i,))
            conn.commit(); conn.close()
            memory.store.DB_PATH = db
            moved = _archive_rows("t", cap=5, archive_table="t_archive")
            self.assertEqual(moved, 10)
            conn = sqlite3.connect(str(db))
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM t_archive").fetchone()[0], 10)
            conn.close()


if __name__ == "__main__":
    unittest.main()
