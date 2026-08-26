"""Product records — one unique piece per row.

The tests that matter most:

  * a piece made last month does not change cost when this month's rate does,
  * a piece with no price is not "losing money", it is unpriced,
  * a sold piece's age stops at the sale, and
  * the platform's cut never touches cost.

Each of those is a way a record can quietly start lying, and each is the kind
of lie somebody re-prices a piece because of.
"""

import os
import unittest

from ofn.adapters.packloader import load_pack
from ofn.adapters.products import (CHANNELS, LOSES_MONEY,
                                   MAX_PHOTOS_PER_PRODUCT, QUICK_SALE, STALE,
                                   STATES, ProductError, ProductStore,
                                   channel_fee, cogs_for, net_margin_aud,
                                   verdicts)
from tests.tmpdir import temp_dir

JAN = "2026-01-10T09:00:00Z"
FEB = "2026-02-10T09:00:00Z"
MAY = "2026-05-20T09:00:00Z"

# $77.50 materials + $3 packaging = $80.50. The labour term is gone — the
# two time questions were removed — so the same total is now assembled from
# what was actually bought.
FULL = {
    "name": "گوشوارهٔ نقره",
    "materials_cost_aud": 77.5,
    "packaging_cost_aud": 3.0,
    "price_primary_aud": 120.0,
}

FORMULA = dict(cost_fields=("materials_cost_aud", "packaging_cost_aud"),
               labour_hours_field="", labour_rate_field="")


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        self.path = os.path.join(self.dir, "products.db")
        self.s = ProductStore(self.path, **FORMULA)
        self.addCleanup(self.s.close)

    def make(self, when=JAN, **over):
        f = dict(FULL)
        f.update(over)
        return self.s.create("ziman", "ZM", f, now_iso=when)

    def sell(self, sku, *, when=FEB, channel="direct"):
        out = self.s.record_sale(
            "ziman", sku, event_id=f"sale-{sku}", sold_at=when,
            channel=channel, amount_unknown=True, fee_unknown=True,
            now_iso=when)
        self.assertTrue(out["ok"])
        return self.s.get("ziman", sku)


class TestCost(Base):
    def test_cogs_is_the_packs_formula_with_no_division(self):
        self.assertAlmostEqual(self.make().cogs_aud, 80.5)

    def test_cogs_follows_an_edit_of_its_inputs(self):
        p = self.make()
        _, after = self.s.update("ziman", p.sku,
                                 {"materials_cost_aud": 100.0}, now_iso=FEB)
        self.assertAlmostEqual(after.cogs_aud, 100.0 + 3.0)

    def test_the_stored_cost_agrees_with_the_formula(self):
        # `cogs_aud` is a plain column now, so this is the check that used to
        # be free when SQLite computed it.
        p = self.make()
        self.assertAlmostEqual(self.s.recompute_cogs("ziman", p.sku),
                               p.cogs_aud)

    def test_cogs_cannot_be_set_by_hand(self):
        with self.assertRaises(ProductError):
            self.make(cogs_aud=1.0)

    def test_formula_ignores_a_field_the_pack_did_not_name(self):
        """Including the two labour columns, which still exist in the file
        and are now named by nothing."""
        self.assertAlmostEqual(
            cogs_for({"materials_cost_aud": 10.0, "shipping_cost_aud": 999.0,
                      "labour_hours": 1.0, "hourly_rate_aud": 20.0}, **FORMULA),
            10.0)


class TestHistoricalTruth(Base):
    def test_a_later_cost_does_not_rewrite_an_older_piece(self):
        """Costs are copied onto the piece at save time, not looked up. When
        silver gets dearer in May, what January cost stays what January cost —
        otherwise every past margin silently rewrites itself."""
        old = self.make()
        self.assertAlmostEqual(old.cogs_aud, 80.5)

        new = self.make(when=MAY, name="دومی", materials_cost_aud=95.0)
        self.assertAlmostEqual(new.cogs_aud, 95.0 + 3.0)

        again = self.s.get("ziman", old.sku)
        self.assertAlmostEqual(again.cogs_aud, 80.5)
        self.assertAlmostEqual(again.materials_cost_aud, 77.5)


class TestPrice(Base):
    def test_a_price_under_cost_loses_money(self):
        p = self.make(price_primary_aud=50.0)
        self.assertTrue(p.loses_money)
        self.assertIn(LOSES_MONEY, verdicts(p, MAY, stale_after_days=90,
                                            quick_sale_days=7))

    def test_an_unpriced_piece_is_not_losing_money(self):
        p = self.make(price_primary_aud=None)
        self.assertIsNone(p.gross_margin_aud)
        self.assertFalse(p.loses_money)
        self.assertEqual(verdicts(p, MAY, stale_after_days=90,
                                  quick_sale_days=7), ())

    def test_gross_margin(self):
        p = self.make()
        self.assertAlmostEqual(p.gross_margin_aud, 39.5)
        self.assertAlmostEqual(p.gross_margin_pct, 39.5 / 120.0)


