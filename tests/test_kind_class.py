"""Contract tests for kind_class (P1 complementary).

Closed roles only. Missing is None, not False.
Timeout is UNKNOWN. Never grants a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    CLAIM_CREATED,
    EXECUTION_RECEIPT,
    POLICY_DECISION,
    PROPOSAL_CREATED,
    RUN_CLOSED,
    RUN_CREATED,
    RUN_REJECTED,
    TOOL_INVOKED,
)
from ofn.kernel.kind_class import (
    CLOSE,
    DEBIT,
    INFLIGHT,
    PROPOSAL,
    REJECT,
    START,
    claims_immutable,
    classify_role,
    grants_send,
    halt_blocks_classify,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)


class ClassifyRole(unittest.TestCase):
    def test_closed_roles(self):
        self.assertEqual(classify_role(RUN_CREATED), START)
        self.assertEqual(classify_role(CLAIM_CREATED), INFLIGHT)
        self.assertEqual(classify_role(POLICY_DECISION), INFLIGHT)
        self.assertEqual(classify_role(TOOL_INVOKED), INFLIGHT)
        self.assertEqual(classify_role(EXECUTION_RECEIPT), INFLIGHT)
        self.assertEqual(classify_role(BUDGET_DEBIT), DEBIT)
        self.assertEqual(classify_role(RUN_CLOSED), CLOSE)
        self.assertEqual(classify_role(RUN_REJECTED), REJECT)
        self.assertEqual(classify_role(PROPOSAL_CREATED), PROPOSAL)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_role(None))
        self.assertIsNot(classify_role(None), False)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_role(RUN_CREATED, timeout=True))
        self.assertIsNot(classify_role(RUN_CREATED, timeout=True), False)
        self.assertFalse(timeout_proves_concurrent_write())

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_role(RUN_CREATED, timeout="yes")

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_role("")
        with self.assertRaises(FailClosedError):
            classify_role("   ")

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_role(True)

    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_role("ALMOST_CREATED")

    def test_hyphen_kind_is_not_folded_into_a_grant(self):
        with self.assertRaises(FailClosedError):
            classify_role("run-created")

    def test_send_names_fail_closed(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "Send_Authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_role(name)

    def test_proposal_is_not_execution(self):
        self.assertEqual(classify_role(PROPOSAL_CREATED), PROPOSAL)
        self.assertNotEqual(classify_role(PROPOSAL_CREATED), EXECUTION_RECEIPT)
        self.assertFalse(proposal_is_execution())

    def test_debit_is_not_a_send(self):
        self.assertEqual(classify_role(BUDGET_DEBIT), DEBIT)
        self.assertFalse(grants_send())


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

    def test_does_not_mint(self):
        self.assertFalse(mints_run_id())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_role).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)


if __name__ == "__main__":
    unittest.main()
