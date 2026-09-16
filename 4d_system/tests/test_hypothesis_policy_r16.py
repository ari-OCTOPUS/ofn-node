"""R16 — تست‌های سیاست صف فرضیه (مصوب مالک 2026-08-16).

پوشش: dedup خانواده‌ای · سقف ورود ۱۰/روز · dormancy · صفر حذف ·
rollback از روی لاگ · صف فعال کوچک می‌شود · رفتار fail-open سیاست ·
صف pending بدون dedup/deferred · timestamp سقف = UTC.
"""
from tests import _bootstrap  # noqa: F401

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from memory import hypothesis_policy as hp
import memory.store as store


def _make_db(tmp: str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(Path(tmp) / "h.db"))
    conn.execute(
        """CREATE TABLE hypotheses (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               timestamp TEXT, domain TEXT, hypothesis TEXT,
               rationale TEXT DEFAULT '', status TEXT DEFAULT 'pending',
               tested INTEGER DEFAULT 0, result TEXT DEFAULT '')""")
    return conn


def _ins(conn, domain, hyp, ts=None, status="pending"):
    conn.execute(
        "INSERT INTO hypotheses (timestamp, domain, hypothesis, status)"
        " VALUES (?, ?, ?, ?)",
        (ts or datetime.now(timezone.utc).isoformat(), domain, hyp, status))


class TestFamilyDedup(unittest.TestCase):
    def test_second_family_member_becomes_dedup(self):
        with tempfile.TemporaryDirectory() as td:
            conn = _make_db(td)
            _base = ("آیا «پایشِ اعتماد» می‌تواند کشفِ بُعدِ پنهان را در محیطِ "
                     "فریبنده تشخیص دهد و به تصمیمِ بهتر برسد")
            _ins(conn, "d1", _base + " — نسخهٔ الف")
            _ins(conn, "d1", _base + " — نسخهٔ ب")
            r = hp.migration_dry_run(conn)
            self.assertEqual(r["by_action"].get("dedup", 0), 1)
            self.assertEqual(r["deletions"], 0)
            out = hp.apply_migration(conn)
            self.assertEqual(out["active_after_actual"], 1)
            row = conn.execute(
                "SELECT status, dedup_of FROM hypotheses WHERE id=2").fetchone()
            self.assertEqual(row[0], "dedup")
            self.assertEqual(row[1], 1)
            # حذف نشده — ردیف هست
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM hypotheses").fetchone()[0], 2)
            conn.close()

    def test_different_families_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            conn = _make_db(td)
            _ins(conn, "d1", "فرضیهٔ الف دربارهٔ X")
            _ins(conn, "d1", "فرضیهٔ کاملاً متفاوت دربارهٔ Y")
            out = hp.apply_migration(conn)
            self.assertEqual(out["active_after_actual"], 2)
            conn.close()


class TestDailyCap(unittest.TestCase):
    def test_eleventh_active_today_defers(self):
        with tempfile.TemporaryDirectory() as td:
            conn = _make_db(td)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            for i in range(hp.DAILY_CAP):
                _ins(conn, "d", f"فرضیهٔ متمایز شمارهٔ {i} دربارهٔ موضوع {i}")
            status, dedup = hp.classify_for_insert(conn, "d", "فرضیهٔ یازدهمِ متمایز")
            self.assertEqual(status, "deferred")
            self.assertIsNone(dedup)
            conn.close()

    def test_under_cap_passes_and_dedup_wins_over_cap(self):
        with tempfile.TemporaryDirectory() as td:
            conn = _make_db(td)
            _ins(conn, "d", "فرضیهٔ خانوادهٔ اصلی")
            status, dedup = hp.classify_for_insert(conn, "d", "فرضیهٔ خانوادهٔ اصلی")
            self.assertEqual(status, "dedup")
            self.assertEqual(dedup, 1)
            conn.close()

    def test_brain_os_seed_does_not_fill_generator_cap(self):
        with tempfile.TemporaryDirectory() as td:
            conn = _make_db(td)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            for i in range(hp.DAILY_CAP):
                _ins(conn, "brain-os", f"بذر دستورکار {i}",
                     ts=f"{today}T00:00:00+00:00")
            status, dedup = hp.classify_for_insert(
                conn, "autonomous-creative", "فرضیهٔ مولدِ متمایز")
            self.assertEqual(status, "pending")
            self.assertIsNone(dedup)
            conn.close()


class TestDormancy(unittest.TestCase):
    def test_old_pending_goes_dormant(self):
        with tempfile.TemporaryDirectory() as td:
            conn = _make_db(td)
            old = (datetime.now(timezone.utc) -
                   timedelta(days=hp.DORMANCY_DAYS + 5)).isoformat()
            _ins(conn, "d", "فرضیهٔ کهنه و بی‌همتا", ts=old)
            out = hp.apply_migration(conn)
            self.assertEqual(out["active_after_actual"], 0)
            self.assertEqual(conn.execute(
                "SELECT status FROM hypotheses WHERE id=1").fetchone()[0], "dormant")
            conn.close()


