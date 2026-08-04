"""Product records.

The tests that matter most here are two:

  * the cost of a product made last month does not move when this month's
    hourly rate changes, and
  * a product with no price is not "losing money" — it is unpriced.

Both are ways a record can quietly start lying about the past, and both are
the kind of lie somebody re-prices a product because of.
"""

import os
import tempfile
import unittest

from ofn.adapters.products import (EDITABLE, MAX_PHOTOS_PER_PRODUCT,
                                   ProductError, ProductStore)

NOW = "2026-08-04T16:00:00Z"
LATER = "2026-09-04T16:00:00Z"

# 120/10 materials + 1.5h × $25 + $3 packaging = $52.50
FULL = {
    "name": "شمع دست‌ساز",
    "batch_materials_cost_aud": 120.0,
    "batch_size": 10,
    "labour_hours": 1.5,
    "hourly_rate_aud": 25.0,
    "packaging_cost_aud": 3.0,
    "price_aud": 80.0,
    "stock_qty": 4,
}


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "products.db")
        self.s = ProductStore(self.path)
        self.addCleanup(self.s.close)

    def make(self, **over):
        f = dict(FULL)
        f.update(over)
        return self.s.create("ziman", "ZM", f, now_iso=NOW)


class TestCost(Base):
    def test_cogs_is_the_pack_formula(self):
        self.assertAlmostEqual(self.make().cogs_aud, 52.5)

    def test_cogs_follows_an_edit_of_its_inputs(self):
        p = self.make()
        _, after = self.s.update("ziman", p.sku,
                                 {"labour_hours": 2.5}, now_iso=LATER)
        self.assertAlmostEqual(after.cogs_aud, 12.0 + 62.5 + 3.0)

    def test_margin_and_percent(self):
        p = self.make()
        self.assertAlmostEqual(p.margin_aud, 27.5)
        self.assertAlmostEqual(p.margin_pct, 27.5 / 80.0)
        self.assertFalse(p.loses_money)

    def test_a_price_under_cost_loses_money(self):
        p = self.make(price_aud=40.0)
        self.assertTrue(p.loses_money)
        self.assertLess(p.margin_aud, 0)

    def test_an_unpriced_product_is_not_losing_money(self):
        # It is unpriced. Painting that red would train her to ignore red.
        p = self.make(price_aud=None)
        self.assertIsNone(p.price_aud)
        self.assertIsNone(p.margin_aud)
        self.assertIsNone(p.margin_pct)
        self.assertFalse(p.loses_money)


class TestHistoricalTruth(Base):
    def test_raising_the_rate_later_does_not_rewrite_an_old_product(self):
        old = self.make()                      # made at $25/hour
        self.assertAlmostEqual(old.cogs_aud, 52.5)

        # A month later she values her time at $35 and makes something new.
        new = self.make(name="دومی", hourly_rate_aud=35.0)
        self.assertAlmostEqual(new.cogs_aud, 12.0 + 52.5 + 3.0)

        # The old product is untouched. It was profitable at the rate that
        # applied then, and it still says so.
        again = self.s.get("ziman", old.sku)
        self.assertAlmostEqual(again.cogs_aud, 52.5)
        self.assertAlmostEqual(again.hourly_rate_aud, 25.0)

    def test_the_rate_is_stored_on_the_row_not_looked_up(self):
        p = self.make()
        self.assertIn("hourly_rate_aud", p.as_dict())
        self.assertAlmostEqual(p.hourly_rate_aud, 25.0)


class TestRefusals(Base):
    def test_zero_batch_is_refused_rather_than_storing_a_null_cost(self):
        # SQLite returns NULL for x/0 instead of raising, so without the
        # guard this would store a product whose cost is simply missing.
        with self.assertRaises(ProductError):
            self.make(batch_size=0)

    def test_negative_numbers_are_refused(self):
        with self.assertRaises(ProductError):
            self.make(labour_hours=-1)

    def test_a_name_is_required(self):
        with self.assertRaises(ProductError):
            self.make(name="   ")

    def test_unknown_fields_are_refused(self):
        with self.assertRaises(ProductError):
            self.make(gst_amount=8.0)

    def test_cogs_cannot_be_set_by_hand(self):
        self.assertNotIn("cogs_aud", EDITABLE)
        with self.assertRaises(ProductError):
            self.make(cogs_aud=1.0)

    def test_a_bad_status_is_refused(self):
        with self.assertRaises(ProductError):
            self.make(status="on_sale")

    def test_text_where_a_number_belongs_is_refused(self):
        with self.assertRaises(ProductError):
            self.make(price_aud="۸۰")

    def test_editing_a_missing_product_says_so(self):
        with self.assertRaises(ProductError):
            self.s.update("ziman", "ZM-9999", {"stock_qty": 1}, now_iso=NOW)


