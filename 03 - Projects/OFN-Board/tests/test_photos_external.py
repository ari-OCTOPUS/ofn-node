"""Photo intake. Every test here is really the same question:

can a phone, or something pretending to be a phone, make this node write
somewhere it should not, or allocate memory it should not?
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.photos import (
    ALLOWED_EDGES, MAX_DECODED_BYTES, MAX_POSITION, Payload, inspect,
    piece_prefix, relative_path,
)


def b64_of_length(n: int) -> str:
    """A syntactically valid base64 string of exactly n characters."""
    assert n % 4 == 0
    return "A" * n


class TestSizeIsJudgedBeforeDecoding(unittest.TestCase):
    def test_an_oversized_payload_is_refused(self):
        # 24MB of base64 → ~18MB decoded, over the 16MB cap.
        with self.assertRaises(FailClosedError) as ctx:
            inspect(b64_of_length(24 * 1024 * 1024))
        self.assertIn("too large", str(ctx.exception))

    def test_the_bound_is_computed_from_length_not_content(self):
        """The refusal must not depend on decoding, because decoding is the
        cost we are trying to avoid paying."""
        p = inspect(b64_of_length(4000))
        self.assertEqual(p.max_decoded_bytes, 3000)

    def test_the_bound_is_an_over_estimate_never_an_under_estimate(self):
        """Padding makes the true size smaller. Bounding high can only cause
        an early refusal; bounding low would let an oversized image through."""
        for pad in ("", "=", "=="):
            body = "A" * (400 - len(pad)) + pad
            with self.subTest(padding=len(pad)):
                p = inspect(body)
                self.assertGreaterEqual(p.max_decoded_bytes, 298)

    def test_the_largest_accepted_payload_sits_just_under_the_limit(self):
        """16MB is not divisible by three, so the biggest payload base64 can
        express under the cap lands one or two bytes short of it. Asserting
        exact equality here would be asserting an accident of the constant."""
        n = (MAX_DECODED_BYTES // 3) * 4
        got = inspect(b64_of_length(n)).max_decoded_bytes
        self.assertLessEqual(got, MAX_DECODED_BYTES)
        self.assertGreater(got, MAX_DECODED_BYTES - 3)

    def test_one_group_over_the_limit_is_refused(self):
        n = (MAX_DECODED_BYTES // 3) * 4 + 4
        with self.assertRaises(FailClosedError):
            inspect(b64_of_length(n))

    def test_the_boundary_holds_for_a_limit_that_divides_evenly(self):
        """The same edge with a limit divisible by three, where the largest
        accepted payload should land exactly on it."""
        self.assertEqual(inspect(b64_of_length(4000), limit=3000)
                         .max_decoded_bytes, 3000)
        with self.assertRaises(FailClosedError):
            inspect(b64_of_length(4004), limit=3000)

    def test_a_smaller_limit_can_be_imposed_per_route(self):
        with self.assertRaises(FailClosedError):
            inspect(b64_of_length(4000), limit=1000)

    def test_a_nonsense_limit_is_refused_rather_than_honoured(self):
        for bad in (0, -1):
            with self.subTest(limit=bad):
                with self.assertRaises(FailClosedError):
                    inspect(b64_of_length(8), limit=bad)


class TestPayloadShape(unittest.TestCase):
    def test_empty_is_refused(self):
        with self.assertRaises(FailClosedError):
            inspect("")

    def test_a_non_string_is_refused(self):
        for bad in (None, 123, b"AAAA", ["AAAA"]):
            with self.subTest(payload=type(bad).__name__):
                with self.assertRaises(FailClosedError):
                    inspect(bad)  # type: ignore[arg-type]

    def test_length_that_is_not_a_multiple_of_four_is_refused(self):
        with self.assertRaises(FailClosedError):
            inspect("AAA")

    def test_whitespace_inside_the_payload_is_refused(self):
        """A canvas never wraps its output. Newlines mean the payload did not
        come from where it claims to — and they also make the length estimate
        meaningless."""
        body = "A" * 100 + "\n" + "A" * 99
        with self.assertRaises(FailClosedError):
            inspect(body)

    def test_characters_outside_the_base64_alphabet_are_refused(self):
        with self.assertRaises(FailClosedError):
            inspect("AAAA" * 10 + "AA$A")

    def test_padding_in_the_middle_is_refused(self):
        with self.assertRaises(FailClosedError):
            inspect("AA==AAAA")


class TestDataUrlHeader(unittest.TestCase):
    def test_a_normal_canvas_output_is_accepted(self):
        p = inspect("data:image/jpeg;base64," + b64_of_length(400))
        self.assertIsInstance(p, Payload)
        self.assertEqual(p.media_type, "image/jpeg")
        self.assertEqual(p.max_decoded_bytes, 300)

    def test_the_header_is_not_counted_toward_the_size(self):
        header = "data:image/jpeg;base64,"
        bare = inspect(b64_of_length(400))
        prefixed = inspect(header + b64_of_length(400))
        self.assertEqual(bare.max_decoded_bytes, prefixed.max_decoded_bytes)

    def test_a_bare_payload_defaults_to_jpeg(self):
        self.assertEqual(inspect(b64_of_length(400)).media_type, "image/jpeg")

    def test_png_is_accepted_because_canvas_falls_back_to_it(self):
        p = inspect("data:image/png;base64," + b64_of_length(400))
        self.assertEqual(p.media_type, "image/png")

    def test_a_media_type_we_do_not_serve_is_refused(self):
        for mt in ("text/html", "image/svg+xml", "application/octet-stream"):
            with self.subTest(media_type=mt):
                with self.assertRaises(FailClosedError):
                    inspect(f"data:{mt};base64," + b64_of_length(400))

    def test_svg_is_refused_specifically(self):
        """SVG is a script container. Serving one back from our own origin is
        stored XSS wearing an image's clothes."""
        with self.assertRaises(FailClosedError):
            inspect("data:image/svg+xml;base64," + b64_of_length(400))

    def test_a_broken_data_url_is_refused_not_treated_as_image_data(self):
        """The failure this prevents: the header falls through and becomes
        part of the payload, so the size estimate is computed over a string
        that is not the image."""
        for bad in ("data:image/jpeg,AAAA", "data:;base64,AAAA",
                    "data:image/jpeg;base64" + "A" * 400):
            with self.subTest(header=bad[:28]):
                with self.assertRaises(FailClosedError):
                    inspect(bad)

    def test_a_comma_cannot_move_the_boundary(self):
        """Splitting on the last comma instead of the matched delimiter would
        let the payload choose where the header ends."""
        with self.assertRaises(FailClosedError):
            inspect("data:image/jpeg;base64," + b64_of_length(400) + ",AAAA")


