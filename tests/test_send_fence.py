"""Contract tests for send_fence (P1 complementary).

Ready cannot become authorized. Authorized cannot become
quote_sent. Missing is None, not False. Later disarm
supersedes older authorization. Never grants a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.send_fence import (
    CAMPAIGN_ENVELOPE_READY,
    QUOTE_SENT,
    SEND_AUTHORIZED,
    admit_send,
    claims_immutable,
    grants_send,
    halt_blocks_fence,
    later_disarm_supersedes,
    promote,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
)


class AdmitSend(unittest.TestCase):
    def test_ready_is_false_not_unknown(self):
        self.assertIs(admit_send("campaign_envelope_ready"), False)
        self.assertIs(admit_send("campaign-envelope-ready"), False)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(admit_send(None))
        self.assertIsNot(admit_send(None), False)

    def test_send_authorized_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_send("send_authorized")
        with self.assertRaises(FailClosedError):
            admit_send("quote_sent")

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_send(True)


class PromoteFence(unittest.TestCase):
    def test_same_ready_is_idempotent(self):
        self.assertEqual(
            promote("campaign_envelope_ready", "campaign-envelope-ready"),
            CAMPAIGN_ENVELOPE_READY)

    def test_ready_to_authorized_refused(self):
        with self.assertRaises(FailClosedError):
            promote("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready_is_authorized())

    def test_authorized_to_quote_sent_refused(self):
        with self.assertRaises(FailClosedError):
            promote("send_authorized", "quote_sent")

    def test_ready_to_quote_sent_refused(self):
        with self.assertRaises(FailClosedError):
            promote("campaign_envelope_ready", "quote_sent")

    def test_missing_is_none_not_false(self):
        self.assertIsNone(promote(None, "send_authorized"))
        self.assertIsNone(promote("campaign_envelope_ready", None))
        self.assertIsNone(promote(None, None))
        self.assertIsNot(promote(None, SEND_AUTHORIZED), False)

    def test_same_send_name_restates_but_does_not_grant(self):
        self.assertEqual(
            promote("send_authorized", "Send_Authorized"),
            SEND_AUTHORIZED)
        self.assertFalse(grants_send())

    def test_unknown_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            promote("almost_ready", "send_authorized")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_later_disarm_supersedes_older_auth(self):
        self.assertTrue(later_disarm_supersedes())

    def test_halt_does_not_block_fence(self):
        self.assertFalse(halt_blocks_fence())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_quote_sent_stays_distinct(self):
        self.assertNotEqual(CAMPAIGN_ENVELOPE_READY, SEND_AUTHORIZED)
        self.assertNotEqual(SEND_AUTHORIZED, QUOTE_SENT)

    def test_promote_has_no_halt_or_now_parameter(self):
        params = inspect.signature(promote).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["from_state", "to_state"])


if __name__ == "__main__":
    unittest.main()