class TestRollback(unittest.TestCase):
    def test_full_rollback_restores_pending(self):
        with tempfile.TemporaryDirectory() as td:
            conn = _make_db(td)
            _base = ("آیا «پایشِ اعتماد» می‌تواند کشفِ بُعدِ پنهان را در محیطِ "
                     "فریبنده تشخیص دهد و به تصمیمِ بهتر برسد")
            _ins(conn, "d", _base + " — نسخهٔ الف")
            _ins(conn, "d", _base + " — نسخهٔ ب")
            old = (datetime.now(timezone.utc) -
                   timedelta(days=hp.DORMANCY_DAYS + 1)).isoformat()
            _ins(conn, "d2", "کهنه", ts=old)
            hp.apply_migration(conn)
            n = hp.rollback_last_migration(conn)
            self.assertEqual(n, 2)   # dedup + dormant
            statuses = [r[0] for r in conn.execute(
                "SELECT status FROM hypotheses ORDER BY id")]
            self.assertEqual(statuses, ["pending", "pending", "pending"])
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM hypothesis_policy_events").fetchone()[0], 0)
            conn.close()


class TestAdmissionShrink(unittest.TestCase):
    def test_queue_shrinks_without_deletion(self):
        with tempfile.TemporaryDirectory() as td:
            conn = _make_db(td)
            for i in range(30):
                _ins(conn, "d", f"فرضیهٔ تکراریِ یکسان شماره {i % 3}")
            before = conn.execute(
                "SELECT COUNT(*) FROM hypotheses").fetchone()[0]
            out = hp.apply_migration(conn)
            after = conn.execute(
                "SELECT COUNT(*) FROM hypotheses").fetchone()[0]
            self.assertEqual(before, after, "حذف رخ داد!")
            self.assertLess(out["active_after_actual"], out["active_before"])
            conn.close()


class TestStoreFailOpenAndQueue(unittest.TestCase):
    """سیم‌کشی store.save_hypothesis / get_pending — یافته‌های Bugbot."""

    def test_fail_open_inserts_without_policy_columns(self):
        """سیاست که بمیرد، INSERT ستون‌های ALTER‌نشده را نمی‌خواهد."""
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            with mock.patch.object(store, "DB_PATH", db), mock.patch(
                "memory.hypothesis_policy.classify_for_insert",
                side_effect=RuntimeError("policy down"),
            ):
                hid = store.save_hypothesis("d", "فرضیهٔ fail-open")
            self.assertTrue(hid)
            conn = sqlite3.connect(str(db))
            try:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(hypotheses)")}
                self.assertNotIn("policy_tag", cols)
                self.assertNotIn("dedup_of", cols)
                row = conn.execute(
                    "SELECT status, hypothesis FROM hypotheses WHERE id=?",
                    (hid,),
                ).fetchone()
                self.assertEqual(row[0], "pending")
                self.assertIn("fail-open", row[1])
            finally:
                conn.close()

    def test_pending_queue_excludes_dedup_and_deferred(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            with mock.patch.object(store, "DB_PATH", db):
                ids = [
                    store.save_hypothesis("d", f"فرضیهٔ متمایز شمارهٔ {i} موضوع {i}")
                    for i in range(hp.DAILY_CAP)
                ]
                deferred_id = store.save_hypothesis("d", "فرضیهٔ یازدهمِ متمایز سقف")
                dup_id = store.save_hypothesis(
                    "d", f"فرضیهٔ متمایز شمارهٔ {0} موضوع {0}"
                )
                pending = store.get_pending_hypotheses(limit=50)
                stats = store.get_stats()
            conn = sqlite3.connect(str(db))
            try:
                by_id = {
                    r[0]: r[1]
                    for r in conn.execute("SELECT id, status FROM hypotheses")
                }
            finally:
                conn.close()
            self.assertEqual(by_id[deferred_id], "deferred")
            self.assertEqual(by_id[dup_id], "dedup")
            pending_ids = {r["id"] for r in pending}
            self.assertEqual(pending_ids, set(ids))
            self.assertNotIn(deferred_id, pending_ids)
            self.assertNotIn(dup_id, pending_ids)
            self.assertTrue(all(r.get("status") == "pending" for r in pending))
            self.assertEqual(stats["pending_hyp"], hp.DAILY_CAP)

    def test_insert_timestamp_date_matches_utc_cap_day(self):
        """نزدیک نیمه‌شب محلی: سقف باید روز UTC را ببیند نه تقویم naive."""

        class _Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is timezone.utc:
                    return cls(2026, 8, 15, 14, 30, 0, tzinfo=timezone.utc)
                return cls(2026, 8, 16, 0, 30, 0)

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            with mock.patch.object(store, "DB_PATH", db), mock.patch.object(
                store, "datetime", _Clock
            ):
                hid = store.save_hypothesis("d", "فرضیهٔ مرزِ نیمه‌شب")
            conn = sqlite3.connect(str(db))
            try:
                ts, status = conn.execute(
                    "SELECT timestamp, status FROM hypotheses WHERE id=?",
                    (hid,),
                ).fetchone()
            finally:
                conn.close()
            self.assertTrue(str(ts).startswith("2026-08-15"))
            self.assertNotIn("2026-08-16", str(ts)[:10])
            self.assertEqual(status, "pending")


if __name__ == "__main__":
    unittest.main()