class TestPathIsBuiltNotAccepted(unittest.TestCase):
    def test_a_normal_path(self):
        self.assertEqual(relative_path("alpha", "piece-01", 0, 1600),
                         "alpha/piece-01/0-1600.jpg")

    def test_traversal_in_the_piece_id_is_refused(self):
        for bad in ("../../etc/passwd", "..", "a/../b", "/etc/passwd",
                    "a/b", ".", "a\\b"):
            with self.subTest(piece_id=bad):
                with self.assertRaises(FailClosedError):
                    relative_path("alpha", bad, 0, 1600)

    def test_traversal_in_the_tenant_is_refused(self):
        with self.assertRaises(FailClosedError):
            relative_path("../bravo", "piece-01", 0, 1600)

    def test_a_null_byte_is_refused(self):
        """Truncation attacks: everything after a NUL disappears in some
        filesystem calls, so 'a.jpg\\0.php' can become 'a.jpg'."""
        with self.assertRaises(FailClosedError):
            relative_path("alpha", "piece\x00", 0, 1600)

    def test_uppercase_is_refused_rather_than_folded(self):
        """Case-insensitive filesystems make 'Piece' and 'piece' the same
        directory, so folding silently merges two pieces."""
        with self.assertRaises(FailClosedError):
            relative_path("alpha", "Piece-01", 0, 1600)

    def test_only_the_two_known_edges_are_allowed(self):
        for edge in ALLOWED_EDGES:
            with self.subTest(edge=edge):
                self.assertIn(f"-{edge}.jpg", relative_path("a", "b", 0, edge))
        for bad in (20000, 1601, 0, -320, "1600", None):
            with self.subTest(edge=bad):
                with self.assertRaises(FailClosedError):
                    relative_path("a", "b", 0, bad)  # type: ignore[arg-type]

    def test_position_is_bounded(self):
        self.assertTrue(relative_path("a", "b", MAX_POSITION, 320))
        for bad in (-1, MAX_POSITION + 1, 10_000):
            with self.subTest(position=bad):
                with self.assertRaises(FailClosedError):
                    relative_path("a", "b", bad, 320)

    def test_position_must_be_an_integer_and_a_bool_is_not_one(self):
        """True == 1 in Python, so a bool would silently become position 1."""
        for bad in (True, False, 1.0, "0", None):
            with self.subTest(position=repr(bad)):
                with self.assertRaises(FailClosedError):
                    relative_path("a", "b", bad, 320)  # type: ignore[arg-type]

    def test_two_tenants_never_share_a_directory(self):
        a = relative_path("alpha", "same-id", 0, 1600)
        b = relative_path("bravo", "same-id", 0, 1600)
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith("alpha/"))
        self.assertTrue(b.startswith("bravo/"))

    def test_the_same_inputs_always_give_the_same_path(self):
        first = relative_path("alpha", "piece-01", 3, 320)
        for _ in range(3):
            self.assertEqual(relative_path("alpha", "piece-01", 3, 320), first)


class TestCascadePrefix(unittest.TestCase):
    def test_the_prefix_covers_every_photo_of_the_piece(self):
        prefix = piece_prefix("alpha", "piece-01")
        for position in range(MAX_POSITION + 1):
            for edge in ALLOWED_EDGES:
                with self.subTest(position=position, edge=edge):
                    self.assertTrue(
                        relative_path("alpha", "piece-01", position, edge)
                        .startswith(prefix))

    def test_the_prefix_does_not_cover_a_neighbouring_piece(self):
        """'piece-1/' must not be a prefix of 'piece-10/...' — the classic
        way a cascade delete takes a piece nobody asked it to take."""
        prefix = piece_prefix("alpha", "piece-1")
        self.assertFalse(
            relative_path("alpha", "piece-10", 0, 1600).startswith(prefix))

    def test_the_prefix_is_validated_too(self):
        with self.assertRaises(FailClosedError):
            piece_prefix("alpha", "../bravo")


if __name__ == "__main__":
    unittest.main()
