"""The golden vector: base64 this project did not produce.

Three times in one night the same pattern appeared —

    auth tests    signed the blob with the same function whose verification
                  they were checking
    the matrix    proved a decode/exclude combination using a blob we had
                  chosen the field set of
    photos.py     shaped its test input to what the code understood, so a
                  `data:` header it could not parse at all was never seen

    anything that generates its own test input is validating itself.

The cure is one real output from the real producer, captured once and stored.
`canvas.toDataURL()` is what the shell actually sends, and its exact shape —
the header, the quality, the padding, the length — is not ours to choose.

Until the fixture exists these tests skip with a message rather than pass.
A skipped test is unfinished work; a passing test built on invented input is
a claim.
"""

from __future__ import annotations

import base64
import os
import unittest

from ofn.kernel.photos import ALLOWED_EDGES, MAX_DECODED_BYTES, inspect

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

WANTED = "\n".join((
    "no golden vector yet — see tests/fixtures/README.md.",
    "Needed: one real `canvas.toDataURL()` output per edge, taken from a",
    "portrait photo shot on a real phone. A synthetic file has no EXIF, so",
    "rotation passes in tests and comes out sideways on the phone.",
))


def load(edge: int) -> str | None:
    path = os.path.join(HERE, f"canvas-{edge}.txt")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip()


class TestAgainstRealCanvasOutput(unittest.TestCase):
    def vector(self, edge: int) -> str:
        text = load(edge)
        if text is None:
            self.skipTest(WANTED)
        return text

    def test_the_real_header_is_understood(self):
        """The failure this exists for: the implementation had no data-URL
        path at all, and every test passed because every test fed it a bare
        string."""
        for edge in ALLOWED_EDGES:
            with self.subTest(edge=edge):
                text = self.vector(edge)
                self.assertTrue(text.startswith("data:image/"))
                payload = inspect(text)
                self.assertIn(payload.media_type, ("image/jpeg", "image/png"))

    def test_the_real_payload_decodes(self):
        for edge in ALLOWED_EDGES:
            with self.subTest(edge=edge):
                payload = inspect(self.vector(edge))
                raw = base64.b64decode(payload.body, validate=True)
                self.assertGreater(len(raw), 0)

    def test_the_bound_holds_against_real_bytes(self):
        """The estimate must never be under the truth — that is the direction
        that lets an oversized image through."""
        for edge in ALLOWED_EDGES:
            with self.subTest(edge=edge):
                payload = inspect(self.vector(edge))
                raw = base64.b64decode(payload.body, validate=True)
                self.assertGreaterEqual(payload.max_decoded_bytes, len(raw))

    def test_a_real_photo_fits_under_the_cap(self):
        """If a normal phone photo does not, the cap is wrong — and today it
        is a number from a document, measured against nothing."""
        for edge in ALLOWED_EDGES:
            with self.subTest(edge=edge):
                payload = inspect(self.vector(edge))
                self.assertLessEqual(payload.max_decoded_bytes,
                                     MAX_DECODED_BYTES)

    def test_it_is_a_jpeg_where_we_expect_one(self):
        """`toDataURL('image/jpeg')` falls back to png silently when the
        argument is wrong. Worth knowing which one actually arrives."""
        for edge in ALLOWED_EDGES:
            with self.subTest(edge=edge):
                payload = inspect(self.vector(edge))
                raw = base64.b64decode(payload.body, validate=True)
                if payload.media_type == "image/jpeg":
                    self.assertEqual(raw[:2], b"\xff\xd8")
                else:
                    self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")


class TestTheFixtureSlotIsDocumented(unittest.TestCase):
    """This one does not skip. The reminder has to be visible even while the
    vectors are missing, or "we will capture it later" becomes never."""

    def test_the_readme_says_what_to_capture(self):
        readme = os.path.join(HERE, "README.md")
        self.assertTrue(os.path.isfile(readme))
        with open(readme, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("toDataURL", text)
        self.assertIn("EXIF", text)


if __name__ == "__main__":
    unittest.main()
