"""ST-2 — storing an image, and the two things that must not go wrong.

The brief for this leg said `kernel/photos.py` already existed, was tested,
and should be used rather than rewritten. It did not exist. Neither did any
decode path, size cap, or write path — only a `product_photos` table and a
`photo_count()`, and zero photos had ever been stored. The description was a
specification that had been written down and then believed.

So this file tests a module written today against the properties that
description named:

    a size cap applied BEFORE decoding
    a path built from validated ids, never from a sender's filename
    tenant isolation
    cascade delete

The last two get their own class each, because for this leg the files are
pictures of a person: a leak between businesses and an orphaned file after a
delete are not storage bugs.
"""

from __future__ import annotations

import base64
import os
import tempfile
import unittest

from ofn.adapters.media import MediaStore
from ofn.kernel.errors import FailClosedError
from ofn.kernel.photos import (
    ALLOWED_MIME, MAX_UPLOAD_BYTES, Size, accept, all_paths, check_size,
    decoded_length, is_inside, relative_path,
)

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * 64).decode()


def up(tenant="studio", owner="d1", photo="p1", mime="image/jpeg",
       text=PNG):
    return accept(tenant, owner, photo, mime=mime, b64_text=text)


class TestTheCapIsAppliedBeforeDecoding(unittest.TestCase):
    """Decoding first and measuring afterwards puts the payload in memory on
    a 4 GB board that is also running three other businesses."""

    def test_an_oversized_payload_is_refused_from_its_length(self):
        huge = "A" * (MAX_UPLOAD_BYTES * 2)
        with self.assertRaises(FailClosedError):
            check_size(huge)

    def test_the_estimate_rounds_up_so_refusals_err_safe(self):
        for n in range(0, 40):
            self.assertGreaterEqual(decoded_length(n), len(base64.b64decode(
                base64.b64encode(b"x" * (n * 3 // 4)))))

    def test_an_empty_payload_is_refused(self):
        with self.assertRaises(FailClosedError):
            check_size("")

    def test_a_normal_photo_passes(self):
        self.assertGreater(check_size(PNG), 0)

    def test_the_cap_is_per_call_not_global(self):
        """This route has a 16 MB limit; the rest of the API has a much
        smaller body limit, and raising that one to fit a photo would raise
        it for every other endpoint."""
        with self.assertRaises(FailClosedError):
            check_size(PNG, max_bytes=8)


class TestThePathComesFromIdsNotFromTheSender(unittest.TestCase):
    def test_no_function_here_takes_a_filename(self):
        """The defence, stated as a test. A filename that arrives with an
        upload is attacker-controlled text; here it is not a parameter of
        anything."""
        import inspect

        from ofn.kernel import photos
        for name, fn in inspect.getmembers(photos, inspect.isfunction):
            params = set(inspect.signature(fn).parameters)
            for banned in ("filename", "file_name", "name", "original_name"):
                self.assertNotIn(banned, params, f"{name}() takes {banned}")

    def test_the_path_is_built_from_the_ids(self):
        self.assertEqual(relative_path(up(), Size.ORIGINAL),
                         "studio/d1/p1.jpg")
        self.assertEqual(relative_path(up(), Size.THUMB),
                         "studio/d1/p1.thumb.jpg")

    def test_a_traversal_id_is_refused_at_the_gate(self):
        for bad in ("../etc", "a/b", "..", "", "A" * 200, "p 1"):
            with self.assertRaises(FailClosedError):
                accept("studio", "d1", bad, mime="image/jpeg", b64_text=PNG)

    def test_a_traversal_tenant_is_refused(self):
        with self.assertRaises(FailClosedError):
            accept("../../root", "d1", "p1", mime="image/jpeg", b64_text=PNG)

    def test_only_known_image_types_are_accepted(self):
        for mime in ("text/html", "application/octet-stream", "image/svg+xml",
                     "", "image/jpeg; charset=utf-8"):
            with self.assertRaises(FailClosedError):
                accept("studio", "d1", "p1", mime=mime, b64_text=PNG)
        for mime in ALLOWED_MIME:
            self.assertTrue(accept("studio", "d1", "p1", mime=mime,
                                   b64_text=PNG))

    def test_derived_sizes_are_always_jpeg(self):
        """A PNG screenshot re-encoded at 1600px is several megabytes for no
        gain."""
        u = up(mime="image/png")
        self.assertTrue(relative_path(u, Size.ORIGINAL).endswith(".png"))
        self.assertTrue(relative_path(u, Size.DISPLAY).endswith(".jpg"))

    def test_is_inside_rejects_an_escape(self):
        self.assertTrue(is_inside("/media", "/media/studio/a.jpg"))
        self.assertFalse(is_inside("/media", "/mediaother/a.jpg"))
        self.assertFalse(is_inside("/media", "/media/../etc/passwd"))


class Disk(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.m = MediaStore(os.path.join(self.dir, "media"))


class TestWriting(Disk):
    def test_all_three_sizes_land(self):
        u = up()
        for size in Size:
            rel = self.m.write(u, size, PNG)
            self.assertTrue(self.m.exists(rel))
        self.assertEqual(len(all_paths(u)), 3)

    def test_the_bytes_come_back_unchanged(self):
        u = up()
        rel = self.m.write(u, Size.ORIGINAL, PNG)
        self.assertEqual(self.m.read(rel), base64.b64decode(PNG))

    def test_corrupt_base64_is_refused_and_nothing_is_written(self):
        u = up()
        with self.assertRaises(FailClosedError):
            self.m.write(u, Size.ORIGINAL, "not!base64!!")
        self.assertFalse(self.m.exists(relative_path(u, Size.ORIGINAL)))

    def test_no_part_file_is_left_behind(self):
        """The write goes to a temporary name and is renamed, so a power cut
        leaves either nothing or a whole file. A half-written JPEG with a
        database row pointing at it is worse than a missing one — it looks
        like data."""
        u = up()
        self.m.write(u, Size.ORIGINAL, PNG)
        leftovers = [f for _, _, files in os.walk(self.m.root)
                     for f in files if f.endswith(".part")]
        self.assertEqual(leftovers, [])

    def test_writing_twice_replaces_rather_than_duplicates(self):
        u = up()
        self.m.write(u, Size.ORIGINAL, PNG)
        rel = self.m.write(u, Size.ORIGINAL, PNG)
        self.assertEqual(self.m.size_on_disk(rel), len(base64.b64decode(PNG)))


class TestZeroLeakBetweenBusinesses(Disk):
    """A separate class on purpose. For this leg the files are pictures of a
    person, so "did anything cross between businesses" is not a storage
    question."""

    def test_each_business_is_its_own_subtree(self):
        a = self.m.write(up(tenant="studio"), Size.ORIGINAL, PNG)
        b = self.m.write(up(tenant="ziman"), Size.ORIGINAL, PNG)
        self.assertTrue(a.startswith("studio/"))
        self.assertTrue(b.startswith("ziman/"))
        self.assertNotEqual(self.m.absolute(a), self.m.absolute(b))

    def test_identical_ids_in_two_businesses_do_not_collide(self):
        """Same draft id, same photo id, different business. If the tenant
        were not in the path these would be the same file, and one partner
        would be looking at another's photo."""
        a = self.m.write(up(tenant="studio", owner="d1", photo="p1"),
                         Size.ORIGINAL, PNG)
        b = self.m.write(up(tenant="ziman", owner="d1", photo="p1"),
                         Size.ORIGINAL, base64.b64encode(b"different").decode())
        self.assertNotEqual(self.m.read(a), self.m.read(b))

    def test_deleting_one_business_does_not_touch_another(self):
        self.m.write(up(tenant="studio"), Size.ORIGINAL, PNG)
        keep = self.m.write(up(tenant="ziman"), Size.ORIGINAL, PNG)
        self.m.remove_owner("studio", "d1")
        self.assertTrue(self.m.exists(keep))

    def test_the_byte_count_is_per_business(self):
        self.m.write(up(tenant="studio"), Size.ORIGINAL, PNG)
        self.assertGreater(self.m.tenant_bytes("studio"), 0)
        self.assertEqual(self.m.tenant_bytes("lead"), 0)


class TestCascadeDelete(Disk):
    def test_every_rendition_of_a_draft_goes(self):
        u = up()
        for size in Size:
            self.m.write(u, size, PNG)
        self.assertEqual(self.m.remove_owner("studio", "d1"), 3)
        for size in Size:
            self.assertFalse(self.m.exists(relative_path(u, size)))

    def test_a_sibling_draft_survives(self):
        self.m.write(up(owner="d1"), Size.ORIGINAL, PNG)
        keep = self.m.write(up(owner="d2"), Size.ORIGINAL, PNG)
        self.m.remove_owner("studio", "d1")
        self.assertTrue(self.m.exists(keep))

    def test_deleting_nothing_is_not_an_error(self):
        self.assertEqual(self.m.remove_owner("studio", "never"), 0)

    def test_no_files_are_left_that_nothing_references(self):
        """The cascade half of a cascade delete. A row removed without this
        leaves files nothing points at and nothing will ever clean up — and
        here those files are pictures of a person."""
        u = up()
        for size in Size:
            self.m.write(u, size, PNG)
        self.m.remove_owner("studio", "d1")
        remaining = [f for _, _, files in os.walk(self.m.root) for f in files]
        self.assertEqual(remaining, [])


if __name__ == "__main__":
    unittest.main()


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
        self.m.write(up(), Size.ORIGINAL, PNG)
        result = self.backup({}, self.dest, stamp="s1", media_root=self.m.root)
        self.assertEqual(result.media_files, 1)
        self.assertTrue(os.path.isfile(
            os.path.join(self.dest, "media", "studio", "d1", "p1.jpg")))

    def test_the_manifest_records_what_was_taken(self):
        """Enough to notice a tree that has silently stopped being copied."""
        import json
        self.m.write(up(), Size.ORIGINAL, PNG)
        self.backup({}, self.dest, stamp="s1", media_root=self.m.root)
        with open(os.path.join(self.dest, "manifest.json"), encoding="utf-8") as fh:
            manifest = json.load(fh)
        self.assertEqual(manifest["media"]["files"], 1)
        self.assertGreater(manifest["media"]["bytes"], 0)

    def test_a_half_written_file_is_not_backed_up(self):
        """A `.part` is an interrupted write, not content."""
        self.m.write(up(), Size.ORIGINAL, PNG)
        with open(os.path.join(self.m.root, "studio", "d1", "x.part"), "w") as fh:
            fh.write("half")
        self.assertEqual(self.mirror(self.m.root, self.dest)[0], 1)

    def test_every_business_subtree_is_included(self):
        self.m.write(up(tenant="studio"), Size.ORIGINAL, PNG)
        self.m.write(up(tenant="ziman"), Size.ORIGINAL, PNG)
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


class TestTheThreeCasesTheBriefFlagged(Disk):
    """`test_photos.py` (40 tests, written independently) never reached this
    board. The three cases it was said to contain did arrive, in prose, so
    they are pinned here against this implementation rather than taken on
    trust — the same reason the module itself had to be written twice.
    """

    def test_svg_is_refused(self):
        """An SVG is a script container. Serving one from our own origin is
        stored XSS wearing a picture's clothes."""
        with self.assertRaises(FailClosedError):
            accept("studio", "d1", "p1", mime="image/svg+xml", b64_text=PNG)
        from ofn.kernel.photos import ALLOWED_MIME as allowed
        self.assertNotIn("image/svg+xml", allowed)

    def test_one_owner_prefix_does_not_swallow_another(self):
        """`piece-1` must not take `piece-10` with it. Deleting by string
        prefix is how that happens; this deletes a directory, and `piece-1`
        and `piece-10` are two directories."""
        self.m.write(up(owner="piece-1", photo="a"), Size.ORIGINAL, PNG)
        self.m.write(up(owner="piece-10", photo="b"), Size.ORIGINAL, PNG)
        self.m.write(up(owner="piece-100", photo="c"), Size.ORIGINAL, PNG)
        self.assertEqual(self.m.remove_owner("studio", "piece-1"), 1)
        left = sorted(f for _, _, fs in os.walk(self.m.root) for f in fs)
        self.assertEqual(left, ["b.jpg", "c.jpg"])

    def test_a_bool_is_not_an_id(self):
        """`True == 1` in Python, so a bool sails through an integer check
        and becomes position 1. There is no `position` field in this module
        yet — `draft_media` is not built — so this pins the gate that does
        exist: a bool is not a valid id either, and `_ID.match` would raise
        TypeError rather than refuse if it were handed one.
        """
        for bad in (True, False, 1, None):
            with self.assertRaises((FailClosedError, TypeError)):
                accept("studio", "d1", bad, mime="image/jpeg", b64_text=PNG)
