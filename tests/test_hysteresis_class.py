"""Contract tests for hysteresis_class (P1 complementary).

A two-threshold band latches HIGH/LOW with hysteresis.
Missing is UNKNOWN, not FALSE. A point band fails closed.
send_authorized / quote_sent / campaign_envelope_ready refuse
as values or priors. Ready ≠ authorized. Never grants a send.
Not wired into the run store. Distinct from later_hold,
scoped_authz, token_ceiling, and deadline_window.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.hysteresis_class import (
    ABOVE,
    BELOW,
    FALL,
    HIGH,
    HOLD,
    HysteresisClass,
    INSIDE,
    LOW,
    RISE,
    UNKNOWN,
    admit_send_after_edge,
    claims_immutable,
    classify_band,
    classify_edge,
    classify_prior,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    latch_band,
    later_hold_supersedes_older,
    pin_edge,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)


class ClassifyBand(unittest.TestCase):
    def test_none_value_is_unknown_not_false(self):
        self.assertEqual(classify_band(None, 0, 10), UNKNOWN)
        self.assertNotEqual(classify_band(None, 0, 10), "FALSE")

    def test_none_low_is_unknown_not_false(self):
        self.assertEqual(classify_band(5, None, 10), UNKNOWN)
        self.assertNotEqual(classify_band(5, None, 10), BELOW)

    def test_none_high_is_unknown_not_false(self):
        self.assertEqual(classify_band(5, 0, None), UNKNOWN)

    def test_all_missing_is_unknown(self):
        self.assertEqual(classify_band(None, None, None), UNKNOWN)

    def test_below_inside_above(self):
        self.assertEqual(classify_band(-1, 0, 10), BELOW)
        self.assertEqual(classify_band(5, 0, 10), INSIDE)
        self.assertEqual(classify_band(11, 0, 10), ABOVE)

    def test_bounds_are_inside(self):
        self.assertEqual(classify_band(0, 0, 10), INSIDE)
        self.assertEqual(classify_band(10, 0, 10), INSIDE)

    def test_point_band_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_band(5, 10, 10)

    def test_inverted_band_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_band(5, 10, 0)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_band(True, 0, 10)
        with self.assertRaises(FailClosedError):
            classify_band(5, False, 10)

    def test_float_str_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_band(5.5, 0, 10)
        with self.assertRaises(FailClosedError):
            classify_band("5", 0, 10)

    def test_send_authorized_as_value_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_band("send_authorized", 0, 10)

    def test_quote_sent_as_low_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_band(5, "quote_sent", 10)

    def test_ready_as_high_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_band(5, 0, "campaign_envelope_ready")
        with self.assertRaises(FailClosedError):
            classify_band(5, 0, "Campaign-Envelope-Ready")


class ClassifyPriorAndLatch(unittest.TestCase):
    def test_none_prior_is_unknown_not_false(self):
        self.assertEqual(classify_prior(None), UNKNOWN)
        self.assertNotEqual(classify_prior(None), "FALSE")

    def test_known_priors(self):
        self.assertEqual(classify_prior("high"), HIGH)
        self.assertEqual(classify_prior("LOW"), LOW)
        self.assertEqual(classify_prior("inside"), INSIDE)

    def test_empty_prior_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_prior("  ")

    def test_unknown_prior_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_prior("maybe")

    def test_bool_prior_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_prior(True)

    def test_sealed_prior_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_prior("send_authorized")

    def test_high_holds_above_low(self):
        self.assertEqual(latch_band(HIGH, 1, 0, 10), HIGH)
        self.assertEqual(latch_band(HIGH, 9, 0, 10), HIGH)

    def test_high_falls_at_low(self):
        self.assertEqual(latch_band(HIGH, 0, 0, 10), LOW)
        self.assertEqual(latch_band(HIGH, -1, 0, 10), LOW)

    def test_low_holds_below_high(self):
        self.assertEqual(latch_band(LOW, 9, 0, 10), LOW)
        self.assertEqual(latch_band(LOW, 1, 0, 10), LOW)

    def test_low_rises_at_high(self):
        self.assertEqual(latch_band(LOW, 10, 0, 10), HIGH)
        self.assertEqual(latch_band(LOW, 11, 0, 10), HIGH)

    def test_inside_rises_and_falls(self):
        self.assertEqual(latch_band(INSIDE, 10, 0, 10), HIGH)
        self.assertEqual(latch_band(INSIDE, 0, 0, 10), LOW)
        self.assertEqual(latch_band(INSIDE, 5, 0, 10), INSIDE)

    def test_missing_latch_is_none_not_false(self):
        self.assertIsNone(latch_band(None, 5, 0, 10))
        self.assertIsNone(latch_band(HIGH, None, 0, 10))
        self.assertIsNot(latch_band(None, 5, 0, 10), False)


class ClassifyEdge(unittest.TestCase):
    def test_missing_is_unknown_not_false(self):
        self.assertEqual(classify_edge(None, 11, 0, 10), UNKNOWN)
        self.assertNotEqual(classify_edge(None, 11, 0, 10), "FALSE")
        self.assertEqual(classify_edge(LOW, None, 0, 10), UNKNOWN)

    def test_rise_from_low(self):
        self.assertEqual(classify_edge(LOW, 10, 0, 10), RISE)

    def test_fall_from_high(self):
        self.assertEqual(classify_edge(HIGH, 0, 0, 10), FALL)

    def test_hold_inside_hysteresis(self):
        self.assertEqual(classify_edge(HIGH, 5, 0, 10), HOLD)
        self.assertEqual(classify_edge(LOW, 5, 0, 10), HOLD)

    def test_inside_to_inside_is_hold(self):
        self.assertEqual(classify_edge(INSIDE, 5, 0, 10), HOLD)

    def test_inside_to_high_is_rise(self):
        self.assertEqual(classify_edge(INSIDE, 10, 0, 10), RISE)

    def test_inside_to_low_is_fall(self):
        self.assertEqual(classify_edge(INSIDE, 0, 0, 10), FALL)

    def test_point_band_edge_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_edge(HIGH, 5, 3, 3)

    def test_sealed_value_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_edge(HIGH, "quote_sent", 0, 10)


class AdmitAndPin(unittest.TestCase):
    def test_admit_rise_is_false_not_unknown(self):
        self.assertIs(admit_send_after_edge(LOW, 10, 0, 10), False)

    def test_admit_hold_is_false(self):
        self.assertIs(admit_send_after_edge(HIGH, 5, 0, 10), False)

    def test_admit_missing_is_none_not_false(self):
        self.assertIsNone(admit_send_after_edge(None, 10, 0, 10))
        self.assertIsNot(admit_send_after_edge(None, 10, 0, 10), False)

    def test_admit_never_returns_true(self):
        self.assertIsNot(admit_send_after_edge(LOW, 11, 0, 10), True)
        self.assertIsNot(admit_send_after_edge(HIGH, -1, 0, 10), True)

    def test_pin_records_rise(self):
        pinned = pin_edge(LOW, 10, 0, 10)
        self.assertIsInstance(pinned, HysteresisClass)
        self.assertEqual(pinned.edge_class, RISE)
        self.assertEqual(pinned.latched, HIGH)
        self.assertEqual(pinned.prior, LOW)

    def test_pin_records_fall(self):
        pinned = pin_edge(HIGH, 0, 0, 10)
        self.assertEqual(pinned.edge_class, FALL)
        self.assertEqual(pinned.latched, LOW)

    def test_frozen_cannot_retcon_to_send(self):
        pinned = pin_edge(LOW, 10, 0, 10)
        with self.assertRaises(Exception):
            pinned.edge_class = "send_authorized"  # type: ignore[misc]

    def test_hold_pin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_edge(HIGH, 5, 0, 10)

    def test_missing_on_explicit_pin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_edge(None, 10, 0, 10)
        with self.assertRaises(FailClosedError):
            pin_edge(LOW, None, 0, 10)

    def test_try_pin_missing_is_none(self):
        self.assertIsNone(try_pin(None, 10, 0, 10))
        self.assertIsNone(try_pin(LOW, None, 0, 10))

    def test_try_pin_success(self):
        pinned = try_pin(LOW, 10, 0, 10)
        self.assertIsNotNone(pinned)
        assert pinned is not None
        self.assertEqual(pinned.edge_class, RISE)

    def test_try_pin_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_pin(HIGH, 5, 0, 10)
        with self.assertRaises(FailClosedError):
            try_pin("send_authorized", 10, 0, 10)


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

    def test_later_hold_still_supersedes(self):
        self.assertTrue(later_hold_supersedes_older())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_writer(self):
        self.assertEqual(classify_timeout(), UNKNOWN)
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_not_wired_flag(self):
        self.assertFalse(wires_into_run_store())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_edge).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["prior", "value", "low", "high"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_these_modules(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("hysteresis_class", source)
        self.assertNotIn("band_pin", source)

    def test_later_hold_stays_distinct(self):
        import ofn.kernel.later_hold as later_hold
        source = inspect.getsource(later_hold)
        self.assertNotIn("classify_edge", source)
        self.assertNotIn("latch_band", source)

    def test_scoped_authz_stays_distinct(self):
        import ofn.kernel.scoped_authz as scoped_authz
        source = inspect.getsource(scoped_authz)
        self.assertNotIn("classify_band", source)
        self.assertNotIn("HysteresisClass", source)

    def test_parity_check_stays_distinct(self):
        import ofn.kernel.parity_class as parity_class
        import ofn.kernel.check_pin as check_pin
        self.assertNotIn("classify_edge", inspect.getsource(parity_class))
        self.assertNotIn("latch_band", inspect.getsource(check_pin))


if __name__ == "__main__":
    unittest.main()
