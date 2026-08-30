"""تستِ B3: شناسه‌ی پایدارِ chunk — مستقل از ترتیبِ سراسریِ vault."""
from tests import _bootstrap  # noqa: F401

import unittest

from memory.chunk_ids import chunk_id, ids_for_chunks


class TestChunkIds(unittest.TestCase):
    def test_stable(self):
        self.assertEqual(chunk_id("a.md", "متن"), chunk_id("a.md", "متن"))

    def test_source_and_content_matter(self):
        self.assertNotEqual(chunk_id("a.md", "x"), chunk_id("b.md", "x"))
        self.assertNotEqual(chunk_id("a.md", "x"), chunk_id("a.md", "y"))

    def test_order_independence(self):
        """رگرسیونِ باگِ قدیم: اندیسِ سراسری، ID را به ترتیبِ کلِ vault گره می‌زد."""
        pairs1 = [("a.md", "c1"), ("b.md", "c2"), ("c.md", "c3")]
        pairs2 = [("c.md", "c3"), ("a.md", "c1"), ("b.md", "c2")]
        ids1 = dict(zip([p[0] for p in pairs1], ids_for_chunks(pairs1)))
        ids2 = dict(zip([p[0] for p in pairs2], ids_for_chunks(pairs2)))
        self.assertEqual(ids1, ids2)

    def test_duplicate_content_same_source_distinct(self):
        ids = ids_for_chunks([("a.md", "same"), ("a.md", "same")])
        self.assertEqual(len(set(ids)), 2)

    def test_no_collision_across_sources_with_same_content(self):
        ids = ids_for_chunks([("a.md", "same"), ("b.md", "same")])
        self.assertEqual(len(set(ids)), 2)


if __name__ == "__main__":
    unittest.main()
