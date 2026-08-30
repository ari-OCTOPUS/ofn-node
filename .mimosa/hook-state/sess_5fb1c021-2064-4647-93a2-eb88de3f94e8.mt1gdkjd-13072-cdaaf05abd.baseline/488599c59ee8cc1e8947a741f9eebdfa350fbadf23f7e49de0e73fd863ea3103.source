"""A photo the library can say something about.

The media row held what a file is — mime, bytes, whether the original was
kept — and nothing about what it *is*. The closed vocabulary answers "which
side of which axis"; it cannot answer "the light came through the blind and I
want the next one like that", and it cannot say which of forty shots she would
keep. A library with no room for a sentence is an inventory.

Three columns, and one of them is really two: `taken_at` never travels without
`taken_source`, because a date with no provenance gets trusted for more than
it is worth. That is §8-ب as a schema — the claim and an independent record of
where the claim came from, so the day EXIF parsing lands the two can be
compared instead of one quietly overwriting the other.
"""

from __future__ import annotations

import sqlite3
import unittest

from ofn.adapters.sqlite_base import apply_schema, missing_columns
from ofn.adapters.studio_store import (
    EARLIEST_PLAUSIBLE_EPOCH_S, MAX_NOTE, MAX_RATING, MIGRATIONS, SCHEMA,
    StudioError, StudioStore,
)
from tests.tmpdir import temp_dir

NOW = 1_785_000_000


class Store(unittest.TestCase):
    def setUp(self):
        self.s = StudioStore(":memory:")
        self.addCleanup(self.s.close)

    def shot(self, **kw):
        mid = self.s.next_media_id("studio")
        self.s.add_media("studio", mid, mime="image/jpeg", byte_size=1000,
                         has_original=True, now_epoch_s=NOW, **kw)
        return mid


