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
    ALLOWED_EDGES, MAX_DECODED_BYTES, inspect, original_path, piece_prefix,
    relative_path,
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
    def test_both_renditions_and_the_original_land(self):
        for edge in ALLOWED_EDGES:
            self.assertTrue(self.m.exists(self.put(edge=edge)))
        rel = self.m.write_original("studio", "d1", 0, PAY)
        self.assertTrue(self.m.exists(rel))

    def test_the_bytes_come_back_unchanged(self):
        rel = self.put()
        self.assertEqual(self.m.read(rel), base64.b64decode(PNG))

    def test_the_archive_copy_keeps_the_type_it_arrived_as(self):
        """The renditions are always jpeg — a canvas made them. This one is
        whatever the phone sent, because "what actually went out" has to stay
        answerable."""
        png = inspect("data:image/png;base64," + PNG)
        self.assertTrue(self.m.write_original("studio", "d1", 0, png)
                        .endswith("0-original.png"))

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
        self.m.write_original("studio", "d1", 0, PAY)
        self.assertEqual(self.m.remove_piece("studio", "d1"), 3)

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
