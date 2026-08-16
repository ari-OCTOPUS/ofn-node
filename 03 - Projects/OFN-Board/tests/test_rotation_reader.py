"""The dimension reader used to check EXIF rotation on the first real photo.

It has to be right before it is trusted, because what it reports decides
whether a golden vector gets captured — and a golden vector taken from a
sideways photo pins the bug in place for ever.

Its own first self-check failed, and the fault was the hand-built JPEG, not
the reader: a DQT segment declared 67 bytes and supplied six, so the scan
walked past the frame header. Which is the night's pattern once more, in
miniature — input I generated myself, disagreeing with code that was fine.
Hence these, with the lengths computed rather than typed.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

from check_rotation import dimensions          # noqa: E402


def jpeg(width: int, height: int, *, marker: int = 0xC0) -> bytes:
    """A minimal JPEG carrying nothing but a frame header."""
    app0 = bytes.fromhex("ffe00010") + b"JFIF\x00" + \
        bytes.fromhex("010100000100010000")
    sof = bytes([0xFF, marker]) + bytes.fromhex("000b08") + \
        height.to_bytes(2, "big") + width.to_bytes(2, "big") + \
        bytes.fromhex("01011100")
    return bytes.fromhex("ffd8") + app0 + sof + bytes.fromhex("ffd9")


# `write` is a module-level helper with no test case to hand ownership to, and
# it is called once per assertion — so a `mkdtemp` per call leaked a directory
# per assertion. One directory for the module, torn down with it, and a unique
# name per file inside it.
_TMP: tempfile.TemporaryDirectory | None = None


def setUpModule() -> None:
    global _TMP
    _TMP = tempfile.TemporaryDirectory()


def tearDownModule() -> None:
    if _TMP is not None:
        _TMP.cleanup()


def write(data: bytes) -> str:
    fd, path = tempfile.mkstemp(suffix=".jpg", dir=_TMP.name)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    return path


class TestDimensions(unittest.TestCase):
    def test_portrait_and_landscape_are_not_confused(self):
        """Height and width are stored in that order, and swapping them is
        the one mistake that would make this whole check report the opposite
        of the truth."""
        self.assertEqual(dimensions(write(jpeg(3, 5))), (3, 5))
        self.assertEqual(dimensions(write(jpeg(5, 3))), (5, 3))

    def test_a_realistic_phone_rendition(self):
        self.assertEqual(dimensions(write(jpeg(1200, 1600))), (1200, 1600))

    def test_square_is_square(self):
        self.assertEqual(dimensions(write(jpeg(4, 4))), (4, 4))

    def test_every_frame_marker_is_understood(self):
        """Baseline, extended, progressive. A phone that sends progressive
        JPEG must not read as "no frame header"."""
        for marker in (0xC0, 0xC1, 0xC2):
            with self.subTest(marker=hex(marker)):
                self.assertEqual(
                    dimensions(write(jpeg(300, 400, marker=marker))),
                    (300, 400))

    def test_a_huffman_table_is_not_mistaken_for_a_frame(self):
        """0xC4 sits in the same numeric range as the frame markers and is
        not one. Reading it as a frame gives two numbers that are not the
        image's size."""
        dht = bytes.fromhex("ffc40014") + bytes(18)
        data = jpeg(300, 400)
        data = data[:2] + dht + data[2:]
        self.assertEqual(dimensions(write(data)), (300, 400))

    def test_a_non_jpeg_is_refused_rather_than_guessed(self):
        with self.assertRaises(ValueError):
            dimensions(write(b"\x89PNG\r\n\x1a\n" + bytes(64)))

    def test_a_truncated_file_says_so(self):
        with self.assertRaises(ValueError):
            dimensions(write(bytes.fromhex("ffd8") + bytes(20)))