class TestTheOldShapeComesForward(unittest.TestCase):
    """`CREATE TABLE IF NOT EXISTS` never revisits a table it finds, so the
    columns only reach an existing file through a migration. Pre-flight grades
    residual drift CRITICAL and drops the node into SAFE MODE, which is the
    correct posture and a terrible surprise."""

    def _old_file(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("""
            CREATE TABLE media_items (
                media_id      TEXT PRIMARY KEY,
                tenant_id     TEXT NOT NULL,
                collection_id TEXT,
                mime          TEXT NOT NULL DEFAULT 'image/jpeg',
                byte_size     INTEGER NOT NULL DEFAULT 0,
                has_original  INTEGER NOT NULL DEFAULT 0,
                added_at      INTEGER NOT NULL,
                archived_at   INTEGER)""")
        conn.execute("INSERT INTO media_items (media_id, tenant_id, added_at) "
                     "VALUES ('shot-0001', 'studio', ?)", (NOW,))
        conn.commit()
        return conn

    def test_the_migration_adds_the_columns_and_keeps_the_rows(self):
        conn = self._old_file()
        apply_schema(conn, SCHEMA, MIGRATIONS)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(media_items)")}
        self.assertLessEqual({"note", "rating", "taken_at", "taken_source",
                              "category"}, cols)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM media_items").fetchone()[0], 1)

    def test_no_drift_is_left_for_pre_flight_to_find(self):
        conn = self._old_file()
        apply_schema(conn, SCHEMA, MIGRATIONS)
        self.assertEqual(missing_columns(conn, SCHEMA), {})

    def test_a_migrated_row_reads_as_unrated_and_undated(self):
        """Not as rated zero-out-of-five, and not as taken at the epoch. The
        defaults have to mean "nobody has said", because every existing photo
        is about to have them."""
        conn = self._old_file()
        apply_schema(conn, SCHEMA, MIGRATIONS)
        row = conn.execute("SELECT rating, taken_at, taken_source, note, "
                           "category FROM media_items").fetchone()
        self.assertEqual(row[0], 0)
        self.assertIsNone(row[1])
        self.assertIsNone(row[2])
        self.assertIsNone(row[3])
        self.assertEqual(row[4], "")


class TestHerWordsAndHerMark(Store):
    def test_a_note_and_a_rating_are_kept(self):
        mid = self.shot()
        self.s.describe_media("studio", mid, note="نور از پنجره", rating=4)
        got = self.s.media_in("studio", mid)
        self.assertEqual(got["note"], "نور از پنجره")
        self.assertEqual(got["rating"], 4)

    def test_a_category_is_kept_with_the_photo(self):
        mid = self.shot()
        self.s.describe_media("studio", mid, category="هنری")
        got = self.s.media_in("studio", mid)
        self.assertEqual(got["category"], "هنری")

    def test_gallery_carries_the_category(self):
        mid = self.shot()
        self.s.describe_media("studio", mid, category="سکسی")
        item = next(m for m in self.s.gallery("studio")
                    if m["media_id"] == mid)
        self.assertEqual(item["category"], "سکسی")

    def test_omitting_one_does_not_erase_the_other(self):
        """The reason `None` and "clear it" have to be different values. A
        screen that saves a rating must not wipe a note it never showed."""
        mid = self.shot()
        self.s.describe_media("studio", mid, note="نور از پنجره", rating=4)
        self.s.describe_media("studio", mid, rating=5)
        got = self.s.media_in("studio", mid)
        self.assertEqual(got["note"], "نور از پنجره")
        self.assertEqual(got["rating"], 5)

    def test_clearing_is_possible_and_explicit(self):
        mid = self.shot()
        self.s.describe_media("studio", mid, note="اشتباه", rating=3)
        self.s.describe_media("studio", mid, note="", rating=0)
        got = self.s.media_in("studio", mid)
        self.assertEqual(got["note"], "")
        self.assertEqual(got["rating"], 0)

    def test_a_rating_outside_the_range_is_refused(self):
        """Enforced in code, not only in the schema: SQLite cannot attach a
        CHECK to a column added by ALTER TABLE, so a migrated file has no
        constraint at all and this is the only thing standing there."""
        mid = self.shot()
        for bad in (-1, MAX_RATING + 1, 99):
            with self.subTest(rating=bad), self.assertRaises(StudioError):
                self.s.describe_media("studio", mid, rating=bad)

    def test_a_rating_that_is_not_a_number_is_refused(self):
        mid = self.shot()
        for bad in ("۴", "4", True, 3.5):
            with self.subTest(rating=bad), self.assertRaises(StudioError):
                self.s.describe_media("studio", mid, rating=bad)

    def test_an_overlong_note_is_refused_rather_than_truncated(self):
        """Silently cutting her sentence in half stores something she did not
        write and shows it back to her as if she had."""
        mid = self.shot()
        with self.assertRaises(StudioError):
            self.s.describe_media("studio", mid, note="ا" * (MAX_NOTE + 1))

    def test_another_tenant_cannot_describe_this_photo(self):
        """The leak that had to be closed once already for album ids: an id
        is not authorisation."""
        mid = self.shot()
        with self.assertRaises(StudioError):
            self.s.describe_media("ziman", mid, note="نه")
        self.assertIsNone(self.s.media_in("ziman", mid))


class TestWhenItWasTaken(Store):
    def test_the_capture_time_is_stored_with_its_source(self):
        taken = NOW - 86_400
        mid = self.shot(taken_at=taken, taken_source="file")
        got = self.s.media_in("studio", mid)
        self.assertEqual(got["taken_at"], taken)
        self.assertEqual(got["taken_source"], "file")

    def test_a_source_nobody_defined_is_not_recorded(self):
        """The column exists to say what the number is worth. An arbitrary
        string in it defeats the only thing it is for."""
        mid = self.shot(taken_at=NOW - 10, taken_source="vibes")
        self.assertEqual(self.s.media_in("studio", mid)["taken_source"], "")

    def test_an_unknown_capture_time_is_null_and_not_zero(self):
        mid = self.shot()
        got = self.s.media_in("studio", mid)
        self.assertIsNone(got["taken_at"])
        self.assertEqual(got["taken_source"], "")

    def test_the_gallery_orders_by_capture_time_when_it_is_known(self):
        """Fifty photos uploaded in one sitting share a single `added_at`, so
        ordering by that hands a shoot back in whatever order the picker
        iterated — which is not an order."""
        old = self.shot(taken_at=NOW - 90_000, taken_source="file")
        new = self.shot(taken_at=NOW - 100, taken_source="file")
        order = [m["media_id"] for m in self.s.gallery("studio")]
        self.assertLess(order.index(new), order.index(old))

    def test_a_photo_with_no_capture_time_falls_back_to_arrival(self):
        """It must still appear, and in a defensible place — not sorted to the
        bottom for ever because one field is empty."""
        mid = self.shot()
        self.assertIn(mid, [m["media_id"] for m in self.s.gallery("studio")])

    def test_the_gallery_carries_the_new_fields(self):
        mid = self.shot(taken_at=NOW - 5, taken_source="file")
        self.s.describe_media("studio", mid, note="این", rating=5)
        item = next(m for m in self.s.gallery("studio")
                    if m["media_id"] == mid)
        self.assertEqual(item["note"], "این")
        self.assertEqual(item["rating"], 5)
        self.assertEqual(item["taken_source"], "file")


class TestTheNodeClampsAClockItDoesNotOwn(unittest.TestCase):
    """`taken_at` is a number from somebody else's phone. A photo dated in
    2087 sorts above everything she owns, for ever, and there is no repair
    that would be honest — so out of range means unknown."""

    def test_the_floor_is_not_the_boards_own_clock_floor(self):
        """`boot.MIN_PLAUSIBLE_EPOCH` asks whether THIS board has heard from
        NTP. A photo from last year is not a broken clock."""
        from ofn.adapters.boot import MIN_PLAUSIBLE_EPOCH
        self.assertLess(EARLIEST_PLAUSIBLE_EPOCH_S, MIN_PLAUSIBLE_EPOCH)

    def _node(self):
        import os
        import tempfile

        from ofn.adapters.facts import FactStore
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.media import MediaStore
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.packloader import load_pack
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        d = temp_dir(self)
        pack = load_pack("packs/studio.yaml")
        registry = TenantRegistry({pack.tenant.value: pack})
        stores = [Ledger(os.path.join(d, "l.sqlite")),
                  StudioStore(os.path.join(d, "s.sqlite")),
                  Outbox(os.path.join(d, "o.sqlite"))]
        for store in stores:
            self.addCleanup(store.close)
        ledger, studio, outbox = stores
        node = Node(registry=registry, quota=None, ledger=ledger,
                    facts=FactStore(os.path.join(d, "f.sqlite")),
                    outbox=outbox, now_epoch_s=lambda: NOW,
                    now_iso=lambda: "2026-08-05T00:00:00Z",
                    studio=studio, media=MediaStore(os.path.join(d, "m")))
        return node, studio, registry.scope(pack.tenant.value)

    def _put(self, node, **kw):
        from tests.fixtures.renditions import RENDITIONS
        return node.add_to_library(self._scope, "u1",
                                   {"renditions": RENDITIONS, **kw})

    def setUp(self):
        self._node_obj, self._studio, self._scope = self._node()

    def _stored(self, **kw):
        out = self._put(self._node_obj, **kw)
        self.assertTrue(out.get("ok"), out)
        return self._studio.media_in("studio", out["media_id"])

    def test_a_future_date_is_dropped_rather_than_stored(self):
        got = self._stored(taken_at=NOW + 2_000_000_000,
                           taken_source="file")
        self.assertIsNone(got["taken_at"])
        self.assertEqual(got["taken_source"], "")

    def test_a_date_before_digital_cameras_is_dropped(self):
        got = self._stored(taken_at=EARLIEST_PLAUSIBLE_EPOCH_S - 1,
                           taken_source="file")
        self.assertIsNone(got["taken_at"])

    def test_a_plausible_date_survives_with_its_source(self):
        got = self._stored(taken_at=NOW - 3600, taken_source="file")
        self.assertEqual(got["taken_at"], NOW - 3600)
        self.assertEqual(got["taken_source"], "file")

    def test_a_date_that_is_not_a_number_is_dropped(self):
        for bad in ("1785000000", None, True, 1.5):
            with self.subTest(taken_at=bad):
                got = self._stored(taken_at=bad, taken_source="file")
                self.assertIsNone(got["taken_at"])


if __name__ == "__main__":
    unittest.main()
