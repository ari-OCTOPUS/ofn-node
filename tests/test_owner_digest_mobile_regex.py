"""Regression test for the owner_digest mobile classifier.

The bug this locks: the old `_MOBILE_RE` required "614" contiguous, so a real
mobile written "+61 415 784 898" (a space after the country code) was never
recognised and the account fell to office-only in the owner's call list. Six
mobile-reachable decision-makers were invisible because of it — among them
ESR Group's Fergus Adamson (+61 415 784 898) and Brix FM ((+61) 416 551 123).

These cases are mutation-checked against the old pattern: run them against
`(?:0[45]\\d{2}|\\+?614\\d{2})...` and the spaced/bracketed forms go red, which
is exactly the regression we are guarding.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import owner_digest  # noqa: E402


class TestMobileRegex(unittest.TestCase):
    def test_spaced_country_code_is_a_mobile(self):
        """The exact form that fell through: '+61 415 784 898' (ESR Group)."""
        self.assertTrue(owner_digest._has_mobile("+61 415 784 898"))

    def test_bracketed_country_code_is_a_mobile(self):
        """'(+61) 416 551 123' (Brix FM) — bracket form seen in the wild."""
        self.assertTrue(owner_digest._has_mobile("(+61) 416 551 123"))

    def test_trunk_zero_mobile_still_works(self):
        """The form that always worked must keep working."""
        self.assertTrue(owner_digest._has_mobile("0415 784 898"))
        self.assertTrue(owner_digest._has_mobile("0400 549 724"))

    def test_05_range_mobile(self):
        self.assertTrue(owner_digest._has_mobile("0512 345 678"))

    def test_1300_is_not_a_mobile(self):
        self.assertFalse(owner_digest._has_mobile("1300 123 456"))

    def test_landline_is_not_a_mobile(self):
        """A Sydney landline that happens to contain '415' must not match."""
        self.assertFalse(owner_digest._has_mobile("+61 2 9186 4727"))
        self.assertFalse(owner_digest._has_mobile("02 9415 7848"))

    def test_empty_is_not_a_mobile(self):
        self.assertFalse(owner_digest._has_mobile(""))
        self.assertFalse(owner_digest._has_mobile(None))

    def test_mobile_inside_a_busy_contact_string(self):
        """Real contact_channel values pack several fields together."""
        s = "(02) 9715 3999 | enquiries@x.com.au | Andrew Smith 0409 600 471"
        self.assertTrue(owner_digest._has_mobile(s))
        self.assertIn("0409 600 471", "".join(owner_digest._extract_mobiles(s)))


if __name__ == "__main__":
    unittest.main()
