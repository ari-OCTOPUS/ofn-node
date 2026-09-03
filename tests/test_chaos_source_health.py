"""Owner-absent chaos extras for source_health (independent of #82).

The seven blueprint scenarios live in test_chaos_owner_absent.py and
are owned by PR #82. This file adds the pins that file does not own:

  * a parked source cannot self-heal while the owner is absent
  * one source parking never parks a sibling
  * timeout remains UNKNOWN, not a fabricated FALSE
  * bool/float clocks cannot reopen a retry budget
"""

from __future__ import annotations

import unittest

from ofn.kernel import source_health as sh
from ofn.kernel.errors import FailClosedError


class ParkedSourceCannotSelfHeal(unittest.TestCase):
    def test_classify_and_index_agree_after_403_then_200(self):
        first = sh.classify_fetch(403)
        self.assertEqual(first, sh.PARKED)
        later = sh.classify_fetch(200, prior=first)
        self.assertEqual(later, sh.PARKED)
        idx = sh.ParkIndex()
        self.assertEqual(idx.note("feed-a", first), sh.PARKED)
        self.assertEqual(idx.note("feed-a", sh.OK), sh.PARKED)

    def test_exhausted_429_then_200_stays_parked(self):
        last = None
        for attempts in range(0, 8):
            last = sh.classify_fetch(429, attempts=attempts)
            if last == sh.PARKED:
                break
        else:
            self.fail("429 never parked")
        self.assertEqual(sh.classify_fetch(200, prior=last), sh.PARKED)


class SiblingSourceKeepsWorking(unittest.TestCase):
    def test_parking_one_feed_does_not_park_another(self):
        idx = sh.ParkIndex()
        idx.note("feed-dead", sh.classify_fetch(403))
        live = sh.classify_fetch(200)
        self.assertEqual(live, sh.OK)
        self.assertEqual(idx.note("feed-live", live), sh.OK)
        self.assertTrue(idx.is_parked("feed-dead"))
        self.assertFalse(idx.is_parked("feed-live"))


class TimeoutIsUnknownNotFalse(unittest.TestCase):
    def test_timeout_is_not_a_negative_witness(self):
        verdict = sh.classify_fetch(None, error=TimeoutError("arm A"))
        self.assertEqual(verdict, sh.UNKNOWN)
        self.assertNotEqual(verdict, "FALSE")
        self.assertNotEqual(verdict, sh.PARKED)
        self.assertNotEqual(verdict, sh.OK)


class BoolClockCannotReopenBudget(unittest.TestCase):
    def test_true_attempts_cannot_look_like_zero(self):
        # True < 3 is True in Python. That must not mint a retry.
        with self.assertRaises(FailClosedError):
            sh.classify_fetch(503, attempts=True)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_classification_does_not_grant_send(self):
        sh.classify_fetch(200)
        sh.classify_fetch(403)
        self.assertIs(sh.grants_send(), False)
        self.assertIs(sh.unpark_without_owner(), False)


if __name__ == "__main__":
    unittest.main()
