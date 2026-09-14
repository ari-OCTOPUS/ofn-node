"""Regression lock for owner_digest's mobile detector.

The detector once required the country code and the leading mobile digit to
be contiguous (`\\+?614\\d{2}`), so a real ESR Group mobile written as
"+61 415 784 898" (space after 61) was not recognised and the account fell
to office-only in the owner's call list. This pins the formats that must and
must not count as a mobile, so that regression cannot return silently.

New standalone file - it does not modify owner_digest.py, only imports and
exercises its public predicate.
"""
from __future__ import annotations

import importlib.util
import pathlib
import unittest

_OD_PATH = pathlib.Path(__file__).resolve().parent.parent / "tools" / "owner_digest.py"
_spec = importlib.util.spec_from_file_location("owner_digest_under_test", _OD_PATH)
owner_digest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(owner_digest)


class TestMobileDetection(unittest.TestCase):
    def test_spaced_country_code_is_a_mobile(self):
        # The exact case that fell to office-only before the fix.
        self.assertTrue(owner_digest._has_mobile("M:+61 415 784 898"))
        self.assertTrue(owner_digest._has_mobile("+61 429 479 141"))

    def test_trunk_zero_forms_still_work(self):
        self.assertTrue(owner_digest._has_mobile("0415 784 898"))
        self.assertTrue(owner_digest._has_mobile("0499 038 901"))
        self.assertTrue(owner_digest._has_mobile("0512 345 678"))   # 05xx range

    def test_contiguous_and_bracketed_country_code(self):
        self.assertTrue(owner_digest._has_mobile("+61415784898"))
        self.assertTrue(owner_digest._has_mobile("(+61) 415 784 898"))
        self.assertTrue(owner_digest._has_mobile("(61) 415 784 898"))

    def test_office_and_service_numbers_are_not_mobiles(self):
        self.assertFalse(owner_digest._has_mobile("1300 123 456"))
        self.assertFalse(owner_digest._has_mobile("1800 123 456"))
        self.assertFalse(owner_digest._has_mobile("(02) 9186 4727"))
        self.assertFalse(owner_digest._has_mobile("+61 2 9186 4727"))
        self.assertFalse(owner_digest._has_mobile(""))

    def test_office_line_next_to_a_mobile_does_not_hide_the_mobile(self):
        # ESR Group's real stored value: office and mobile in one field.
        esr = ("Fergus Adamson (GM Property Services NSW) "
               "M:+61 415 784 898 O:+61 2 9186 4727 fergus.adamson@esr.com")
        self.assertTrue(owner_digest._has_mobile(esr))
        self.assertEqual(owner_digest._extract_mobiles(esr), ["+61 415 784 898"])

    def test_landline_containing_a_415_run_is_not_a_false_mobile(self):
        # No 61/0 immediately before the [45] digit, so it must not match.
        self.assertFalse(owner_digest._has_mobile("02 9415 7848"))


if __name__ == "__main__":
    unittest.main()