class TestSku(Base):
    def test_codes_run_in_sequence(self):
        self.assertEqual(self.make().sku, "ZM-0001")
        self.assertEqual(self.make(name="ب").sku, "ZM-0002")
        self.assertEqual(self.make(name="پ").sku, "ZM-0003")

    def test_next_code_comes_from_the_highest_used_not_the_count(self):
        self.make()
        self.make(name="ب")
        self.s.update("ziman", "ZM-0001", {"status": "archived"}, now_iso=NOW)
        # Archiving must not hand ZM-0002's number to something new.
        self.assertEqual(self.s.next_sku("ziman", "ZM"), "ZM-0003")


class TestTenantIsolation(Base):
    def test_one_business_does_not_see_anothers_products(self):
        self.make()
        self.s.create("lead", "LD", {"name": "رنگ‌آمیزی"}, now_iso=NOW)
        self.assertEqual([p.sku for p in self.s.list("ziman")], ["ZM-0001"])
        self.assertEqual([p.sku for p in self.s.list("lead")], ["LD-0001"])

    def test_editing_is_scoped_to_the_business(self):
        self.make()
        with self.assertRaises(ProductError):
            self.s.update("lead", "ZM-0001", {"stock_qty": 9}, now_iso=NOW)


class TestListing(Base):
    def test_archived_products_are_hidden_by_default(self):
        self.make()
        self.make(name="ب")
        self.s.update("ziman", "ZM-0001", {"status": "archived"}, now_iso=NOW)
        self.assertEqual([p.sku for p in self.s.list("ziman")], ["ZM-0002"])
        self.assertEqual(len(self.s.list("ziman", include_archived=True)), 2)


class TestSurvivesRestart(Base):
    def test_three_products_are_still_there_after_reopening(self):
        for n in ("یک", "دو", "سه"):
            self.make(name=n)
        self.s.close()

        # Same file, new process would do exactly this.
        again = ProductStore(self.path)
        self.addCleanup(again.close)
        rows = again.list("ziman")
        self.assertEqual([p.name for p in rows], ["یک", "دو", "سه"])
        self.assertEqual([p.sku for p in rows],
                         ["ZM-0001", "ZM-0002", "ZM-0003"])
        self.assertAlmostEqual(rows[0].cogs_aud, 52.5)
        self.assertEqual(again.next_sku("ziman", "ZM"), "ZM-0004")


class TestPhotoTableIsReadyForTomorrow(Base):
    def test_the_table_exists_tonight_so_tomorrow_is_not_a_migration(self):
        self.assertEqual(self.s.photo_count(1), 0)
        self.assertEqual(MAX_PHOTOS_PER_PRODUCT, 5)

    def test_photos_disappear_with_their_product(self):
        p = self.make()
        conn = self.s._conn
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO product_photos (product_id, original_path, "
            "display_path, position) VALUES (?, ?, ?, 0)",
            (p.id, "/o/1.jpg", "/d/1.jpg"))
        conn.execute("COMMIT")
        self.assertEqual(self.s.photo_count(p.id), 1)

        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM products WHERE id = ?", (p.id,))
        conn.execute("COMMIT")
        self.assertEqual(self.s.photo_count(p.id), 0)


class TestNoTaxAnywhere(unittest.TestCase):
    def test_no_column_mentions_tax(self):
        # The business is not registered for GST, so no page, receipt or
        # export may imply one. Easiest way to keep that true is to have
        # nowhere to put it.
        from ofn.adapters.products import SCHEMA
        blob = " ".join(SCHEMA).lower()
        for word in ("gst", "tax", "vat"):
            self.assertNotIn(word, blob)


if __name__ == "__main__":
    unittest.main()
