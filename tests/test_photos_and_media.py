"""ST-2 — storing an image, and the two things that must not go wrong.

The brief said `kernel/photos.py` already existed and should be used rather
than rewritten. It did not exist — it had been written in another workspace,
tested there, and never moved to this board. So it was written here from the
properties the brief named.

Then the original arrived, as tests. It targets a different API and a better
one: it understands the `data:` URL a canvas actually produces, and it carries
`position`, which is the column `draft_media` needs. This module converged on
it. `test_photos_external.py` is that file, unchanged, and it is the contract.

What remains here is the part it does not cover: bytes actually reaching
disk, tenant isolation on a real filesystem, cascade delete, and the backup.
"""

from __future__ import annotations

import base64
import os
import tempfile
import unittest

from ofn.adapters.media import MediaStore
from ofn.kernel.errors import FailClosedError
from ofn.kernel.photos import (
    ALLOWED_EDGES, MAX_DECODED_BYTES, inspect, piece_prefix, relative_path,
)

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * 64).decode()
PAY = inspect(PNG)


class Disk(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.m = MediaStore(os.path.join(self.dir, "media"))

    def put(self, tenant="studio", piece="d1", position=0, edge=1600,
            payload=None):
        return self.m.write_rendition(tenant, piece, position, edge,
                                      payload or PAY)


class TestWriting(Disk):
    def test_both_renditions_land(self):
        for edge in ALLOWED_EDGES:
            self.assertTrue(self.m.exists(self.put(edge=edge)))

    def test_the_original_is_kept(self):
        """This was once asserted the other way round, and both versions were
        right about the question they were asked.

        Archiving an original proves nothing about what was *published* — a
        1600px rendition is what goes to a platform, and `media_sent` hashes
        what actually left. That is unchanged.

        It is kept because the leg turned out to have a second job: this is
        her archive, and for that job a 1600px copy is not her work, it is a
        copy of her work.
        """
        rel = self.m.write_original("studio", "d1", 0, PAY)
        self.assertTrue(self.m.exists(rel))
        self.assertTrue(rel.endswith("0-original.jpg"))

    def test_the_original_keeps_the_type_it_arrived_as(self):
        png = inspect("data:image/png;base64," + PNG)
        self.assertTrue(self.m.write_original("studio", "d1", 0, png)
                        .endswith("0-original.png"))

    def test_evidence_and_archive_stay_separate(self):
        """`media_sent` still hashes what went out. The original is the work;
        the hash is the proof. Neither substitutes for the other."""
        from ofn.adapters import studio_store
        self.assertIn("media_sent", "".join(studio_store.SCHEMA))
        self.assertIn("sha256", "".join(studio_store.SCHEMA))

    def test_the_original_is_owner_only_too(self):
        rel = self.m.write_original("studio", "d1", 0, PAY)
        self.assertEqual(
            os.stat(self.m.absolute(rel)).st_mode & 0o777, 0o600)

    def test_the_bytes_come_back_unchanged(self):
        rel = self.put()
        self.assertEqual(self.m.read(rel), base64.b64decode(PNG))

    def test_corrupt_base64_is_refused_and_nothing_is_written(self):
        from ofn.kernel.photos import Payload
        bad = Payload(body="AAAA", media_type="image/jpeg",
                      max_decoded_bytes=0)
        with self.assertRaises(FailClosedError):
            self.m.write_rendition("studio", "d1", 0, 1600, bad)
        self.assertFalse(self.m.exists(relative_path("studio", "d1", 0, 1600)))

    def test_no_part_file_is_left_behind(self):
        """The write goes to a temporary name and is renamed, so a power cut
        leaves either nothing or a whole file. A half-written JPEG with a row
        pointing at it is worse than a missing one — it looks like data."""
        self.put()
        leftovers = [f for _, _, files in os.walk(self.m.root)
                     for f in files if f.endswith(".part")]
        self.assertEqual(leftovers, [])

    def test_writing_twice_replaces_rather_than_duplicates(self):
        self.put()
        rel = self.put()
        self.assertEqual(self.m.size_on_disk(rel), len(base64.b64decode(PNG)))


class TestZeroLeakBetweenBusinesses(Disk):
    """A separate class on purpose. For this leg the files are pictures of a
    person, so "did anything cross between businesses" is not a storage
    question."""

    def test_each_business_is_its_own_subtree(self):
        a = self.put(tenant="studio")
        b = self.put(tenant="ziman")
        self.assertTrue(a.startswith("studio/"))
        self.assertTrue(b.startswith("ziman/"))

    def test_identical_ids_in_two_businesses_do_not_collide(self):
        """Same piece id, same position, different business. Without the
        tenant in the path these are one file, and one partner is looking at
        another's photo."""
        other = inspect(base64.b64encode(b"different bytes!").decode())
        a = self.put(tenant="studio")
        b = self.put(tenant="ziman", payload=other)
        self.assertNotEqual(self.m.read(a), self.m.read(b))

    def test_deleting_one_business_does_not_touch_another(self):
        self.put(tenant="studio")
        keep = self.put(tenant="ziman")
        self.m.remove_piece("studio", "d1")
        self.assertTrue(self.m.exists(keep))

    def test_the_byte_count_is_per_business(self):
        self.put(tenant="studio")
        self.assertGreater(self.m.tenant_bytes("studio"), 0)
        self.assertEqual(self.m.tenant_bytes("lead"), 0)


class TestCascadeDelete(Disk):
    def test_every_rendition_of_a_piece_goes(self):
        for edge in ALLOWED_EDGES:
            self.put(edge=edge)
        self.assertEqual(self.m.remove_piece("studio", "d1"), 2)

    def test_a_sibling_piece_survives(self):
        self.put(piece="d1")
        keep = self.put(piece="d2")
        self.m.remove_piece("studio", "d1")
        self.assertTrue(self.m.exists(keep))

    def test_one_piece_prefix_does_not_swallow_another(self):
        """`piece-1` must not take `piece-10` with it. Deleting by string
        prefix is how that happens; this deletes the directory named by
        `piece_prefix`."""
        self.put(piece="piece-1")
        self.put(piece="piece-10")
        self.put(piece="piece-100")
        self.assertEqual(self.m.remove_piece("studio", "piece-1"), 1)
        left = sorted(f for _, _, fs in os.walk(self.m.root) for f in fs)
        self.assertEqual(len(left), 2)

    def test_deleting_nothing_is_not_an_error(self):
        self.assertEqual(self.m.remove_piece("studio", "never"), 0)

    def test_no_files_are_left_that_nothing_references(self):
        for edge in ALLOWED_EDGES:
            self.put(edge=edge)
        self.m.remove_piece("studio", "d1")
        remaining = [f for _, _, files in os.walk(self.m.root) for f in files]
        self.assertEqual(remaining, [])


class TestTheDecodedSizeIsCheckedAgain(Disk):
    def test_a_payload_that_decodes_larger_than_it_measured_is_refused(self):
        """The bound rounds up, so real bytes exceeding it means the text was
        not what was measured."""
        from ofn.kernel.photos import Payload
        lying = Payload(body=PNG, media_type="image/jpeg",
                        max_decoded_bytes=1)
        with self.assertRaises(FailClosedError):
            self.m.write_rendition("studio", "d1", 0, 1600, lying)


class TestTheBackupTakesTheFilesToo(Disk):
    """Photos live outside SQLite so a 40 MB image does not turn every read
    of a row into a 40 MB read. The cost of that choice is this: a backup of
    the databases alone restores rows pointing at files that are not there,
    and for this leg those files are the content."""

    def setUp(self):
        super().setUp()
        from ofn.adapters.backup import backup, mirror_media
        self.backup, self.mirror = backup, mirror_media
        self.dest = os.path.join(self.dir, "out")

    def test_media_is_copied_beside_the_databases(self):
        self.put()
        result = self.backup({}, self.dest, stamp="s1", media_root=self.m.root)
        self.assertEqual(result.media_files, 1)
        self.assertTrue(os.path.isfile(
            os.path.join(self.dest, "media", "studio", "d1", "0-1600.jpg")))

    def test_the_manifest_records_what_was_taken(self):
        """Enough to notice a tree that has silently stopped being copied."""
        import json
        self.put()
        self.backup({}, self.dest, stamp="s1", media_root=self.m.root)
        with open(os.path.join(self.dest, "manifest.json"), encoding="utf-8") as fh:
            manifest = json.load(fh)
        self.assertEqual(manifest["media"]["files"], 1)
        self.assertGreater(manifest["media"]["bytes"], 0)

    def test_a_half_written_file_is_not_backed_up(self):
        """A `.part` is an interrupted write, not content."""
        self.put()
        with open(os.path.join(self.m.root, "studio", "d1", "x.part"), "w") as fh:
            fh.write("half")
        self.assertEqual(self.mirror(self.m.root, self.dest)[0], 1)

    def test_every_business_subtree_is_included(self):
        self.put(tenant="studio")
        self.put(tenant="ziman")
        self.assertEqual(self.mirror(self.m.root, self.dest)[0], 2)

    def test_no_media_directory_is_not_a_failure(self):
        result = self.backup({}, self.dest, stamp="s1",
                             media_root=os.path.join(self.dir, "nothing"))
        self.assertTrue(result.ok)
        self.assertEqual(result.media_files, 0)

    def test_callers_that_pass_no_media_root_still_work(self):
        """The parameter is optional only so existing callers keep working."""
        result = self.backup({}, self.dest, stamp="s1")
        self.assertTrue(result.ok)
        self.assertEqual(result.media_files, 0)


if __name__ == "__main__":
    unittest.main()


class TestFilesAreNotWorldReadable(Disk):
    """The files are pictures of a person, on a disk that is not encrypted.
    This does not survive theft of the board — nothing here does — but it is
    one fewer account that can read them."""

    def test_the_media_root_is_owner_only(self):
        self.assertEqual(os.stat(self.m.root).st_mode & 0o777, 0o700)

    def test_a_stored_file_is_owner_only(self):
        rel = self.put()
        self.assertEqual(
            os.stat(self.m.absolute(rel)).st_mode & 0o777, 0o600)

    def test_the_directory_it_lands_in_is_owner_only(self):
        rel = self.put()
        folder = os.path.dirname(self.m.absolute(rel))
        self.assertEqual(os.stat(folder).st_mode & 0o777, 0o700)


class TestDeleteMeansDelete(Disk):
    """Without purging the backups, "delete" means "in fourteen days" — the
    nightly job keeps fourteen generations, so a photo she removed is still
    on the disk in fourteen places.

    For a control panel that is a reasonable trade. For somebody's archive of
    their own body it is the wrong default, and it is the kind of wrong that
    is only discovered by somebody who trusted the button.
    """

    def setUp(self):
        super().setUp()
        self.backups = os.path.join(self.dir, "backups")
        for gen in ("20260801-000000", "20260802-000000"):
            folder = os.path.join(self.backups, gen, "media", "studio", "d1")
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "0-1600.jpg"), "wb") as fh:
                fh.write(b"old copy")

    def test_every_generation_is_purged(self):
        self.assertEqual(
            self.m.purge_from_backups(self.backups, "studio", "d1"), 2)
        left = [f for _, _, fs in os.walk(self.backups) for f in fs]
        self.assertEqual(left, [])

    def test_another_piece_in_the_backups_survives(self):
        keep = os.path.join(self.backups, "20260801-000000", "media",
                            "studio", "d2")
        os.makedirs(keep, exist_ok=True)
        with open(os.path.join(keep, "0-1600.jpg"), "wb") as fh:
            fh.write(b"keep")
        self.m.purge_from_backups(self.backups, "studio", "d1")
        self.assertTrue(os.path.isfile(os.path.join(keep, "0-1600.jpg")))

    def test_one_prefix_does_not_take_another(self):
        """`d1` must not take `d10` out of the backups either."""
        other = os.path.join(self.backups, "20260801-000000", "media",
                             "studio", "d10")
        os.makedirs(other, exist_ok=True)
        with open(os.path.join(other, "0-1600.jpg"), "wb") as fh:
            fh.write(b"keep")
        self.m.purge_from_backups(self.backups, "studio", "d1")
        self.assertTrue(os.path.isfile(os.path.join(other, "0-1600.jpg")))

    def test_nothing_outside_the_backup_root_can_be_reached(self):
        """A recursive delete driven by an id gets a check even though the
        id is validated upstream."""
        with self.assertRaises(FailClosedError):
            self.m.purge_from_backups(self.backups, "studio", "../../etc")

    def test_no_backups_is_not_an_error(self):
        self.assertEqual(
            self.m.purge_from_backups(os.path.join(self.dir, "none"),
                                      "studio", "d1"), 0)

    def test_the_rest_of_the_backup_is_untouched(self):
        """Only the media mirror, only this subtree. Databases are not
        touched: losing a backup of the ledger to delete a photo would be a
        far worse trade."""
        db = os.path.join(self.backups, "20260801-000000", "ledger.sqlite")
        with open(db, "wb") as fh:
            fh.write(b"database")
        self.m.purge_from_backups(self.backups, "studio", "d1")
        self.assertTrue(os.path.isfile(db))
