"""Contract tests for inference_class (P1 complementary).

INFERENCE cannot become OBSERVATION. Missing is None, not False.
Timeout does not prove concurrent writing. Ready ≠ send.
Not wired into the run store. Distinct from report mint/verify.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.inference_class import (
    claims_immutable, grants_send, halt_blocks_infer, promote,
    proposal_is_execution, ready_is_authorized, ready_to_send,
    timeout_proves_concurrent_write,
)
from ofn.kernel.observation_class import INFERENCE, OBSERVATION, UNKNOWN


class PromoteFence(unittest.TestCase):
    def test_same_class_is_idempotent(self):
        self.assertEqual(promote(INFERENCE, INFERENCE), INFERENCE)
        self.assertEqual(promote(OBSERVATION, OBSERVATION), OBSERVATION)
        self.assertEqual(promote(UNKNOWN, UNKNOWN), UNKNOWN)

    def test_inference_to_observation_refused(self):
        with self.assertRaises(FailClosedError):
            promote(INFERENCE, OBSERVATION)

    def test_unknown_to_observation_refused(self):
        with self.assertRaises(FailClosedError):
            promote(UNKNOWN, OBSERVATION)

    def test_observation_to_inference_refused(self):
        with self.assertRaises(FailClosedError):
            promote(OBSERVATION, INFERENCE)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(promote(None, OBSERVATION))
        self.assertIsNone(promote(INFERENCE, None))
        self.assertIsNone(promote(None, None))
        self.assertIsNot(promote(None, OBSERVATION), False)

    def test_sealed_ready_to_send_refused(self):
        with self.assertRaises(FailClosedError):
            promote("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            promote("send_authorized", "quote_sent")
        self.assertFalse(ready_to_send())

    def test_bool_class_fails_closed(self):
        with self.assertRaises(FailClosedError):
            promote(True, OBSERVATION)
        with self.assertRaises(FailClosedError):
            promote(INFERENCE, 1)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_fence(self):
        self.assertFalse(halt_blocks_infer())

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_promote_has_no_halt_parameter(self):
        params = inspect.signature(promote).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["from_class", "to_class"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_these_modules(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("observation_class", source)
        self.assertNotIn("inference_class", source)


if __name__ == "__main__":
    unittest.main()
