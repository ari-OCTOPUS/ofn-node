"""Contract tests for scoped_authz (P1 complementary).

Authorization is scoped only when explicit, newer than the
later hold, and non-wildcard. Missing is UNKNOWN, not FALSE.
Stale after a later hold is AUTHZ_STALE, not a send.
send_authorized / quote_sent / campaign_envelope_ready refuse
as epochs or scopes. Ready ≠ authorized. Never grants a send.
Not wired into the run store. Distinct from later_hold,
send_fence, and campaign_bind.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.scoped_authz import (
    AUTHZ_SCOPED,
    AUTHZ_STALE,
    ScopedAuthz,
    UNKNOWN,
    claims_immutable,
    classify_authz,
    grants_send,
    halt_blocks_pin,
    later_hold_supersedes_older,
    pin_allows_effect,
    pin_scoped,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    scoped_is_send,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)


class ClassifyAuthz(unittest.TestCase):
    def test_none_authz_is_unknown_not_false(self):
        self.assertEqual(classify_authz(None, 10, "lead"), UNKNOWN)
        self.assertNotEqual(classify_authz(None, 10, "lead"), "FALSE")

    def test_none_hold_is_unknown_not_false(self):
        self.assertEqual(classify_authz(20, None, "lead"), UNKNOWN)

    def test_none_scope_is_unknown_not_false(self):
        self.assertEqual(classify_authz(20, 10, None), UNKNOWN)
        self.assertNotEqual(classify_authz(20, 10, None), AUTHZ_STALE)

    def test_all_missing_is_unknown(self):
        self.assertEqual(classify_authz(None, None, None), UNKNOWN)

    def test_newer_scoped_is_scoped(self):
        self.assertEqual(classify_authz(20, 10, "lead"), AUTHZ_SCOPED)

    def test_hyphen_and_case_scope_folds(self):
        self.assertEqual(
            classify_authz(20, 10, "Lead-NSW"), AUTHZ_SCOPED)

    def test_stale_after_later_hold(self):
        self.assertEqual(classify_authz(10, 20, "lead"), AUTHZ_STALE)

    def test_same_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_authz(10, 10, "lead")

    def test_empty_scope_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "  ")

    def test_wildcard_scope_fails_closed(self):
        for wild in ("*", "all", "any", "wildcard", "0.0.0.0", "::"):
            with self.subTest(scope=wild):
                with self.assertRaises(FailClosedError):
                    classify_authz(20, 10, wild)

    def test_bool_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_authz(True, 10, "lead")
        with self.assertRaises(FailClosedError):
            classify_authz(20, False, "lead")

    def test_bool_scope_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, True)

    def test_send_authorized_as_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_authz("send_authorized", 10, "lead")
        with self.assertRaises(FailClosedError):
            classify_authz(20, "send_authorized", "lead")

    def test_quote_sent_as_scope_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "quote_sent")

    def test_ready_as_scope_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "campaign_envelope_ready")
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "campaign-envelope-ready")

    def test_bad_scope_token_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "../lead")
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "lead nsw")
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "9lead")


class PinAllowsAndPin(unittest.TestCase):
    def test_scoped_class_does_not_allow_effect(self):
        self.assertFalse(pin_allows_effect(AUTHZ_SCOPED))
        self.assertFalse(pin_allows_effect("authz_scoped"))

    def test_stale_and_unknown_do_not_allow(self):
        self.assertFalse(pin_allows_effect(AUTHZ_STALE))
        self.assertFalse(pin_allows_effect(UNKNOWN))
        self.assertFalse(pin_allows_effect(None))

    def test_sealed_class_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_allows_effect("send_authorized")
        with self.assertRaises(FailClosedError):
            pin_allows_effect("quote_sent")

    def test_unknown_class_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_allows_effect("almost_scoped")

    def test_pin_records_canonical_scoped(self):
        pinned = pin_scoped(20, 10, "Lead-NSW")
        self.assertIsInstance(pinned, ScopedAuthz)
        self.assertEqual(pinned.authz_epoch, 20)
        self.assertEqual(pinned.hold_epoch, 10)
        self.assertEqual(pinned.scope, "lead_nsw")
        self.assertEqual(pinned.authz_class, AUTHZ_SCOPED)

    def test_frozen_cannot_retcon_to_send(self):
        pinned = pin_scoped(20, 10, "lead")
        with self.assertRaises(Exception):
            pinned.authz_class = "send_authorized"  # type: ignore[misc]

    def test_stale_pin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_scoped(10, 20, "lead")

    def test_missing_on_explicit_pin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_scoped(None, 10, "lead")
        with self.assertRaises(FailClosedError):
            pin_scoped(20, None, "lead")
        with self.assertRaises(FailClosedError):
            pin_scoped(20, 10, None)

    def test_try_pin_missing_is_none(self):
        self.assertIsNone(try_pin(None, 10, "lead"))
        self.assertIsNone(try_pin(20, None, "lead"))
        self.assertIsNone(try_pin(20, 10, None))

    def test_try_pin_success(self):
        pinned = try_pin(20, 10, "lead")
        self.assertIsNotNone(pinned)
        assert pinned is not None
        self.assertEqual(pinned.authz_class, AUTHZ_SCOPED)

    def test_try_pin_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_pin(10, 10, "lead")
        with self.assertRaises(FailClosedError):
            try_pin(20, 10, "*")
        with self.assertRaises(FailClosedError):
            try_pin(10, 20, "lead")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())
        self.assertFalse(scoped_is_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_later_hold_supersedes_older_is_true(self):
        self.assertTrue(later_hold_supersedes_older())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_not_wired_flag(self):
        self.assertFalse(wires_into_run_store())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_authz).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(
            list(params), ["authz_epoch", "hold_epoch", "scope"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_these_modules(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("scoped_authz", source)
        self.assertNotIn("later_hold", source)

    def test_later_hold_does_not_import_scoped_authz(self):
        import ofn.kernel.later_hold as later_hold
        source = inspect.getsource(later_hold)
        self.assertNotIn("scoped_authz", source)
        self.assertNotIn("AUTHZ_SCOPED", source)


if __name__ == "__main__":
    unittest.main()
