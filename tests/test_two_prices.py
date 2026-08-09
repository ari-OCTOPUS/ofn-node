"""Two prices, and the one the warning is computed against.

The whole point, in one sentence: listed at $100, floor $60, cost $80. A
system that judges profit on the listed price calls that healthy while she
sells at a stall for $60 and loses $20 every time.

Also here: nothing is "stale" until she has said how long is too long.
Ninety days was a guess, and a guess wearing a warning label trains her to
ignore warnings.
"""

import os
import unittest

from ofn.adapters.products import (LOSES_MONEY, STALE, ProductStore,
                                   money_view, net_margin_aud, verdicts)
from tests.tmpdir import temp_dir

JAN = "2026-01-10T09:00:00Z"
# No labour term: the two time questions were removed, so a piece costs what
# was bought for it. The fixture still totals $80 exactly, because what these
# tests are about is *which price the warning is computed against* — that
# argument does not care how the cost was assembled.
FORMULA = dict(cost_fields=("materials_cost_aud", "packaging_cost_aud"),
               labour_hours_field="", labour_rate_field="")

# materials 77.5 + packaging 2.5 = $80.00 exactly
COST80 = {"name": "گوشواره", "materials_cost_aud": 77.5,
          "packaging_cost_aud": 2.5}


class Base(unittest.TestCase):
    def setUp(self):
        self.s = ProductStore(
            os.path.join(temp_dir(self), "p.db"), **FORMULA)
        self.addCleanup(self.s.close)

    def make(self, **over):
        f = dict(COST80)
        f.update(over)
        return self.s.create("ziman", "ZM", f, now_iso=JAN)


class TestTheWarningUsesTheFloor(Base):
    def test_the_exact_case_this_decision_came_from(self):
        p = self.make(price_primary_aud=100.0, price_secondary_aud=60.0)
        self.assertAlmostEqual(p.cogs_aud, 80.0)
        # Listed price alone would have said "healthy".
        self.assertAlmostEqual(p.judged_price_aud, 60.0)
        self.assertTrue(p.loses_money)
        self.assertAlmostEqual(p.gross_margin_aud, -20.0)

    def test_a_healthy_listing_with_a_healthy_floor_is_healthy(self):
        p = self.make(price_primary_aud=140.0, price_secondary_aud=120.0)
        self.assertFalse(p.loses_money)
        self.assertAlmostEqual(p.gross_margin_aud, 40.0)

    def test_no_floor_means_the_listed_price_is_judged(self):
        p = self.make(price_primary_aud=60.0)
        self.assertIsNone(p.price_secondary_aud)
        self.assertAlmostEqual(p.judged_price_aud, 60.0)
        self.assertTrue(p.loses_money)

    def test_a_floor_alone_is_still_judged(self):
        p = self.make(price_secondary_aud=60.0)
        self.assertAlmostEqual(p.judged_price_aud, 60.0)
        self.assertTrue(p.loses_money)

    def test_neither_price_is_not_a_loss(self):
        p = self.make()
        self.assertIsNone(p.judged_price_aud)
        self.assertFalse(p.loses_money)
        self.assertIsNone(p.gross_margin_aud)

    def test_the_floor_is_never_averaged_with_the_listing(self):
        # $80 would be the average of 100 and 60, and would read as break-even.
        p = self.make(price_primary_aud=100.0, price_secondary_aud=60.0)
        self.assertNotAlmostEqual(p.judged_price_aud, 80.0)

    def test_raising_the_floor_above_cost_clears_the_warning(self):
        p = self.make(price_primary_aud=100.0, price_secondary_aud=60.0)
        _, after = self.s.update("ziman", p.sku,
                                 {"price_secondary_aud": 95.0}, now_iso=JAN)
        self.assertFalse(after.loses_money)

    def test_the_verdict_follows_the_floor(self):
        p = self.make(price_primary_aud=100.0, price_secondary_aud=60.0)
        self.assertIn(LOSES_MONEY,
                      verdicts(p, "2026-02-01", stale_after_days=90,
                               quick_sale_days=7))

    def test_the_channel_fee_comes_off_the_floor_not_the_listing(self):
        fees = {"market": {"percent": 0.10, "fixed": 0.0}}
        p = self.make(price_primary_aud=100.0, price_secondary_aud=60.0)
        _, sold = self.s.update("ziman", p.sku,
                                {"state": "sold", "channel": "market"},
                                now_iso=JAN)
        self.assertAlmostEqual(net_margin_aud(sold, fees), 60.0 - 6.0 - 80.0)


