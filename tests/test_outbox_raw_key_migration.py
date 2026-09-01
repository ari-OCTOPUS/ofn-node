"""T1/T2/T3 for the raw-key outbox migration.

Contract under test (issue #44, merged in PR #46):
    the stored idempotency key IS the raw key.
    ("lead", "k1"), ("lead", "lead:k1"), ("lead", "LEAD:k1")
    are three DISTINCT, equally valid rows.

Schema and helper style follow tests/test_outbox_negative_controls.py
(legacy DDL, Outbox(path) triggering migration on boot, ob._conn probing,
addCleanup for connection ownership).

Two cases in TestT2LosslessGuard are deliberate defect probes and are
expected to FAIL on main@a6dd2fcb. They are the permanent negative
controls for D1 and D2 and must go green with the migration patch, not
by weakening the assertions.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import unittest
from unittest import mock

from ofn.adapters import outbox as outbox_mod
from ofn.adapters.outbox import Outbox
from ofn.kernel.errors import FailClosedError

LEGACY_DDL = (
    "CREATE TABLE outbox (idem_key TEXT PRIMARY KEY, tenant TEXT,"
    " kind TEXT, payload TEXT, tier TEXT, status TEXT,"
    " attempts INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT,"
    " note TEXT DEFAULT '')"
)
COLS = ("idem_key, tenant, kind, payload, tier, status, attempts,"
        " created_at, updated_at, note")
TS = "2026-09-01T00:00:00Z"


def row(idem_key, tenant="lead", status="QUEUED"):
    return (idem_key, tenant, "quote", "{}", "T0", status, 0, TS, TS, "")


def make_legacy_db(path, rows):
    conn = sqlite3.connect(path)
    try:
        conn.execute(LEGACY_DDL)
        conn.executemany(
            f"INSERT INTO outbox ({COLS}) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
    finally:
        conn.close()


def pk_of(conn):
    return [r[1] for r in conn.execute("PRAGMA table_info(outbox)") if r[5] > 0]


def pairs_of(conn):
    return {(r[0], r[1])
            for r in conn.execute("SELECT tenant, idem_key FROM outbox")}


def tables_of(conn):
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


class RawKeyMigrationCase(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.addCleanup(self._d.cleanup)
        self.path = os.path.join(self._d.name, "legacy.sqlite")

    def probe(self, path=None):
        """Own the probing connection explicitly (Windows handle discipline)."""
        conn = sqlite3.connect(path or self.path)
        self.addCleanup(conn.close)
        return conn


# --------------------------------------------------------------------------
# T1 - case sensitivity / coexistence
# --------------------------------------------------------------------------
class TestT1RawKeyCoexistence(RawKeyMigrationCase):

    def test_three_spellings_coexist_byte_identical(self):
        make_legacy_db(self.path, [row("k1"), row("lead:k1"), row("LEAD:k1")])
        ob = Outbox(self.path)
        self.addCleanup(ob.close)

        self.assertEqual(pairs_of(ob._conn), {
            ("lead", "k1"),
            ("lead", "lead:k1"),
            ("lead", "LEAD:k1"),
        })

    def test_migration_moves_to_composite_pk(self):
        make_legacy_db(self.path, [row("k1")])
        ob = Outbox(self.path)
        self.addCleanup(ob.close)

        self.assertEqual(pk_of(ob._conn), ["tenant", "idem_key"])
        self.assertNotIn("outbox_legacy", tables_of(ob._conn))

    def test_key_not_matching_tenant_prefix_still_migrates(self):
        """The old LIKE tenant || ':%' filter silently dropped these rows."""
        make_legacy_db(self.path, [
            row("k1", tenant="lead"),
            row("paint:k9", tenant="lead"),      # foreign-looking prefix
            row("k2", tenant="paint"),
        ])
        ob = Outbox(self.path)
        self.addCleanup(ob.close)

        self.assertEqual(pairs_of(ob._conn), {
            ("lead", "k1"), ("lead", "paint:k9"), ("paint", "k2"),
        })

    def test_same_key_under_two_tenants_is_not_a_collision(self):
        make_legacy_db(self.path, [
            row("shared", tenant="lead"),
            row("lead:shared", tenant="paint"),
        ])
        ob = Outbox(self.path)
        self.addCleanup(ob.close)

        self.assertEqual(pairs_of(ob._conn),
                         {("lead", "shared"), ("paint", "lead:shared")})

    def test_payload_and_status_survive_unchanged(self):
        make_legacy_db(self.path, [
            ("lead:k1", "lead", "quote", '{"aud": 1234}', "T0",
             "SENT", 3, TS, TS, "note-text"),
        ])
        ob = Outbox(self.path)
        self.addCleanup(ob.close)

        got = ob._conn.execute(
            "SELECT payload, status, attempts, note FROM outbox").fetchone()
        self.assertEqual(tuple(got), ('{"aud": 1234}', "SENT", 3, "note-text"))


# --------------------------------------------------------------------------
# T2 - lossless guard
# --------------------------------------------------------------------------
class _FakeDigest:
    def __init__(self, value):
        self._value = value

    def hexdigest(self):
        return self._value


class TestT2LosslessGuard(RawKeyMigrationCase):

    ORIGINAL = [row("k1"), row("lead:k1"), row("LEAD:k1"),
                row("k2", tenant="paint")]

    def test_happy_path_count_and_fingerprint_match_then_legacy_dropped(self):
        make_legacy_db(self.path, self.ORIGINAL)
        ob = Outbox(self.path)
        self.addCleanup(ob.close)

        n = ob._conn.execute("SELECT count(*) FROM outbox").fetchone()[0]
        self.assertEqual(n, len(self.ORIGINAL))
        self.assertNotIn("outbox_legacy", tables_of(ob._conn))

    def test_fingerprint_mismatch_fails_closed_and_restores_legacy(self):
        make_legacy_db(self.path, self.ORIGINAL)
        digests = iter([_FakeDigest("a" * 64), _FakeDigest("b" * 64)])
        fake_hashlib = mock.Mock()
        fake_hashlib.sha256 = lambda _payload: next(digests)

        with mock.patch.object(outbox_mod, "hashlib", fake_hashlib):
            with self.assertRaisesRegex(
                    FailClosedError, "lossless-migration-check-failed"):
                Outbox(self.path)

        conn = self.probe()
        self.assertEqual(pk_of(conn), ["idem_key"], "legacy schema restored")
        self.assertNotIn("outbox_legacy", tables_of(conn))
        self.assertEqual(
            pairs_of(conn),
            {("lead", "k1"), ("lead", "lead:k1"),
             ("lead", "LEAD:k1"), ("paint", "k2")})

    def test_error_message_names_both_counts_and_both_hashes(self):
        make_legacy_db(self.path, self.ORIGINAL)
        digests = iter([_FakeDigest("a" * 64), _FakeDigest("b" * 64)])
        fake_hashlib = mock.Mock()
        fake_hashlib.sha256 = lambda _payload: next(digests)

        with mock.patch.object(outbox_mod, "hashlib", fake_hashlib):
            with self.assertRaises(FailClosedError) as ctx:
                Outbox(self.path)

        msg = str(ctx.exception)
        for token in ("before=", "after=", "fp_before=", "fp_after=",
                      "no DROP performed"):
            self.assertIn(token, msg)

    def test_mid_migration_exception_must_not_lose_rows(self):
        """DEFECT PROBE D1 - RED on main@a6dd2fcb, must go green with the patch.

        A legacy row with a NULL tenant violates the new NOT NULL column, so
        the INSERT loop raises before the lossless check is ever reached. The
        loop is not wrapped, so `outbox` has been renamed to `outbox_legacy`
        and a partially filled `outbox` remains: the next boot sees a
        composite PK, skips migration entirely, and the untransferred rows
        are gone silently. That is an I3 violation, not a crash.

        Required behaviour: fail closed with every original row recoverable.
        """
        make_legacy_db(self.path, [
            row("k1"), row("k2", tenant=None), row("k3"),
        ])
        with self.assertRaises(Exception):
            Outbox(self.path)

        conn = self.probe()
        recoverable = set()
        for table in ("outbox", "outbox_legacy"):
            if table in tables_of(conn):
                recoverable |= {
                    r[0] for r in conn.execute(f"SELECT idem_key FROM {table}")}
        self.assertEqual(recoverable, {"k1", "k2", "k3"},
                         "every legacy row must remain recoverable")

    def test_row_order_must_not_change_the_fingerprint(self):
        """DEFECT PROBE D2 - the canonical form must sort rows, not just keys.

        json.dumps(..., sort_keys=True) normalises keys inside each row but
        leaves the row list in scan order. If SQLite returns the rebuilt
        table in a different order than the legacy scan, boot fails on a
        healthy database.
        """
        make_legacy_db(self.path, [row("zz"), row("aa"), row("mm")])
        ob = Outbox(self.path)
        self.addCleanup(ob.close)
        self.assertEqual(
            pairs_of(ob._conn),
            {("lead", "zz"), ("lead", "aa"), ("lead", "mm")})


# --------------------------------------------------------------------------
# T3 - Windows replay isolation
# --------------------------------------------------------------------------
class TestT3ReplayIsolation(RawKeyMigrationCase):

    def test_replay_uses_a_copy_in_its_own_temp_dir(self):
        make_legacy_db(self.path, [row("k1"), row("lead:k1")])

        replay_dir = tempfile.mkdtemp(prefix="outbox-replay-")
        self.addCleanup(shutil.rmtree, replay_dir, True)
        replay_path = os.path.join(replay_dir, "replay.sqlite")
        shutil.copy2(self.path, replay_path)

        ob = Outbox(replay_path)
        try:
            self.assertEqual(pk_of(ob._conn), ["tenant", "idem_key"])
        finally:
            ob.close()

        # Windows raises PermissionError here if any handle is still open.
        os.remove(replay_path)
        self.assertFalse(os.path.exists(replay_path))

        original = self.probe()
        self.assertEqual(pk_of(original), ["idem_key"],
                         "replay must not touch the original file")

    def test_failed_boot_releases_the_file_handle(self):
        make_legacy_db(self.path, [row("k1")])
        digests = iter([_FakeDigest("a" * 64), _FakeDigest("b" * 64)])
        fake_hashlib = mock.Mock()
        fake_hashlib.sha256 = lambda _payload: next(digests)

        with mock.patch.object(outbox_mod, "hashlib", fake_hashlib):
            with self.assertRaises(FailClosedError):
                Outbox(self.path)

        moved = self.path + ".moved"
        os.replace(self.path, moved)     # fails on Windows if handle leaked
        self.addCleanup(os.remove, moved)
        self.assertTrue(os.path.exists(moved))

    def test_two_sequential_boots_each_own_their_connection(self):
        make_legacy_db(self.path, [row("k1")])

        first = Outbox(self.path)
        first_pk = pk_of(first._conn)
        first.close()

        second = Outbox(self.path)
        try:
            self.assertEqual(pk_of(second._conn), first_pk)
            self.assertEqual(pairs_of(second._conn), {("lead", "k1")})
        finally:
            second.close()


if __name__ == "__main__":
    unittest.main()
