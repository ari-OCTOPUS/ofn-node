"""source_health pins — exact-int clock, park latch, ready ≠ authorized.

Complementary to tests/test_chaos_owner_absent.py (owned by #82).
This file owns the new pins; it does not rewrite the seven scenarios.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel import source_health as sh
from ofn.kernel.errors import FailClosedError


class ExactIntPins(unittest.TestCase):
    def test_bool_attempts_is_not_an_int(self):
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(429, attempts=True)
        with self.assertRaises(FailClosedError):
            sh.backoff_delays(attempts=True)

    def test_bool_status_is_not_an_int(self):
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(True)
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(False)

    def test_float_status_and_attempts_fail_closed(self):
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(200.0)
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(429, attempts=1.5)
        with self.assertRaises(FailClosedError):
            sh.backoff_delays(attempts=3.0, cap_s=60)

    def test_string_status_is_not_coerced(self):
        with self.assertRaises(FailClosedError):
            sh.classify_fetch("200")
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(429, attempts="0")

    def test_negative_attempts_fail_closed(self):
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(429, attempts=-1)
        with self.assertRaises(FailClosedError):
            sh.backoff_delays(attempts=-1)

    def test_existing_int_paths_unchanged(self):
        self.assertEqual(sh.classify_fetch(None), sh.UNKNOWN)
        self.assertEqual(sh.classify_fetch(403), sh.PARKED)
        self.assertEqual(sh.classify_fetch(429, attempts=0),
                         sh.RETRY_AFTER_BACKOFF)
        self.assertEqual(
            sh.classify_fetch(429, attempts=sh.MAX_BACKOFF_ATTEMPTS),
            sh.PARKED)
        self.assertEqual(sh.backoff_delays(), (1, 2, 4))


class UnknownIsNotFalse(unittest.TestCase):
    def test_401_and_404_are_unknown_not_false(self):
        for code in (401, 404, 418, 0, 999):
            with self.subTest(code=code):
                verdict = sh.classify_fetch(code)
                self.assertEqual(verdict, sh.UNKNOWN)
                self.assertNotEqual(verdict, "FALSE")

    def test_timeout_error_is_unknown_even_with_200(self):
        self.assertEqual(
            sh.classify_fetch(200, error=TimeoutError("deadline")),
            sh.UNKNOWN)
        self.assertNotEqual(
            sh.classify_fetch(200, error=TimeoutError("deadline")),
            sh.OK)


class PriorParkLatch(unittest.TestCase):
    def test_prior_parked_stays_parked_on_200(self):
        self.assertEqual(
            sh.classify_fetch(200, prior=sh.PARKED),
            sh.PARKED)

    def test_prior_parked_beats_error_and_none(self):
        self.assertEqual(
            sh.classify_fetch(None, error=TimeoutError("x"), prior=sh.PARKED),
            sh.PARKED)
        self.assertEqual(
            sh.classify_fetch(None, prior=sh.PARKED),
            sh.PARKED)

    def test_prior_ok_does_not_override_this_fetch(self):
        self.assertEqual(sh.classify_fetch(403, prior=sh.OK), sh.PARKED)
        self.assertEqual(sh.classify_fetch(200, prior=sh.OK), sh.OK)

    def test_unknown_prior_fails_closed(self):
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(200, prior="CLEAN")
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(200, prior="FALSE")


class ParkIndexLatch(unittest.TestCase):
    def test_second_ok_after_park_stays_parked(self):
        idx = sh.ParkIndex()
        self.assertEqual(idx.note("src-a", sh.OK), sh.OK)
        self.assertFalse(idx.is_parked("src-a"))
        self.assertEqual(idx.note("src-a", sh.PARKED), sh.PARKED)
        self.assertTrue(idx.is_parked("src-a"))
        self.assertEqual(idx.note("src-a", sh.OK), sh.PARKED)
        self.assertEqual(idx.note("src-a", sh.UNKNOWN), sh.PARKED)

    def test_sibling_source_is_independent(self):
        idx = sh.ParkIndex()
        idx.note("dead", sh.PARKED)
        self.assertEqual(idx.note("live", sh.OK), sh.OK)
        self.assertFalse(idx.is_parked("live"))

    def test_unpark_is_refused(self):
        idx = sh.ParkIndex()
        idx.note("dead", sh.PARKED)
        with self.assertRaises(FailClosedError):
            idx.unpark("dead")
        self.assertTrue(idx.is_parked("dead"))

    def test_empty_or_sealed_source_id_fails_closed(self):
        idx = sh.ParkIndex()
        for bad in ("", "  ", "send_authorized", "quote_sent",
                    "campaign_envelope_ready", "send-authorized"):
            with self.subTest(source_id=bad):
                with self.assertRaises(FailClosedError):
                    idx.note(bad, sh.PARKED)
                with self.assertRaises(FailClosedError):
                    idx.is_parked(bad)

    def test_unknown_verdict_fails_closed(self):
        idx = sh.ParkIndex()
        with self.assertRaises(FailClosedError):
            idx.note("src-a", "FALSE")


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertIs(sh.grants_send(), False)
        self.assertIs(sh.halt_blocks_classify(), False)
        self.assertIs(sh.unpark_without_owner(), False)

    def test_classify_fetch_has_no_send_or_resend_parameter(self):
        names = set(inspect.signature(sh.classify_fetch).parameters)
        self.assertNotIn("resend", names)
        self.assertNotIn("send_authorized", names)
        self.assertNotIn("quote_sent", names)
        self.assertIn("prior", names)
        self.assertIn("attempts", names)

    def test_backoff_delays_has_no_send_parameter(self):
        names = set(inspect.signature(sh.backoff_delays).parameters)
        self.assertEqual(names, {"attempts", "cap_s"})


if __name__ == "__main__":
    unittest.main()