class TestChannelFeeIsNotCost(Base):
    FEES = {"etsy": {"percent": 0.065, "fixed": 0.30},
            "direct": {"percent": 0.0, "fixed": 0.0}}

    def test_the_fee_never_enters_cost(self):
        p = self.make()
        sold = self.sell(p.sku, channel="etsy")
        # Same piece, same cost, regardless of who bought it.
        self.assertAlmostEqual(sold.cogs_aud, 80.5)

    def test_the_fee_comes_off_the_margin(self):
        p = self.make()
        sold = self.sell(p.sku, channel="etsy")
        expected = 120.0 - (120.0 * 0.065 + 0.30) - 80.5
        self.assertAlmostEqual(net_margin_aud(sold, self.FEES), expected)

    def test_an_unconfigured_channel_refuses_rather_than_assuming_zero(self):
        # A silent zero would report a margin the business does not keep.
        p = self.make()
        sold = self.sell(p.sku, channel="market")
        with self.assertRaises(ProductError):
            net_margin_aud(sold, self.FEES)

    def test_nothing_sold_means_no_fee(self):
        self.assertEqual(channel_fee(120.0, None, self.FEES), 0.0)

    def test_selling_without_naming_a_channel_is_refused(self):
        p = self.make()
        with self.assertRaises(ProductError):
            self.s.update("ziman", p.sku, {"state": "sold"}, now_iso=FEB)


class TestStateAndAge(Base):
    def test_listing_stamps_the_date(self):
        p = self.make()
        self.assertIsNone(p.listed_at)
        _, listed = self.s.update("ziman", p.sku, {"state": "for_sale"},
                                  now_iso=JAN)
        self.assertTrue(listed.listed_at.startswith("2026-01-10"))

    def test_a_piece_sitting_too_long_is_stale(self):
        p = self.make()
        _, listed = self.s.update("ziman", p.sku, {"state": "for_sale"},
                                  now_iso=JAN)
        self.assertEqual(listed.days_on_sale("2026-05-20"), 130)
        self.assertIn(STALE, verdicts(listed, "2026-05-20",
                                      stale_after_days=90, quick_sale_days=7))

    def test_a_fresh_listing_is_not_stale(self):
        p = self.make()
        _, listed = self.s.update("ziman", p.sku, {"state": "for_sale"},
                                  now_iso=JAN)
        self.assertEqual(verdicts(listed, "2026-02-01", stale_after_days=90,
                                  quick_sale_days=7), ())

    def test_a_sold_pieces_age_stops_at_the_sale(self):
        # Otherwise nothing would ever count as having sold fast, because the
        # number keeps growing long after the event.
        p = self.make()
        self.s.update("ziman", p.sku, {"state": "for_sale"}, now_iso=JAN)
        sold = self.sell(p.sku, when="2026-01-13T09:00:00Z")
        self.assertEqual(sold.days_on_sale("2026-12-31"), 3)
        self.assertIn(QUICK_SALE, verdicts(sold, "2026-12-31",
                                           stale_after_days=90,
                                           quick_sale_days=7))

    def test_a_slow_sale_is_not_a_quick_one(self):
        p = self.make()
        self.s.update("ziman", p.sku, {"state": "for_sale"}, now_iso=JAN)
        sold = self.sell(p.sku, when=MAY)
        self.assertEqual(verdicts(sold, MAY, stale_after_days=90,
                                  quick_sale_days=7), ())

    def test_sold_without_ever_being_listed_has_age_zero(self):
        p = self.make()
        sold = self.sell(p.sku)
        self.assertEqual(sold.days_on_sale(MAY), 0)

    def test_an_unlisted_piece_has_no_age(self):
        self.assertIsNone(self.make().days_on_sale(MAY))

    def test_gifted_is_a_real_ending(self):
        p = self.make()
        _, gifted = self.s.update("ziman", p.sku, {"state": "gifted"},
                                  now_iso=FEB)
        self.assertEqual(gifted.state, "gifted")
        self.assertIsNone(gifted.channel)

    def test_bad_state_and_channel_are_refused(self):
        p = self.make()
        with self.assertRaises(ProductError):
            self.s.update("ziman", p.sku, {"state": "sold_out"}, now_iso=FEB)
        with self.assertRaises(ProductError):
            self.s.update("ziman", p.sku, {"channel": "ebay"}, now_iso=FEB)


