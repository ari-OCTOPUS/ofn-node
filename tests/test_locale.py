"""The locale contract.

The point of these is not that the fields parse. It is that an unimplemented
market is *refused* and an unanswered question stays unanswered — because
both failure modes are silent by nature, and both end with a wrong number in
front of a partner who has no way to know it is wrong.
"""

import unittest

from ofn.adapters.packloader import SUPPORTED_LOCALES, load_pack, spec_from_mapping
from ofn.kernel.domain import UNRESOLVED, Currency, Locale, LocaleError, PackSpec
from ofn.kernel.errors import PackError


def base(**over):
    d = {"tenant": "ziman", "capacity_units_per_week": 6}
    d.update(over)
    return d


class TestCurrency(unittest.TestCase):
    def test_formats_to_the_locale_decimals(self):
        self.assertEqual(Currency("AUD", "$", 2).format(1234.5), "$1,234.50")

    def test_rejects_a_non_currency_code(self):
        for bad in ("aud", "AUDX", ""):
            with self.assertRaises(ValueError):
                Currency(bad, "$", 2)


class TestUnresolvedFailsClosed(unittest.TestCase):
    """An unanswered locale field must raise, never return a default."""

    def setUp(self):
        self.loc = Locale("en-AU", Currency("AUD", "$", 2))

    def test_timezone_unresolved_raises(self):
        with self.assertRaises(LocaleError):
            self.loc.require_timezone()

    def test_tax_status_unresolved_raises(self):
        with self.assertRaises(LocaleError):
            self.loc.require_tax()

    def test_not_registered_is_an_answer_not_an_absence(self):
        # Zero tax because the owner said so is a fact. It must not raise,
        # and it must not be confused with "nobody has said yet".
        loc = Locale("en-AU", Currency("AUD", "$", 2),
                     tax_status="not_registered", tax_rate=0.10)
        self.assertEqual(loc.require_tax(), (0.0, "inclusive"))

    def test_registered_applies_the_rate(self):
        loc = Locale("en-AU", Currency("AUD", "$", 2),
                     tax_status="registered", tax_rate=0.10)
        self.assertEqual(loc.require_tax(), (0.10, "inclusive"))

    def test_resolved_timezone_is_returned(self):
        loc = Locale("en-AU", Currency("AUD", "$", 2),
                     timezone="Australia/Sydney")
        self.assertEqual(loc.require_timezone(), "Australia/Sydney")


class TestLoaderRefusesUnsupported(unittest.TestCase):
    def test_unknown_locale_is_refused_not_defaulted(self):
        with self.assertRaises(PackError) as cm:
            spec_from_mapping(base(locale={"id": "fa-IR"}))
        self.assertIn("unsupported_locale", str(cm.exception))

    def test_error_names_what_is_implemented(self):
        with self.assertRaises(PackError) as cm:
            spec_from_mapping(base(locale={"id": "en-NZ"}))
        self.assertIn("en-AU", str(cm.exception))

    def test_currency_may_not_disagree_with_the_locale(self):
        with self.assertRaises(PackError):
            spec_from_mapping(base(
                locale={"id": "en-AU", "currency": {"code": "EUR"}}))

    def test_absent_locale_block_is_the_named_default(self):
        spec = spec_from_mapping(base())
        self.assertEqual(spec.locale.id, "en-AU")
        self.assertEqual(spec.locale.currency.code, "AUD")
        # …and the default still leaves the owner's questions unanswered.
        self.assertEqual(spec.locale.tax_status, UNRESOLVED)
        self.assertEqual(spec.locale.timezone, UNRESOLVED)

    def test_bad_tax_status_is_refused(self):
        with self.assertRaises(PackError):
            spec_from_mapping(base(locale={"id": "en-AU",
                                           "tax": {"status": "maybe"}}))

    def test_bad_tax_pricing_is_refused(self):
        with self.assertRaises(PackError):
            spec_from_mapping(base(locale={"id": "en-AU",
                                           "tax": {"pricing": "sometimes"}}))

    def test_rails_and_platforms_must_be_lists(self):
        with self.assertRaises(PackError):
            spec_from_mapping(base(locale={"id": "en-AU",
                                           "payment_rails": "stripe"}))

    def test_every_supported_locale_carries_a_law(self):
        # A market with no legal entry means someone added a currency and
        # called it a locale.
        for name, cfg in SUPPORTED_LOCALES.items():
            with self.subTest(locale=name):
                self.assertTrue(cfg["legal"])


class TestZimanPack(unittest.TestCase):
    def test_ziman_is_en_au_with_both_questions_still_open(self):
        spec = load_pack("packs/ziman.yaml")
        self.assertEqual(spec.locale.id, "en-AU")
        self.assertEqual(spec.locale.currency.code, "AUD")
        self.assertEqual(spec.locale.timezone, UNRESOLVED)
        self.assertEqual(spec.locale.tax_status, UNRESOLVED)

    def test_ziman_claims_no_sales_channel_yet(self):
        # She is not selling anywhere yet. An empty list is the honest state;
        # a populated one would mean somebody assumed an integration.
        spec = load_pack("packs/ziman.yaml")
        self.assertEqual(spec.locale.platforms, ())
        self.assertEqual(spec.locale.payment_rails, ())


class TestDefaultSpec(unittest.TestCase):
    def test_packspec_default_locale_is_a_real_locale(self):
        self.assertIn(PackSpec(tenant="ziman", capacity_units_per_week=1)
                      .locale.id, SUPPORTED_LOCALES)


if __name__ == "__main__":
    unittest.main()
