"""تستِ B15: پشتیبانِ روتیشن‌دار روی مسیرهای موقت (DB واقعی دست نمی‌خورد)."""
from tests import _bootstrap  # noqa: F401

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import brain.backup as bk
import memory.store as store
import config.settings as settings


class TestBackup(unittest.TestCase):
    def test_backup_now_and_rotation(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            db = tmp / "t.db"
            conn = sqlite3.connect(str(db))
            conn.execute("CREATE TABLE x(i INTEGER)")
            conn.execute("INSERT INTO x VALUES (7)")
            conn.commit()
            conn.close()

            out_dir = tmp / "outputs"
            (out_dir / "self_evolved").mkdir(parents=True)
            (out_dir / "self_evolved" / "strategy.json").write_text(
                '{"k": 1}', encoding="utf-8")

            with mock.patch.object(store, "DB_PATH", db), \
                 mock.patch.object(settings, "OUTPUT_DIR", out_dir):
                dest = bk.backup_now(tag="t1")
                self.assertIsNotNone(dest)
                # DB با backup API کپی شده و قابلِ‌خواندن است
                c2 = sqlite3.connect(str(dest / "t.db"))
                self.assertEqual(c2.execute("SELECT i FROM x").fetchone()[0], 7)
                c2.close()
                self.assertTrue((dest / "strategy.json").exists())

                # روتیشن: ۷ نسخه → فقط ۵ نسخه‌ی آخر بماند
                for i in range(2, 9):
                    bk.backup_now(tag=f"t{i}")
                remaining = sorted(p.name for p in (out_dir / "backups").iterdir()
                                   if p.is_dir())
                self.assertEqual(len(remaining), 5)
                self.assertNotIn("t1", remaining)   # قدیمی‌ترین‌ها حذف

    def test_daily_marker(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            db = tmp / "t.db"
            sqlite3.connect(str(db)).close()
            out_dir = tmp / "outputs"
            out_dir.mkdir()

            with mock.patch.object(store, "DB_PATH", db), \
                 mock.patch.object(settings, "OUTPUT_DIR", out_dir):
                first = bk.maybe_daily_backup()
                second = bk.maybe_daily_backup()
            self.assertIsNotNone(first)
            self.assertIsNone(second, "در یک روز فقط یک backup")


if __name__ == "__main__":
    unittest.main()
