"""Costing rules.

The tests that matter here are the refusals. Getting the arithmetic right is
table stakes; the failure that costs real money is a plausible margin built
out of a fact nobody supplied.
"""

import unittest

from ofn.adapters.ziman_costing import (BELOW_FLOOR, HEALTHY, LOSS_MAKING,
                                        Costing, NotReady, assess,
                                        price_for_margin)
from ofn.kernel.domain import Currency, Locale, LocaleError

AU = Locale("en-AU", Currency("AUD", "$", 2), timezone="Australia/Sydney",
            tax_status="not_registered", tax_rate=0.10,
            tax_registration_threshold=75_000.0)
AU_GST = Locale("en-AU", Currency("AUD", "$", 2), timezone="Australia/Sydney",
                tax_status="registered", tax_rate=0.10,
                tax_registration_threshold=75_000.0)
UNSET = Locale("en-AU", Currency("AUD", "$", 2))


def facts(**over):
    f = {
        "materials.cost_per_batch": 120.0,   # $120 of materials
        "production.batch_size": 10.0,       # makes 10 boxes
        "time.hours_per_item": 1.5,
        "time.hourly_floor": 25.0,
        "offer.price_current": 80.0,
    }
    f.update(over)
    return f


def go(f, locale=AU, floor=0.30, warn=7.0):
    return assess(f, locale, margin_floor=floor, runway_warn_days=warn)


class TestRefusals(unittest.TestCase):
    def test_every_missing_fact_is_named(self):
        r = go({})
        self.assertIsInstance(r, NotReady)
        self.assertFalse(r.ready)
        self.assertIn("time.hourly_floor", r.missing)
        self.assertIn("materials.cost_per_batch", r.missing)

    def test_no_margin_without_the_makers_own_time(self):
        # The industry's default mistake, made unrepresentable.
        f = facts()
        del f["time.hourly_floor"]
        r = go(f)
        self.assertIsInstance(r, NotReady)
        self.assertEqual(r.missing, ("time.hourly_floor",))

    def test_a_string_is_not_a_number(self):
        r = go(facts(**{"offer.price_current": "80"}))
        self.assertIsInstance(r, NotReady)

    def test_true_is_not_a_number(self):
        r = go(facts(**{"production.batch_size": True}))
        self.assertIsInstance(r, NotReady)

    def test_zero_batch_does_not_divide_by_zero(self):
        r = go(facts(**{"production.batch_size": 0}))
        self.assertIsInstance(r, NotReady)

    def test_unresolved_tax_refuses_rather_than_assuming(self):
        with self.assertRaises(LocaleError):
            go(facts(), locale=UNSET)


class TestArithmetic(unittest.TestCase):
    def test_cogs_is_materials_plus_labour(self):
        r = go(facts())
        self.assertIsInstance(r, Costing)
        self.assertAlmostEqual(r.materials_per_item, 12.0)   # 120 / 10
        self.assertAlmostEqual(r.labour_per_item, 37.5)      # 1.5h × 25
        self.assertAlmostEqual(r.cogs, 49.5)

    def test_margin_against_an_untaxed_price(self):
        r = go(facts())
        self.assertAlmostEqual(r.net_price, 80.0)
        self.assertAlmostEqual(r.margin, 30.5)
        self.assertAlmostEqual(r.margin_pct, 30.5 / 80.0)
        self.assertEqual(r.verdict, HEALTHY)

    def test_gst_registration_lowers_the_margin(self):
        # Same price, same costs — but a tenth of the price was never hers.
        plain = go(facts())
        taxed = go(facts(), locale=AU_GST)
        self.assertAlmostEqual(taxed.net_price, 80.0 / 1.1)
        self.assertLess(taxed.margin, plain.margin)

    def test_materials_only_pricing_is_caught_as_a_loss(self):
        # Priced at $40: comfortably above the $12 of materials, and a loss
        # once her hours are counted. This is the case the module exists for.
        r = go(facts(**{"offer.price_current": 40.0}))
        self.assertEqual(r.verdict, LOSS_MAKING)
        self.assertTrue(r.loses_money)
        self.assertLess(r.margin, 0)

    def test_thin_margin_is_below_floor_not_healthy(self):
        r = go(facts(**{"offer.price_current": 60.0}))
        self.assertEqual(r.verdict, BELOW_FLOOR)
        self.assertGreater(r.margin, 0)

    def test_floor_is_a_pack_parameter(self):
        self.assertEqual(go(facts(), floor=0.10).verdict, HEALTHY)
        self.assertEqual(go(facts(), floor=0.90).verdict, BELOW_FLOOR)


class TestProvenance(unittest.TestCase):
    def test_every_input_is_named(self):
        r = go(facts())
        for k in facts():
            self.assertIn(k, r.provenance)

    def test_runway_facts_only_appear_when_used(self):
        self.assertNotIn("stock.units_left", go(facts()).provenance)
        r = go(facts(**{"stock.units_left": 12.0, "sales.units_last_7d": 7.0}))
        self.assertIn("stock.units_left", r.provenance)


class TestRunway(unittest.TestCase):
    def test_runway_in_days(self):
        r = go(facts(**{"stock.units_left": 12.0, "sales.units_last_7d": 7.0}))
        self.assertAlmostEqual(r.runway_days, 12.0)
        self.assertFalse(r.low_stock)

    def test_low_stock_warns(self):
        r = go(facts(**{"stock.units_left": 3.0, "sales.units_last_7d": 7.0}))
        self.assertAlmostEqual(r.runway_days, 3.0)
        self.assertTrue(r.low_stock)

    def test_no_sales_is_not_infinite_runway(self):
        r = go(facts(**{"stock.units_left": 12.0, "sales.units_last_7d": 0.0}))
        self.assertIsNone(r.runway_days)
        self.assertFalse(r.low_stock)

    def test_margin_still_works_without_stock_facts(self):
        r = go(facts())
        self.assertEqual(r.verdict, HEALTHY)
        self.assertIsNone(r.runway_days)


class TestSuggestedPrice(unittest.TestCase):
    def test_price_that_hits_the_target(self):
        p = price_for_margin(49.5, 0.30, AU)
        self.assertAlmostEqual(p, 49.5 / 0.7)
        r = go(facts(**{"offer.price_current": p}))
        self.assertEqual(r.verdict, HEALTHY)
        self.assertAlmostEqual(r.margin_pct, 0.30)

    def test_gst_is_added_back_for_the_label(self):
        self.assertAlmostEqual(price_for_margin(49.5, 0.30, AU_GST),
                               (49.5 / 0.7) * 1.1)

    def test_impossible_target_is_refused(self):
        for bad in (1.0, 1.5, -0.1):
            with self.assertRaises(ValueError):
                price_for_margin(49.5, bad, AU)

    def test_unresolved_tax_refuses(self):
        with self.assertRaises(LocaleError):
            price_for_margin(49.5, 0.30, UNSET)


class TestRegistrationThreshold(unittest.TestCase):
    def test_below_threshold_stays_a_choice(self):
        self.assertFalse(AU.must_register_at(40_000))

    def test_at_threshold_it_stops_being_a_choice(self):
        self.assertTrue(AU.must_register_at(75_000))

    def test_already_registered_never_triggers(self):
        self.assertFalse(AU_GST.must_register_at(200_000))


if __name__ == "__main__":
    unittest.main()
