"""Contract tests for renew_pin (P1 complementary).

First live renew only. already_renewed and lease_collision fail
closed. Missing window is UNKNOWN, not FALSE and not expired.
Equal epoch is expired (closed). Ready ≠ authorized.
peek does not write. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.renew_pin import (
    LEASE_EXPIRED,
    LEASE_LIVE,
    RenewPin,
    UNKNOWN,
    claims_immutable,
    classify_window,
    expired_is_false,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    live_is_send,
    peek_window,
    peek_writes,
    pin_renew,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_expired,
    unknown_is_false,
    wires_into_run_store,
)

_LEASE = "lse-0123456789abcdef"
_LEASE_B = "lse-fedcba9876543210"
_RUN = "run-1780000000-leaseaaaaaa"
_RUN_B = "run-1780000000-leasebbbbbb"


class ClassifyWindow(unittest.TestCase):
    def test_none_expire_is_unknown_not_false(self):
        self.assertEqual(classify_window(None, 10), UNKNOWN)
        self.assertNotEqual(classify_window(None, 10), "FALSE")
        self.assertNotEqual(classify_window(None, 10), LEASE_EXPIRED)

    def test_none_now_is_unknown_not_expired(self):
        self.assertEqual(classify_window(20, None), UNKNOWN)
        self.assertNotEqual(classify_window(20, None), LEASE_EXPIRED)

    def test_both_missing_is_unknown(self):
        self.assertEqual(classify_window(None, None), UNKNOWN)

    def test_live_when_now_before_expire(self):
        self.assertEqual(classify_window(20, 10), LEASE_LIVE)

    def test_expired_when_now_after(self):
        self.assertEqual(classify_window(10, 20), LEASE_EXPIRED)

    def test_equal_is_expired_closed(self):
        self.assertEqual(classify_window(10, 10), LEASE_EXPIRED)
        self.assertEqual(classify_window(0, 0), LEASE_EXPIRED)

    def test_zero_expire_against_later_now_is_expired(self):
        self.assertEqual(classify_window(0, 1), LEASE_EXPIRED)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_window(True, 10)
        with self.assertRaises(FailClosedError):
            classify_window(20, False)

    def test_float_str_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_window(10.5, 10)
        with self.assertRaises(FailClosedError):
            classify_window("20", 10)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_window(-1, 0)

    def test_sealed_name_as_epoch_fails(self):
        with self.assertRaises(FailClosedError):
            classify_window("send_authorized", 10)
        with self.assertRaises(FailClosedError):
            classify_window(20, "campaign_envelope_ready")

    def test_peek_matches_classify_and_does_not_write(self):
        self.assertEqual(peek_window(20, 10), classify_window(20, 10))
        self.assertEqual(peek_window(None, 10), UNKNOWN)
        self.assertFalse(peek_writes())


class PinRenew(unittest.TestCase):
    def test_pin_records_canonical_live(self):
        pinned = pin_renew(_LEASE, _RUN, 20, 10)
        self.assertIsInstance(pinned, RenewPin)
        self.assertEqual(pinned.lease_id, _LEASE)
        self.assertEqual(pinned.run_id, _RUN)
        self.assertEqual(pinned.expire_epoch, 20)
        self.assertEqual(pinned.now_epoch, 10)
        self.assertEqual(pinned.window_class, LEASE_LIVE)

    def test_frozen_cannot_retcon_to_send(self):
        pinned = pin_renew(_LEASE, _RUN, 20, 10)
        with self.assertRaises(Exception):
            pinned.window_class = "send_authorized"  # type: ignore[misc]

    def test_expired_pin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_renew(_LEASE, _RUN, 10, 20)
        with self.assertRaises(FailClosedError):
            pin_renew(_LEASE, _RUN, 10, 10)

    def test_already_renewed_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_renew(_LEASE, _RUN, 20, 10, prior_renew=True)

    def test_collision_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_renew(
                _LEASE, _RUN, 20, 10, bound_run_id=_RUN_B,
            )

    def test_same_bound_run_is_first(self):
        pinned = pin_renew(_LEASE, _RUN, 20, 10, bound_run_id=_RUN)
        self.assertEqual(pinned.run_id, _RUN)

    def test_missing_on_explicit_pin_fails(self):
        with self.assertRaises(FailClosedError):
            pin_renew(None, _RUN, 20, 10)
        with self.assertRaises(FailClosedError):
            pin_renew(_LEASE, _RUN, None, 10)

    def test_try_pin_missing_is_none(self):
        self.assertIsNone(try_pin(None, _RUN, 20, 10))
        self.assertIsNone(try_pin(_LEASE, None, 20, 10))
        self.assertIsNone(try_pin(_LEASE, _RUN, None, 10))
        self.assertIsNone(try_pin(_LEASE, _RUN, 20, None))
        self.assertIsNot(try_pin(None, _RUN, 20, 10), False)

    def test_try_pin_success(self):
        pinned = try_pin(_LEASE_B, _RUN_B, 50, 1)
        self.assertIsNotNone(pinned)
        assert pinned is not None
        self.assertEqual(pinned.window_class, LEASE_LIVE)

    def test_try_pin_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_pin(_LEASE, _RUN, 20, 10, prior_renew=True)
        with self.assertRaises(FailClosedError):
            try_pin("send_authorized", _RUN, 20, 10)
        with self.assertRaises(FailClosedError):
            try_pin(_LEASE, _RUN, 5, 9)
        with self.assertRaises(FailClosedError):
            try_pin(_LEASE, _RUN, 20, 10, bound_run_id=_RUN_B)

    def test_prior_renew_must_be_bool(self):
        with self.assertRaises(FailClosedError):
            pin_renew(_LEASE, _RUN, 20, 10, prior_renew="yes")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())
        self.assertFalse(live_is_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_unknown_is_not_false_or_expired(self):
        self.assertFalse(unknown_is_false())
        self.assertFalse(unknown_is_expired())
        self.assertFalse(expired_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_later_disarm_holds(self):
        self.assertTrue(later_disarm_supersedes())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_not_wired_flag(self):
        self.assertFalse(wires_into_run_store())

    def test_classify_has_no_halt_or_now_name(self):
        params = inspect.signature(classify_window).parameters
        self.assertNotIn("halted", params)
        self.assertEqual(list(params), ["expire_epoch", "now_epoch"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_renew_pin(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("renew_pin", source)
        self.assertNotIn("pin_renew", source)

    def test_deadline_window_does_not_pin_renew(self):
        import ofn.kernel.deadline_window as deadline_window
        source = inspect.getsource(deadline_window)
        self.assertNotIn("pin_renew", source)
        self.assertNotIn("LEASE_LIVE", source)


if __name__ == "__main__":
    unittest.main()
