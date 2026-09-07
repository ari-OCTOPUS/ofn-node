"""Contract tests for burn_pin (P1 complementary).

A refused write, a ready state, a missing key, or a cited
receipt does not burn. Missing is None, not False. Later
disarm supersedes older authorization. Never grants a send.
Ready ≠ authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.burn_pin import (
    CAMPAIGN_ENVELOPE_READY,
    QUOTE_SENT,
    SEND_AUTHORIZED,
    BurnDecision,
    admit_burn,
    burns_on_missing,
    burns_on_ready,
    burns_on_receipt,
    burns_on_refuse,
    claims_immutable,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.key_class import KEY_BOUND


class AdmitBurn(unittest.TestCase):
    def test_receipt_cited_does_not_burn(self):
        decision = admit_burn(key="keep-me", outcome="receipt_cited")
        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertIs(decision.burned, False)
        self.assertIs(decision.allowed, False)
        self.assertEqual(decision.reason, "pin_does_not_burn")
        self.assertEqual(decision.key_class, KEY_BOUND)
        self.assertEqual(decision.outcome, "receipt_cited")
        self.assertFalse(decision.grants_send)

    def test_refused_does_not_burn(self):
        decision = admit_burn(key="keep-me", outcome="refused")
        assert decision is not None
        self.assertIs(decision.burned, False)
        self.assertEqual(decision.reason, "refuse_does_not_burn")
        self.assertFalse(burns_on_refuse())

    def test_ready_does_not_burn(self):
        decision = admit_burn(key="keep-me", outcome="ready")
        assert decision is not None
        self.assertIs(decision.burned, False)
        self.assertEqual(decision.reason, "ready_does_not_burn")
        self.assertFalse(burns_on_ready())

    def test_missing_outcome_token_does_not_burn(self):
        decision = admit_burn(key="keep-me", outcome="missing")
        assert decision is not None
        self.assertIs(decision.burned, False)
        self.assertEqual(decision.reason, "missing_key")
        self.assertFalse(burns_on_missing())

    def test_missing_key_is_none_not_false(self):
        self.assertIsNone(admit_burn(key=None, outcome="receipt_cited"))
        self.assertIsNone(admit_burn(key=None, outcome="refused"))
        self.assertIsNot(admit_burn(key=None, outcome="receipt_cited"), False)

    def test_missing_outcome_is_none_not_false(self):
        self.assertIsNone(admit_burn(key="keep-me", outcome=None))
        self.assertIsNone(admit_burn(key=None, outcome=None))
        self.assertIsNot(admit_burn(key="keep-me", outcome=None), False)

    def test_send_authorized_key_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_burn(key="send_authorized", outcome="receipt_cited")
        with self.assertRaises(FailClosedError):
            admit_burn(key="quote_sent", outcome="refused")
        with self.assertRaises(FailClosedError):
            admit_burn(key="campaign_envelope_ready", outcome="ready")

    def test_sealed_outcome_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_burn(key="keep-me", outcome="send_authorized")
        with self.assertRaises(FailClosedError):
            admit_burn(key="keep-me", outcome="quote_sent")
        with self.assertRaises(FailClosedError):
            admit_burn(key="keep-me", outcome="campaign_envelope_ready")

    def test_unknown_outcome_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_burn(key="keep-me", outcome="almost_burned")

    def test_empty_key_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_burn(key="  ", outcome="receipt_cited")

    def test_bool_key_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_burn(key=True, outcome="receipt_cited")

    def test_bool_outcome_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_burn(key="keep-me", outcome=True)


class ConstructorLocks(unittest.TestCase):
    def test_cannot_construct_a_burn(self):
        with self.assertRaises(FailClosedError):
            BurnDecision(
                burned=True,
                allowed=False,
                reason="pin_does_not_burn",
                key_class=KEY_BOUND,
                outcome="receipt_cited",
            )

    def test_cannot_construct_an_allow(self):
        with self.assertRaises(FailClosedError):
            BurnDecision(
                burned=False,
                allowed=True,
                reason="pin_does_not_burn",
                key_class=KEY_BOUND,
                outcome="receipt_cited",
            )

    def test_cannot_grant_send(self):
        with self.assertRaises(FailClosedError):
            BurnDecision(
                burned=False,
                allowed=False,
                reason="pin_does_not_burn",
                key_class=KEY_BOUND,
                outcome="receipt_cited",
                grants_send=True,
            )


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_later_disarm_supersedes_older_auth(self):
        self.assertTrue(later_disarm_supersedes())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_receipt_cite_does_not_burn(self):
        self.assertFalse(burns_on_receipt())

    def test_quote_sent_stays_distinct(self):
        self.assertNotEqual(CAMPAIGN_ENVELOPE_READY, SEND_AUTHORIZED)
        self.assertNotEqual(SEND_AUTHORIZED, QUOTE_SENT)

    def test_admit_has_no_halt_or_now_parameter(self):
        params = inspect.signature(admit_burn).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertNotIn("resend", params)
        self.assertNotIn("send_authorized", params)
        self.assertEqual(list(params), ["key", "outcome"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_burn_pin(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("burn_pin", source)
        self.assertNotIn("key_class", source)


if __name__ == "__main__":
    unittest.main()
