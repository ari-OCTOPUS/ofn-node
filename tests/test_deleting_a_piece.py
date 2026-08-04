"""Removing a piece, and the code it used.

Written because the first real piece recorded on this node was a test — the
partner was trying the app, the numbers were invented — and the owner asked
for it to go.

Deleting is easy. What is not easy is that `next_sku` derived the next code
from the rows in the table, and its docstring claimed that "retiring a row
never hands its code to a different piece". The query could not keep that
promise: a deleted row is precisely the one it can no longer see. The first
deletion would have handed ZM-0001 to the next piece while the ledger still
described a different ZM-0001 under that name — two pieces, one code, one
history that quietly disagrees with itself.

A code that has been read out on a phone call is spent for ever, whatever
happens to the row.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from ofn.adapters.products import ProductError, ProductStore

FORMULA = dict(cost_fields=("materials_cost_aud", "packaging_cost_aud"),
               labour_hours_field="", labour_rate_field="")
JAN = "2026-01-10T09:00:00Z"


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "p.sqlite")
        self.s = self.open()

    def open(self):
        s = ProductStore(self.path, **FORMULA)
        self.addCleanup(s.close)
        return s

    def add(self, name="گوشواره", **over):
        f = {"name": name, "materials_cost_aud": 10.0}
        f.update(over)
        return self.s.create("ziman", "ZM", f, now_iso=JAN)


class TestTheCodeIsNeverReissued(Base):
    def test_deleting_the_only_piece_does_not_free_its_code(self):
        first = self.add()
        self.assertEqual(first.sku, "ZM-0001")
        self.s.delete("ziman", "ZM-0001")
        self.assertEqual(self.add(name="دومی").sku, "ZM-0002")

    def test_deleting_the_newest_does_not_free_its_code(self):
        self.add()
        self.add(name="دومی")
        self.s.delete("ziman", "ZM-0002")
        self.assertEqual(self.add(name="سومی").sku, "ZM-0003")

    def test_deleting_every_piece_still_moves_forward(self):
        for i in range(3):
            self.add(name=f"قطعه {i}")
        for i in range(1, 4):
            self.s.delete("ziman", f"ZM-{i:04d}")
        self.assertEqual(self.add(name="تازه").sku, "ZM-0004")

    def test_the_high_water_mark_survives_reopening(self):
        """It lives in the file, not in the process."""
        self.add()
        self.s.delete("ziman", "ZM-0001")
        self.s.close()
        self.s = self.open()
        self.assertEqual(self.add(name="دومی").sku, "ZM-0002")

    def test_one_business_does_not_spend_anothers_numbers(self):
        self.s.create("ziman", "ZM", {"name": "الف"}, now_iso=JAN)
        self.s.create("lead", "LD", {"name": "ب"}, now_iso=JAN)
        self.s.delete("ziman", "ZM-0001")
        self.assertEqual(
            self.s.create("lead", "LD", {"name": "ج"}, now_iso=JAN).sku,
            "LD-0002")
        self.assertEqual(
            self.s.create("ziman", "ZM", {"name": "د"}, now_iso=JAN).sku,
            "ZM-0002")

    def test_rows_still_act_as_a_floor(self):
        """If the high-water table were ever lost or reset, the codes plainly
        in use must still not be handed out again."""
        self.add()
        self.add(name="دومی")
        self.s._conn.execute("DELETE FROM sku_high_water")
        self.assertEqual(self.s.next_sku("ziman", "ZM"), "ZM-0003")


class TestWhatDeleteReturnsAndRemoves(Base):
    def test_it_returns_the_row_it_removed(self):
        """So the caller can write down what disappeared. A deletion that
        leaves no description of what it deleted is the one operation this
        node must not have."""
        made = self.add(name="باکس", materials_cost_aud=180.0)
        gone = self.s.delete("ziman", made.sku)
        self.assertEqual(gone.name, "باکس")
        self.assertAlmostEqual(gone.materials_cost_aud, 180.0)

    def test_the_piece_is_actually_gone(self):
        self.add()
        self.s.delete("ziman", "ZM-0001")
        self.assertIsNone(self.s.get("ziman", "ZM-0001"))
        self.assertEqual(self.s.list("ziman"), [])

    def test_deleting_something_absent_is_refused_not_ignored(self):
        with self.assertRaises(ProductError):
            self.s.delete("ziman", "ZM-9999")

    def test_a_sibling_business_cannot_delete_it(self):
        self.add()
        with self.assertRaises(ProductError):
            self.s.delete("lead", "ZM-0001")
        self.assertIsNotNone(self.s.get("ziman", "ZM-0001"))

    def test_its_photos_go_with_it(self):
        p = self.add()
        self.s._conn.execute("BEGIN IMMEDIATE")
        self.s._conn.execute(
            "INSERT INTO product_photos (product_id, original_path, "
            "display_path, thumb_path) VALUES (?, 'a', 'b', 'c')", (p.id,))
        self.s._conn.execute("COMMIT")
        self.assertEqual(self.s.photo_count(p.id), 1)
        self.s.delete("ziman", p.sku)
        self.assertEqual(self.s.photo_count(p.id), 0)


class TestOlderFilesAreSeeded(Base):
    def test_a_file_written_before_the_table_existed_keeps_its_numbers(self):
        """Otherwise reopening an existing database would start at zero and
        reissue every code sitting in it."""
        self.add()
        self.add(name="دومی")
        self.s._conn.execute("DROP TABLE sku_high_water")
        self.s.close()

        s = self.open()
        row = s._conn.execute(
            "SELECT last FROM sku_high_water WHERE tenant_id = 'ziman'"
        ).fetchone()
        self.assertEqual(int(row[0]), 2)
        self.assertEqual(s.next_sku("ziman", "ZM"), "ZM-0003")


if __name__ == "__main__":
    unittest.main()
