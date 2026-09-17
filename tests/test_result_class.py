"""Contract tests for result_class (P1 complementary).

Four-state labels only. Missing is None, not False.
ok=True with sent=False fails closed. Never grants a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.result_class import (
    FAILED,
    PASSED,
    REJECTED,
    UNKNOWN,
    claims_immutable,
    classify_result,
    grants_send,
    halt_blocks_classify,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)


class ClassifyResult(unittest.TestCase):
    def test_four_states(self):
        self.assertEqual(classify_result("passed"), PASSED)
        self.assertEqual(classify_result("rejected"), REJECTED)
        self.assertEqual(classify_result("failed"), FAILED)
        self.assertEqual(classify_result("unknown"), UNKNOWN)

    def test_hyphen_and_case_fold(self):
        self.assertEqual(classify_result("Passed"), PASSED)
        self.assertEqual(classify_result("FAILED"), FAILED)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_result(None))
        self.assertIsNot(classify_result(None), False)

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_result("")
        with self.assertRaises(FailClosedError):
            classify_result("   ")

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_result(True)

    def test_unknown_label_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_result("almost_passed")

    def test_send_names_fail_closed(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "Send_Authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_result(name)

    def test_ok_true_sent_false_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_result("passed", sent=False, ok=True)

    def test_sent_true_requires_passed(self):
        with self.assertRaises(FailClosedError):
            classify_result("rejected", sent=True)
        with self.assertRaises(FailClosedError):
            classify_result("failed", sent=True)
        self.assertEqual(classify_result("passed", sent=True), PASSED)

    def test_sent_true_still_does_not_grant_send(self):
        self.assertEqual(classify_result("passed", sent=True, ok=True), PASSED)
        self.assertFalse(grants_send())

    def test_missing_with_sent_true_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_result(None, sent=True)

    def test_non_bool_sent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_result("passed", sent="yes")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_result).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)


if __name__ == "__main__":
    unittest.main()
