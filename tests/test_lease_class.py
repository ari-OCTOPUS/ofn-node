"""Contract tests for lease_class (P1 complementary).

A lease_id binds one run. Missing is UNKNOWN, not FALSE.
steal never admitted. Ready ≠ authorized. Never grants a send.
Not wired into the run store. Distinct from later_hold,
scoped_authz, and deadline_window.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.lease_class import (
    LEASE_ADMIT,
    LEASE_EXPIRE,
    LEASE_ID_RE,
    LEASE_INSPECT,
    LEASE_RENEW,
    LeaseClass,
    UNKNOWN,
    admit_send,
    claims_immutable,
    classify_lease,
    grants_send,
    halt_blocks_classify,
    halt_blocks_expire,
    halt_blocks_inspect,
    is_start,
    later_disarm_supersedes,
    may_proceed,
    pin_lease,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    require_lease_id,
    steals_lease,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_expired,
    unknown_is_false,
    wires_into_run_store,
)

_LEASE = "lse-0123456789abcdef"
_RUN = "run-1780000000-leaseaaaaaa"


class RequireLeaseId(unittest.TestCase):
    def test_valid_token(self):
        self.assertEqual(require_lease_id(_LEASE), _LEASE)
        self.assertTrue(LEASE_ID_RE.match(_LEASE))

    def test_malformed_fails_closed(self):
        with self.assertRaises(FailClosedError):
            require_lease_id("lse-SHORT")
        with self.assertRaises(FailClosedError):
            require_lease_id("nce-0123456789abcdef")
        with self.assertRaises(FailClosedError):
            require_lease_id("LSE-0123456789ABCDEF")

    def test_sealed_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            require_lease_id("send_authorized")
        with self.assertRaises(FailClosedError):
            require_lease_id("campaign_envelope_ready")

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            require_lease_id(True)


class ClassifyLease(unittest.TestCase):
    def test_none_lease_is_unknown_not_false(self):
        self.assertEqual(classify_lease(None, _RUN, "admit"), UNKNOWN)
        self.assertNotEqual(classify_lease(None, _RUN, "admit"), "FALSE")

    def test_none_run_is_unknown(self):
        self.assertEqual(classify_lease(_LEASE, None, "inspect"), UNKNOWN)

    def test_none_action_is_unknown(self):
        self.assertEqual(classify_lease(_LEASE, _RUN, None), UNKNOWN)

    def test_all_missing_is_unknown(self):
        self.assertEqual(classify_lease(None, None, None), UNKNOWN)

    def test_admit_inspect_renew_expire(self):
        self.assertEqual(classify_lease(_LEASE, _RUN, "admit"), LEASE_ADMIT)
        self.assertEqual(classify_lease(_LEASE, _RUN, "inspect"), LEASE_INSPECT)
        self.assertEqual(classify_lease(_LEASE, _RUN, "renew"), LEASE_RENEW)
        self.assertEqual(classify_lease(_LEASE, _RUN, "expire"), LEASE_EXPIRE)

    def test_hyphen_alias_action(self):
        self.assertEqual(classify_lease(_LEASE, _RUN, "ADMIT"), LEASE_ADMIT)

    def test_steal_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, _RUN, "steal")

    def test_unknown_action_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, _RUN, "publish")

    def test_empty_action_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, _RUN, "")

    def test_bool_action_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, _RUN, True)

    def test_malformed_lease_with_present_others_fails(self):
        with self.assertRaises(FailClosedError):
            classify_lease("lse-xx", _RUN, "admit")

    def test_malformed_run_fails(self):
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, "run-1-x", "admit")

    def test_send_authorized_as_lease_fails(self):
        with self.assertRaises(FailClosedError):
            classify_lease("send_authorized", _RUN, "admit")

    def test_ready_as_action_fails(self):
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, _RUN, "campaign_envelope_ready")

    def test_quote_sent_as_run_fails(self):
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, "quote_sent", "inspect")

    def test_present_bad_with_missing_sibling_still_fails(self):
        with self.assertRaises(FailClosedError):
            classify_lease("send-authorized", None, "admit")
        with self.assertRaises(FailClosedError):
            classify_lease(None, _RUN, "steal")


class StartAndProceed(unittest.TestCase):
    def test_admit_and_renew_are_starts(self):
        self.assertTrue(is_start(LEASE_ADMIT))
        self.assertTrue(is_start(LEASE_RENEW))
        self.assertFalse(is_start(LEASE_INSPECT))
        self.assertFalse(is_start(LEASE_EXPIRE))
        self.assertFalse(is_start(UNKNOWN))
        self.assertFalse(is_start(None))

    def test_halt_refuses_starts(self):
        self.assertIs(may_proceed(LEASE_ADMIT, True), False)
        self.assertIs(may_proceed(LEASE_RENEW, True), False)
        self.assertIs(may_proceed(LEASE_ADMIT, False), True)
        self.assertIs(may_proceed(LEASE_RENEW, False), True)

    def test_inspect_expire_continue_under_halt(self):
        self.assertIs(may_proceed(LEASE_INSPECT, True), True)
        self.assertIs(may_proceed(LEASE_EXPIRE, True), True)

    def test_unknown_proceed_is_none_not_false(self):
        self.assertIsNone(may_proceed(UNKNOWN, False))
        self.assertIsNone(may_proceed(None, True))
        self.assertIsNot(may_proceed(None, False), False)

    def test_halted_must_be_bool(self):
        with self.assertRaises(FailClosedError):
            may_proceed(LEASE_ADMIT, "yes")
        with self.assertRaises(FailClosedError):
            may_proceed(LEASE_ADMIT, 1)

    def test_admit_send_never_true(self):
        self.assertIs(admit_send(LEASE_ADMIT), False)
        self.assertIs(admit_send(LEASE_RENEW), False)
        self.assertIs(admit_send(LEASE_INSPECT), False)
        self.assertIsNone(admit_send(None))
        self.assertIsNone(admit_send(UNKNOWN))
        self.assertIsNot(admit_send(LEASE_ADMIT), True)

    def test_sealed_klass_fails(self):
        with self.assertRaises(FailClosedError):
            admit_send("send_authorized")
        with self.assertRaises(FailClosedError):
            is_start("quote_sent")


class PinLease(unittest.TestCase):
    def test_pin_records_canonical(self):
        pinned = pin_lease(_LEASE, _RUN, "renew")
        self.assertIsInstance(pinned, LeaseClass)
        self.assertEqual(pinned.lease_id, _LEASE)
        self.assertEqual(pinned.run_id, _RUN)
        self.assertEqual(pinned.lease_class, LEASE_RENEW)

    def test_frozen_cannot_retcon_to_send(self):
        pinned = pin_lease(_LEASE, _RUN, "admit")
        with self.assertRaises(Exception):
            pinned.lease_class = "send_authorized"  # type: ignore[misc]

    def test_missing_on_explicit_pin_fails(self):
        with self.assertRaises(FailClosedError):
            pin_lease(None, _RUN, "admit")

    def test_try_pin_missing_is_none(self):
        self.assertIsNone(try_pin(None, _RUN, "admit"))
        self.assertIsNone(try_pin(_LEASE, None, "inspect"))
        self.assertIsNone(try_pin(_LEASE, _RUN, None))

    def test_try_pin_success(self):
        pinned = try_pin(_LEASE, _RUN, "inspect")
        self.assertIsNotNone(pinned)
        assert pinned is not None
        self.assertEqual(pinned.lease_class, LEASE_INSPECT)

    def test_try_pin_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_pin(_LEASE, _RUN, "steal")
        with self.assertRaises(FailClosedError):
            try_pin("send_authorized", _RUN, "admit")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())
        self.assertFalse(steals_lease())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_inspect())
        self.assertFalse(halt_blocks_expire())

    def test_unknown_is_not_false_or_expired(self):
        self.assertFalse(unknown_is_false())
        self.assertFalse(unknown_is_expired())

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

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_lease).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["lease_id", "run_id", "action"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_these_modules(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("lease_class", source)
        self.assertNotIn("renew_pin", source)

    def test_deadline_window_stays_distinct(self):
        import ofn.kernel.deadline_window as deadline_window
        source = inspect.getsource(deadline_window)
        self.assertNotIn("classify_lease", source)
        self.assertNotIn("LEASE_ADMIT", source)

    def test_later_hold_stays_distinct(self):
        import ofn.kernel.later_hold as later_hold
        source = inspect.getsource(later_hold)
        self.assertNotIn("classify_lease", source)
        self.assertNotIn("lse-", source)


if __name__ == "__main__":
    unittest.main()
