"""Contract tests for later_hold (P1 complementary).

A later hold supersedes an older authorization epoch.
Missing is UNKNOWN, not FALSE. Same epoch fails closed.
send_authorized / quote_sent / campaign_envelope_ready refuse
as epochs. Ready ≠ authorized. Never grants a send.
Not wired into the run store. Distinct from send_fence,
campaign_bind, phase_wall, and flag_freeze.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.later_hold import (
    LATER_HOLD,
    LaterHold,
    OLDER_HOLD,
    UNKNOWN,
    admit_send_after_hold,
    claims_immutable,
    classify_hold,
    grants_send,
    halt_blocks_classify,
    later_supersedes_older,
    pin_later,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    supersedes,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)


class ClassifyHold(unittest.TestCase):
    def test_none_hold_is_unknown_not_false(self):
        self.assertEqual(classify_hold(None, 10), UNKNOWN)
        self.assertNotEqual(classify_hold(None, 10), "FALSE")

    def test_none_authz_is_unknown_not_false(self):
        self.assertEqual(classify_hold(20, None), UNKNOWN)
        self.assertNotEqual(classify_hold(20, None), "FALSE")

    def test_both_missing_is_unknown(self):
        self.assertEqual(classify_hold(None, None), UNKNOWN)

    def test_later_hold_when_hold_greater(self):
        self.assertEqual(classify_hold(20, 10), LATER_HOLD)

    def test_older_hold_when_hold_lesser(self):
        self.assertEqual(classify_hold(10, 20), OLDER_HOLD)

    def test_zero_hold_against_later_authz_is_older(self):
        self.assertEqual(classify_hold(0, 1), OLDER_HOLD)

    def test_zero_authz_against_later_hold_is_later(self):
        self.assertEqual(classify_hold(1, 0), LATER_HOLD)

    def test_same_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_hold(10, 10)
        with self.assertRaises(FailClosedError):
            classify_hold(0, 0)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_hold(True, 10)
        with self.assertRaises(FailClosedError):
            classify_hold(10, False)

    def test_float_str_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_hold(10.5, 10)
        with self.assertRaises(FailClosedError):
            classify_hold("10", 9)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_hold(-1, 0)

    def test_send_authorized_as_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_hold("send_authorized", 10)
        with self.assertRaises(FailClosedError):
            classify_hold(10, "send-authorized")

    def test_quote_sent_as_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_hold("quote_sent", 10)

    def test_ready_as_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_hold("campaign_envelope_ready", 10)
        with self.assertRaises(FailClosedError):
            classify_hold(10, "Campaign-Envelope-Ready")


class SupersedesAndAdmit(unittest.TestCase):
    def test_later_supersedes_is_true(self):
        self.assertIs(supersedes(20, 10), True)

    def test_older_does_not_supersede(self):
        self.assertIs(supersedes(10, 20), False)

    def test_missing_supersedes_is_none_not_false(self):
        self.assertIsNone(supersedes(None, 10))
        self.assertIsNone(supersedes(20, None))
        self.assertIsNot(supersedes(None, None), False)

    def test_admit_later_is_false_not_unknown(self):
        self.assertIs(admit_send_after_hold(20, 10), False)

    def test_admit_older_is_false(self):
        self.assertIs(admit_send_after_hold(10, 20), False)

    def test_admit_missing_is_none_not_false(self):
        self.assertIsNone(admit_send_after_hold(None, 10))
        self.assertIsNot(admit_send_after_hold(None, 10), False)

    def test_admit_never_returns_true(self):
        self.assertIsNot(admit_send_after_hold(99, 1), True)
        self.assertIsNot(admit_send_after_hold(1, 99), True)

    def test_same_epoch_admit_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_send_after_hold(5, 5)

    def test_sealed_name_admit_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_send_after_hold("quote_sent", 1)


class PinLater(unittest.TestCase):
    def test_pin_records_canonical_later(self):
        pinned = pin_later(20, 10)
        self.assertIsInstance(pinned, LaterHold)
        self.assertEqual(pinned.hold_epoch, 20)
        self.assertEqual(pinned.authz_epoch, 10)
        self.assertEqual(pinned.hold_class, LATER_HOLD)

    def test_frozen_cannot_retcon_to_send(self):
        pinned = pin_later(20, 10)
        with self.assertRaises(Exception):
            pinned.hold_class = "send_authorized"  # type: ignore[misc]

    def test_older_pin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_later(10, 20)

    def test_missing_on_explicit_pin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_later(None, 10)
        with self.assertRaises(FailClosedError):
            pin_later(20, None)

    def test_try_pin_missing_is_none(self):
        self.assertIsNone(try_pin(None, 10))
        self.assertIsNone(try_pin(20, None))

    def test_try_pin_success(self):
        pinned = try_pin(20, 10)
        self.assertIsNotNone(pinned)
        assert pinned is not None
        self.assertEqual(pinned.hold_class, LATER_HOLD)

    def test_try_pin_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_pin(10, 10)
        with self.assertRaises(FailClosedError):
            try_pin("send_authorized", 1)
        with self.assertRaises(FailClosedError):
            try_pin(10, 20)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_later_supersedes_older_is_true(self):
        self.assertTrue(later_supersedes_older())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_not_wired_flag(self):
        self.assertFalse(wires_into_run_store())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_hold).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["hold_epoch", "authz_epoch"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_these_modules(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("later_hold", source)
        self.assertNotIn("scoped_authz", source)

    def test_send_fence_stays_distinct(self):
        import ofn.kernel.send_fence as send_fence
        source = inspect.getsource(send_fence)
        self.assertNotIn("classify_hold", source)
        self.assertNotIn("pin_later", source)

    def test_campaign_bind_stays_distinct(self):
        import ofn.kernel.campaign_bind as campaign_bind
        source = inspect.getsource(campaign_bind)
        self.assertNotIn("classify_hold", source)
        self.assertNotIn("LaterHold", source)


if __name__ == "__main__":
    unittest.main()
