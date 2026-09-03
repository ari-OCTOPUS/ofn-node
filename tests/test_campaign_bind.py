"""Contract tests for campaign_bind (P1 complementary).

campaign_envelope_ready binds as CAMPAIGN_READY. Missing is
UNKNOWN, not FALSE. send_authorized / quote_sent refuse.
Ready ≠ authorized. Not wired into the run store. Distinct
from campaign_envelope.py and #143 typed_event.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.campaign_bind import (
    CAMPAIGN_READY,
    CampaignBind,
    UNKNOWN,
    bind_ready,
    claims_immutable,
    classify_state,
    grants_send,
    halt_blocks_bind,
    promotes_ready_to_send,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
)
from ofn.kernel.errors import FailClosedError


class ClassifyState(unittest.TestCase):
    def test_none_is_unknown_not_false(self):
        self.assertEqual(classify_state(None), UNKNOWN)
        self.assertNotEqual(classify_state(None), "FALSE")

    def test_canonical_ready_is_campaign_ready(self):
        self.assertEqual(
            classify_state("campaign_envelope_ready"), CAMPAIGN_READY)

    def test_hyphen_and_case_aliases(self):
        self.assertEqual(
            classify_state("campaign-envelope-ready"), CAMPAIGN_READY)
        self.assertEqual(
            classify_state("Campaign_Envelope_Ready"), CAMPAIGN_READY)

    def test_send_authorized_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_state("send_authorized")
        with self.assertRaises(FailClosedError):
            classify_state("Send_Authorized")
        with self.assertRaises(FailClosedError):
            classify_state("send-authorized")

    def test_quote_sent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_state("quote_sent")

    def test_unknown_string_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_state("almost_ready")

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_state("  ")

    def test_bool_int_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_state(True)
        with self.assertRaises(FailClosedError):
            classify_state(1)


class BindReady(unittest.TestCase):
    def test_bind_records_canonical_name(self):
        bound = bind_ready("campaign-envelope-ready")
        self.assertIsInstance(bound, CampaignBind)
        self.assertEqual(bound.state, "campaign_envelope_ready")
        self.assertEqual(bound.state_class, CAMPAIGN_READY)

    def test_frozen_cannot_retcon_to_send(self):
        bound = bind_ready("campaign_envelope_ready")
        with self.assertRaises(Exception):
            bound.state = "send_authorized"  # type: ignore[misc]

    def test_missing_on_explicit_bind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_ready(None)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None))

    def test_try_bind_success(self):
        bound = try_bind("campaign_envelope_ready")
        self.assertIsNotNone(bound)
        assert bound is not None
        self.assertEqual(bound.state_class, CAMPAIGN_READY)

    def test_try_bind_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_bind("send_authorized")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_bind(self):
        self.assertFalse(halt_blocks_bind())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_state).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["value"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_these_modules(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("campaign_bind", source)
        self.assertNotIn("send_fence", source)


if __name__ == "__main__":
    unittest.main()
