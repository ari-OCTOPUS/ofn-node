"""Owner-absent chaos for observation_class / inference_class.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify, inference
never becomes observation, and a recorded class never becomes a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.inference_class import (
    grants_send, halt_blocks_infer, promote, timeout_proves_concurrent_write,
)
from ofn.kernel.observation_class import (
    INFERENCE, OBSERVATION, UNKNOWN, classify_claim, halt_blocks_observe,
)


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(classify_claim(None, None), UNKNOWN)
        self.assertNotEqual(classify_claim(None, None), "FALSE")
        self.assertIsNone(promote(None, OBSERVATION))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_evidence_is_unknown(self):
        self.assertEqual(classify_claim(OBSERVATION, ("timeout",)), UNKNOWN)
        self.assertFalse(timeout_proves_concurrent_write())


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_infer())
        self.assertEqual(
            classify_claim(INFERENCE, ()), INFERENCE)
        params = inspect.signature(classify_claim).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_refused_promotion_does_not_grant_send(self):
        with self.assertRaises(FailClosedError):
            promote(INFERENCE, OBSERVATION)
        self.assertFalse(grants_send())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_sealed_names_cannot_promote(self):
        with self.assertRaises(FailClosedError):
            promote("campaign_envelope_ready", "send_authorized")
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_same_class_recorded_cross_class_refused(self):
        self.assertEqual(promote(INFERENCE, INFERENCE), INFERENCE)
        with self.assertRaises(FailClosedError):
            promote(UNKNOWN, OBSERVATION)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic(self):
        a = classify_claim(OBSERVATION, ("direct_observation",))
        b = classify_claim(OBSERVATION, ("direct_observation",))
        self.assertEqual(a, b)
        self.assertEqual(a, OBSERVATION)


if __name__ == "__main__":
    unittest.main()