class TestStaleNeedsHerAnswer(Base):
    def setUp(self):
        super().setUp()
        p = self.make(price_primary_aud=200.0)
        _, self.listed = self.s.update("ziman", p.sku, {"state": "for_sale"},
                                       now_iso=JAN)

    def test_nothing_is_stale_until_she_says_how_long_is_too_long(self):
        self.assertEqual(self.listed.days_on_sale("2026-12-31"), 355)
        got = verdicts(self.listed, "2026-12-31", stale_after_days=None,
                       quick_sale_days=7)
        self.assertNotIn(STALE, got)

    def test_with_her_answer_the_flag_appears(self):
        got = verdicts(self.listed, "2026-12-31", stale_after_days=30,
                       quick_sale_days=7)
        self.assertIn(STALE, got)

    def test_her_answer_is_the_threshold_not_a_default(self):
        # 355 days on sale, and she said she only worries after a year.
        got = verdicts(self.listed, "2026-12-31", stale_after_days=400,
                       quick_sale_days=7)
        self.assertNotIn(STALE, got)

    def test_an_unanswered_threshold_still_reports_a_loss(self):
        # One missing answer must not silence a different, known problem.
        p = self.make(price_primary_aud=10.0)
        got = verdicts(p, "2026-12-31", stale_after_days=None,
                       quick_sale_days=7)
        self.assertIn(LOSES_MONEY, got)


class TestPackAsksForIt(unittest.TestCase):
    def test_the_pack_asks_her_and_carries_no_guess(self):
        from ofn.adapters.packloader import load_pack
        pack = load_pack("packs/ziman.yaml")
        self.assertIn("sales.days_before_worry", pack.required_facts)
        meta = pack.question_meta["sales.days_before_worry"]
        self.assertIn("نگران", meta["label"])
        self.assertEqual(meta["min"], 7)
        self.assertEqual(meta["max"], 730)
        # No default: offering one is offering a guess.
        self.assertNotIn("default", meta)



class TestGstMovesTheVerdict(unittest.TestCase):
    """The tax question is not paperwork — it is the width of the band
    between "healthy" and "losing money"."""

    def setUp(self):
        self.s = ProductStore(os.path.join(temp_dir(self), "p.db"),
                              **FORMULA)
        self.addCleanup(self.s.close)
        # cost $80, listed $86
        self.p = self.s.create("ziman", "ZM",
                               dict(COST80, price_primary_aud=86.0),
                               now_iso=JAN)

    def test_registered_turns_a_healthy_piece_into_a_loss(self):
        healthy = money_view(self.p, gst_rate=0.0, gst_known=True)
        taxed = money_view(self.p, gst_rate=0.10, gst_known=True)
        self.assertFalse(healthy["loses_money"])
        self.assertTrue(taxed["loses_money"])
        self.assertAlmostEqual(taxed["price_ex_tax_aud"], 86.0 / 1.1)

    def test_an_unanswered_question_is_marked_not_guessed(self):
        v = money_view(self.p, gst_rate=0.10, gst_known=False)
        self.assertFalse(v["gst_known"])
        # No rate applied while unknown — but the caller is told, so the
        # screen can say the figure is not final.
        self.assertAlmostEqual(v["price_ex_tax_aud"], 86.0)

    def test_the_verdict_follows_the_same_computation(self):
        v = money_view(self.p, gst_rate=0.10, gst_known=True)
        got = verdicts(self.p, "2026-02-01", stale_after_days=None,
                       quick_sale_days=7, loses_money=v["loses_money"])
        self.assertIn(LOSES_MONEY, got)
        # …and the un-taxed view does not raise the flag.
        clean = money_view(self.p, gst_rate=0.0, gst_known=True)
        self.assertNotIn(LOSES_MONEY,
                         verdicts(self.p, "2026-02-01", stale_after_days=None,
                                  quick_sale_days=7,
                                  loses_money=clean["loses_money"]))

    def test_zero_rate_agrees_with_the_plain_property(self):
        # One computation, two doors. They must not drift.
        v = money_view(self.p, gst_rate=0.0, gst_known=True)
        self.assertEqual(v["loses_money"], self.p.loses_money)
        self.assertAlmostEqual(v["margin_aud"], self.p.gross_margin_aud)


class TestPackAsksAboutGst(unittest.TestCase):
    def test_the_pack_asks_and_offers_no_default(self):
        from ofn.adapters.packloader import load_pack
        pack = load_pack("packs/ziman.yaml")
        self.assertIn("business.gst_registered", pack.required_facts)
        meta = pack.question_meta["business.gst_registered"]
        self.assertEqual(list(meta["options"]), ["\u0628\u0644\u0647", "\u062e\u06cc\u0631"])
        self.assertNotIn("default", meta)
        self.assertIn("\u062d\u0633\u0627\u0628\u062f\u0627\u0631", meta["hint"])

if __name__ == "__main__":
    unittest.main()
