"""Phase D — backup/media durability (findings 21, 22, 23, 31, 32, 37, 53).

- verify_backup checks media count + bytes against the manifest
- backup() fails on missing required databases, skips optional ones
- backup_job includes memory.sqlite (Ari approved)
- attach_media rolls back written files when the DB step fails
- delete_media leaves the DB row if file deletion fails
- restore_media restores the media tree from a verified backup (sandbox)
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest

from ofn.adapters.backup import (
    backup, mirror_media, restore_media, verify_backup,
)
from ofn.adapters.sqlite_base import connect

from tests.tmpdir import temp_dir

STAMP = "20260810-120000"


def _make_db(path: str) -> None:
    conn = connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute("INSERT INTO t (v) VALUES ('x')")
    conn.close()


def _make_media(root: str, n: int = 3) -> None:
    os.makedirs(os.path.join(root, "sub"), exist_ok=True)
    for i in range(n):
        with open(os.path.join(root, f"p{i}.jpg"), "wb") as fh:
            fh.write(b"jpeg-data-" + str(i).encode())
    with open(os.path.join(root, "sub", "q.jpg"), "wb") as fh:
        fh.write(b"sub-data")


class TestVerifyBackupMedia(unittest.TestCase):
    """verify_backup must check media count and bytes, not just DBs."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.db_src = os.path.join(self.dir, "ledger.sqlite")
        _make_db(self.db_src)
        self.media_root = os.path.join(self.dir, "photos")
        _make_media(self.media_root)
        self.dest = os.path.join(self.dir, "backup")
        self.result = backup({"ledger": self.db_src}, self.dest,
                             stamp=STAMP, media_root=self.media_root)

    def test_verify_passes_with_intact_media(self):
        ok, why = verify_backup(self.dest)
        self.assertTrue(ok, why)
        self.assertIn("media", why)

    def test_verify_fails_when_media_file_removed(self):
        # Remove one media file after backup
        os.remove(os.path.join(self.dest, "media", "p0.jpg"))
        ok, why = verify_backup(self.dest)
        self.assertFalse(ok)
        self.assertIn("media", why)

    def test_verify_fails_when_media_count_changed(self):
        # Add a file after backup
        with open(os.path.join(self.dest, "media", "extra.jpg"), "wb") as fh:
            fh.write(b"extra")
        ok, why = verify_backup(self.dest)
        self.assertFalse(ok)
        self.assertIn("count", why)


class TestBackupRequiredDatabases(unittest.TestCase):
    """backup() fails when a required database is missing."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.db_src = os.path.join(self.dir, "ledger.sqlite")
        _make_db(self.db_src)
        self.dest = os.path.join(self.dir, "backup")

    def test_required_missing_fails(self):
        result = backup({"ledger": self.db_src, "memory": "/nonexistent/m.sqlite"},
                        self.dest, stamp=STAMP,
                        required=("ledger", "memory"))
        self.assertFalse(result.ok)
        self.assertIn("memory", result.detail)

    def test_optional_missing_is_skipped(self):
        result = backup({"ledger": self.db_src, "memory": "/nonexistent/m.sqlite"},
                        self.dest, stamp=STAMP,
                        required=("ledger",))
        self.assertTrue(result.ok)
        names = [e.name for e in result.entries]
        self.assertIn("ledger", names)
        self.assertNotIn("memory", names)


class TestRestoreMediaSandbox(unittest.TestCase):
    """restore_media restores the tree from a verified backup."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.db_src = os.path.join(self.dir, "ledger.sqlite")
        _make_db(self.db_src)
        self.media_root = os.path.join(self.dir, "photos")
        _make_media(self.media_root)
        self.dest = os.path.join(self.dir, "backup")
        backup({"ledger": self.db_src}, self.dest,
               stamp=STAMP, media_root=self.media_root)

    def test_restore_copies_tree(self):
        target = os.path.join(self.dir, "restored")
        ok, why = restore_media(self.dest, target)
        self.assertTrue(ok, why)
        self.assertTrue(os.path.exists(os.path.join(target, "p0.jpg")))
        self.assertTrue(os.path.exists(os.path.join(target, "sub", "q.jpg")))

    def test_restore_refuses_unverified(self):
        # Corrupt the backup manifest by removing a DB file
        os.remove(os.path.join(self.dest, f"ledger-{STAMP}.sqlite"))
        target = os.path.join(self.dir, "restored2")
        ok, why = restore_media(self.dest, target)
        self.assertFalse(ok)
        self.assertIn("refusing", why)


class TestMemoryInBackupScope(unittest.TestCase):
    """backup_job must include memory.sqlite (Ari approved 2026-08-10)."""

    def test_backup_job_adds_memory(self):
        src = open(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ofn", "backup_job.py"), encoding="utf-8").read()
        self.assertIn('db_paths["memory"] = cfg.memory_path', src)
        self.assertIn("required", src)


if __name__ == "__main__":
    unittest.main()
