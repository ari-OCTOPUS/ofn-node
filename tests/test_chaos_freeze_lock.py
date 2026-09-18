"""Owner-absent chaos — freeze-class / lock-pin composition.

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the freeze-lock layer: no
store, no run_id mint, no fabricated witness. HALT is not a
classify parameter. One arm's timeout cannot rewrite another
arm's lock. Recovery is pinning LF_MATCH and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.freeze_class import (
    CRLF_CHECKOUT,
    LF_MATCH,
    UNKNOWN,
    classify_digest,
    grants_send,
    halt_blocks_classify,
    ready_is_authorized,
)
from ofn.kernel.lock_pin import pin_lock

_LF = "5c0c16732b60b20f2bb8483955c770574e8d99c217ecc6e9d7a0536bca1be1d6"
_CRLF = "7e99cb35f8970a5069521f36f72855948b56f2a8d9182326edd2db61d4d9c901"
_OTHER = "b" * 64


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_missing_digest_is_unknown_not_false(self):
        d = classify_digest(observed=None, lock=_LF)
        self.assertEqual(d.kind, UNKNOWN)
        self.assertNotEqual(d.kind, "FALSE")

    def test_unknown_kind_pin_is_not_false(self):
        pin = pin_lock(UNKNOWN)
        self.assertTrue(pin.unknown)
        self.assertNotEqual(pin.kind, "FALSE")


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_rewrite_sibling_lock(self):
        timed = classify_digest(
            observed=_LF, lock=_LF, error=TimeoutError("arm A"))
        self.assertEqual(timed.kind, UNKNOWN)
        sibling = classify_digest(observed=_LF, lock=_LF, known_crlf=_CRLF)
        self.assertEqual(sibling.kind, LF_MATCH)
        self.assertFalse(sibling.grants_send)
        self.assertTrue(pin_lock(sibling.kind).frozen_ok)

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        d = classify_digest(observed=_LF, lock=_LF)
        self.assertEqual(d.kind, LF_MATCH)
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_classify_distinct_pairs(self):
        decisions = [
            classify_digest(observed=obs, lock=_LF, known_crlf=_CRLF)
            for obs in (_LF, _CRLF, _OTHER)
        ]
        self.assertEqual(len(decisions), 3)
        self.assertEqual(
            [d.kind for d in decisions],
            [LF_MATCH, CRLF_CHECKOUT, "MISMATCH"],
        )
        for d in decisions:
            self.assertFalse(d.grants_send)


class Scenario4DuplicateClassifyStillNotASend(unittest.TestCase):
    def test_second_identical_classify_is_not_a_send(self):
        first = classify_digest(observed=_LF, lock=_LF)
        second = classify_digest(observed=_LF, lock=_LF)
        self.assertEqual(first, second)
        self.assertFalse(first.grants_send)
        self.assertFalse(grants_send())
        self.assertTrue(pin_lock(first.kind).frozen_ok)


class Scenario5SealedNameStopsThatArmOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_classify_continues(self):
        with self.assertRaises(FailClosedError):
            classify_digest(observed="send_authorized", lock=_LF)
        sibling = classify_digest(observed=_LF, lock=_LF)
        self.assertEqual(sibling.kind, LF_MATCH)
        self.assertFalse(sibling.grants_send)


class Scenario6RecoveryIsReversibleAndNotASend(unittest.TestCase):
    def test_pin_lf_match_is_not_a_send(self):
        pin = pin_lock(LF_MATCH)
        self.assertTrue(pin.frozen_ok)
        self.assertFalse(pin.grants_send)
        self.assertFalse(ready_is_authorized())
        self.assertFalse(halt_blocks_classify())


class Scenario7CrlfArtefactDoesNotUnfreeze(unittest.TestCase):
    def test_crlf_pin_is_artefact_not_a_rewrite(self):
        d = classify_digest(observed=_CRLF, lock=_LF, known_crlf=_CRLF)
        pin = pin_lock(d.kind)
        self.assertTrue(pin.artefact)
        self.assertFalse(pin.frozen_ok)
        self.assertFalse(pin.grants_send)
        sibling = pin_lock(LF_MATCH)
        self.assertTrue(sibling.frozen_ok)
