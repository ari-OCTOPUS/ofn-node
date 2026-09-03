"""Contract tests for observation_class (P1 complementary).

OBSERVATION requires evidence. Agent-reported cannot produce it.
Timeout and missing are UNKNOWN, not FALSE. Ready ≠ authorized.
Distinct from report mint/verify.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.observation_class import (
    INFERENCE, OBSERVATION, UNKNOWN, agent_reported_is_verified, as_bool,
    claims_immutable, classify_claim, grants_send, halt_blocks_observe,
    ready_is_authorized, unknown_is_false,
)


class ClassifyClaim(unittest.TestCase):
    def test_both_missing_is_unknown_not_false(self):
        self.assertEqual(classify_claim(None, None), UNKNOWN)
        self.assertNotEqual(classify_claim(None, None), "FALSE")

    def test_named_type_with_missing_evidence_is_unknown(self):
        self.assertEqual(classify_claim(OBSERVATION, None), UNKNOWN)
        self.assertEqual(classify_claim(INFERENCE, None), UNKNOWN)

    def test_observation_with_direct_evidence(self):
        self.assertEqual(
            classify_claim(OBSERVATION, ("direct_observation",)),
            OBSERVATION)

    def test_empty_observation_evidence_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_claim(OBSERVATION, ())

    def test_agent_reported_cannot_be_observation(self):
        with self.assertRaises(FailClosedError):
            classify_claim(OBSERVATION, ("agent_reported",))
        with self.assertRaises(FailClosedError):
            classify_claim(OBSERVATION, ("agent_report_only",))
        self.assertFalse(agent_reported_is_verified())

    def test_timeout_is_unknown_not_false(self):
        self.assertEqual(
            classify_claim(OBSERVATION, ("timeout",)), UNKNOWN)
        self.assertEqual(
            classify_claim(INFERENCE, ("timeout_unknown",)), UNKNOWN)
        self.assertNotEqual(
            classify_claim(INFERENCE, ("timeout",)), "FALSE")

    def test_inference_with_empty_evidence_stays_inference(self):
        self.assertEqual(classify_claim(INFERENCE, ()), INFERENCE)

    def test_unknown_named_type(self):
        self.assertEqual(classify_claim(UNKNOWN, ()), UNKNOWN)

    def test_unknown_claim_type_string_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_claim("GUESS", ("direct_observation",))

    def test_bool_int_claim_type_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_claim(True, ())
        with self.assertRaises(FailClosedError):
            classify_claim(1, ())

    def test_string_evidence_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_claim(INFERENCE, "direct_observation")

    def test_sealed_names_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "Send_Authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_claim(name, ())
                with self.assertRaises(FailClosedError):
                    classify_claim(INFERENCE, (name,))


class AsBool(unittest.TestCase):
    def test_observation_is_true(self):
        self.assertIs(as_bool(OBSERVATION), True)

    def test_unknown_fails_closed(self):
        with self.assertRaises(FailClosedError):
            as_bool(UNKNOWN)

    def test_inference_fails_closed_not_false(self):
        with self.assertRaises(FailClosedError):
            as_bool(INFERENCE)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_observe())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_claim).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["claim_type", "evidence"])


if __name__ == "__main__":
    unittest.main()