class TestNoStockAnywhere(unittest.TestCase):
    def test_the_unique_piece_model_has_no_counts(self):
        from ofn.adapters.products import EDITABLE, SCHEMA
        blob = " ".join(SCHEMA).lower()
        for word in ("stock", "quantity", "qty", "batch", "runway"):
            self.assertNotIn(word, blob)
            self.assertNotIn(word, " ".join(EDITABLE).lower())

    def test_no_column_mentions_tax(self):
        from ofn.adapters.products import SCHEMA
        blob = " ".join(SCHEMA).lower()
        for word in ("gst", "tax", "vat"):
            self.assertNotIn(word, blob)


class TestRefusals(Base):
    def test_negative_numbers_are_refused(self):
        with self.assertRaises(ProductError):
            self.make(materials_cost_aud=-1)

    def test_a_name_is_required(self):
        with self.assertRaises(ProductError):
            self.make(name="   ")

    def test_unknown_fields_are_refused(self):
        with self.assertRaises(ProductError):
            self.make(gst_amount=8.0)

    def test_text_where_a_number_belongs_is_refused(self):
        with self.assertRaises(ProductError):
            self.make(price_primary_aud="۱۲۰")

    def test_editing_a_missing_piece_says_so(self):
        with self.assertRaises(ProductError):
            self.s.update("ziman", "ZM-9999", {"name": "x"}, now_iso=FEB)


class TestSkuAndTenants(Base):
    def test_codes_run_in_sequence(self):
        self.assertEqual(self.make().sku, "ZM-0001")
        self.assertEqual(self.make(name="ب").sku, "ZM-0002")

    def test_one_business_does_not_see_anothers_pieces(self):
        self.make()
        self.s.create("lead", "LD", {"name": "رنگ‌آمیزی"}, now_iso=JAN)
        self.assertEqual([p.sku for p in self.s.list("ziman")], ["ZM-0001"])
        self.assertEqual([p.sku for p in self.s.list("lead")], ["LD-0001"])

    def test_editing_is_scoped_to_the_business(self):
        self.make()
        with self.assertRaises(ProductError):
            self.s.update("lead", "ZM-0001", {"name": "x"}, now_iso=FEB)


class TestSurvivesRestart(Base):
    def test_three_pieces_are_still_there_after_reopening(self):
        for n in ("یک", "دو", "سه"):
            self.make(name=n)
        self.s.close()

        again = ProductStore(self.path, **FORMULA)
        self.addCleanup(again.close)
        rows = again.list("ziman")
        self.assertEqual([p.name for p in rows], ["یک", "دو", "سه"])
        self.assertEqual([p.sku for p in rows],
                         ["ZM-0001", "ZM-0002", "ZM-0003"])
        self.assertAlmostEqual(rows[0].cogs_aud, 80.5)
        self.assertEqual(again.next_sku("ziman", "ZM"), "ZM-0004")


class TestPhotosReadyForTomorrow(Base):
    def test_three_sizes_exist_tonight_so_tomorrow_is_not_a_migration(self):
        p = self.make()
        conn = self.s._conn
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO product_photos (product_id, original_path, "
            "display_path, thumb_path, position) VALUES (?, ?, ?, ?, 0)",
            (p.id, "/o/1.jpg", "/d/1.jpg", "/t/1.jpg"))
        conn.execute("COMMIT")
        self.assertEqual(self.s.photo_count(p.id), 1)
        self.assertEqual(MAX_PHOTOS_PER_PRODUCT, 5)


class TestPackDrivesIt(unittest.TestCase):
    def test_the_ziman_pack_declares_the_formula_not_the_code(self):
        p = load_pack("packs/ziman.yaml")
        self.assertEqual(p.cost_fields,
                         ("materials_cost_aud", "packaging_cost_aud"))
        # The pack no longer declares a labour term at all.
        self.assertEqual(p.labour_hours_field, "")
        self.assertEqual(p.labour_rate_field, "")
        self.assertEqual(p.sku_prefix, "ZM")

    def test_the_pack_no_longer_asks_per_product_questions(self):
        # Those numbers live on the piece now. Asking them once per business
        # would price every piece the same.
        p = load_pack("packs/ziman.yaml")
        for gone in ("materials.cost_per_batch", "production.batch_size",
                     "stock.units_left", "sales.units_last_7d",
                     "offer.price_current"):
            self.assertNotIn(gone, p.required_facts)
        # Her hourly rate is not asked anywhere any more — not per piece,
        # and not once per business either. Removed by the owner after
        # watching the first real session.
        self.assertNotIn("time.hourly_floor", p.required_facts)

    def test_states_and_channels_are_the_agreed_values(self):
        self.assertEqual(STATES,
                         ("in_progress", "for_sale", "sold", "gifted"))
        self.assertEqual(CHANNELS,
                         ("instagram", "market", "etsy", "direct", "shopify"))


if __name__ == "__main__":
    unittest.main()
