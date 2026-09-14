"""Contract tests for peak_class (P1 complementary).

A three-sample extremum is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
All-equal coincidence is NEITHER, never PEAK or TROUGH.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.peak_class import (
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    NEITHER,
    OBSERVE,
    PEAK,
    SAMPLE,
    TROUGH,
    UNKNOWN,
    PeakBind,
    admit_peak,
    bind_peak,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    coincidence_is_peak,
    coincidence_is_trough,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    later_disarm_supersedes,
    mints_run_id,
    missing_is_zero,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    two_sample_is_three,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-peak-0001"


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("sample"), SAMPLE)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(INTENTS, frozenset({SAMPLE, CLASSIFY, OBSERVE, INSPECT}))

    def test_missing_is_unknown_not_false(self):
        self.assertEqual(classify_intent(None), UNKNOWN)
        self.assertNotEqual(classify_intent(None), "FALSE")
        self.assertIsNot(classify_intent(None), False)

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("")
        with self.assertRaises(FailClosedError):
            classify_intent("   ")

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent(True)
        with self.assertRaises(FailClosedError):
            classify_intent(False)

    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("resend")
        with self.assertRaises(FailClosedError):
            classify_intent("send")
        with self.assertRaises(FailClosedError):
            classify_intent("consume")
        with self.assertRaises(FailClosedError):
            classify_intent("measure")

    def test_send_names_fail_closed(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
            "Quote_Sent",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_intent(name)


class ClassifyFamily(unittest.TestCase):
    def test_closed_families(self):
        self.assertEqual(classify_family(1, 3, 0), PEAK)
        self.assertEqual(classify_family(3, 0, 2), TROUGH)
        self.assertEqual(classify_family(1, 2, 3), NEITHER)
        self.assertEqual(FAMILIES, frozenset({PEAK, TROUGH, NEITHER}))

    def test_strict_peak(self):
        self.assertEqual(classify_family(-2, 5, 1), PEAK)
        self.assertEqual(classify_family(0, 1, -1), PEAK)

    def test_strict_trough(self):
        self.assertEqual(classify_family(4, -1, 2), TROUGH)
        self.assertEqual(classify_family(1, 0, 1), TROUGH)

    def test_all_equal_is_neither_not_unknown(self):
        self.assertEqual(classify_family(0, 0, 0), NEITHER)
        self.assertEqual(classify_family(7, 7, 7), NEITHER)
        self.assertNotEqual(classify_family(0, 0, 0), UNKNOWN)
        self.assertIsNot(classify_family(0, 0, 0), None)

    def test_measured_zero_is_a_sample(self):
        self.assertEqual(classify_family(-1, 0, -1), PEAK)
        self.assertEqual(classify_family(1, 0, 1), TROUGH)
        self.assertEqual(classify_family(0, 0, 1), NEITHER)

    def test_monotonic_is_neither(self):
        self.assertEqual(classify_family(1, 2, 3), NEITHER)
        self.assertEqual(classify_family(3, 2, 1), NEITHER)

    def test_one_sided_is_neither(self):
        self.assertEqual(classify_family(1, 3, 3), NEITHER)
        self.assertEqual(classify_family(3, 3, 1), NEITHER)
        self.assertEqual(classify_family(2, 2, 5), NEITHER)

    def test_missing_is_none_not_false_or_zero(self):
        self.assertIsNone(classify_family(None, 3, 0))
        self.assertIsNone(classify_family(1, None, 0))
        self.assertIsNone(classify_family(1, 3, None))
        self.assertIsNot(classify_family(None, 3, 0), False)
        self.assertIsNot(classify_family(None, 3, 0), 0)
        self.assertIsNot(classify_family(None, 3, 0), PEAK)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(1, 3, 0, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(1, 3, 0, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(1, 3, 0, timeout=1)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, 3, 0)
        with self.assertRaises(FailClosedError):
            classify_family(1, False, 0)
        with self.assertRaises(FailClosedError):
            classify_family(1, 3, True)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(1.0, 3, 0)
        with self.assertRaises(FailClosedError):
            classify_family(1, 3.0, 0)
        with self.assertRaises(FailClosedError):
            classify_family(1, 3, 0.0)

    def test_str_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family("1", 3, 0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_peak("classify", 1, 3, 0, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_peak("observe", 1, 3, 0, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_peak("inspect", 1, 3, 0, halted=True), True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(admit_peak("sample", 1, 0, 1, halted=True), False)
        self.assertIs(admit_peak("sample", 1, 0, 1, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_peak("sample", 1, 0, 1, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_peak(None, 1, 0, 1))
        self.assertIsNone(admit_peak("classify", None, 0, 1))
        self.assertIsNone(admit_peak("classify", 1, None, 1))
        self.assertIsNone(admit_peak("classify", 1, 0, None))

    def test_admit_neither_is_not_a_send_false(self):
        self.assertIs(admit_peak("classify", 1, 2, 3), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_peak("classify", 1, 3, 0, halted="yes")

    def test_bind_records_trough(self):
        bound = bind_peak("classify", 4, -1, 2, slot=_SLOT)
        self.assertIsInstance(bound, PeakBind)
        self.assertEqual(bound.family, TROUGH)
        self.assertEqual(bound.earlier, 4)
        self.assertEqual(bound.mid, -1)
        self.assertEqual(bound.later, 2)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_records_peak(self):
        bound = bind_peak("inspect", -2, 5, 1, slot=_SLOT)
        self.assertEqual(bound.family, PEAK)
        self.assertEqual(bound.intent, INSPECT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 1, 3, 0, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, 3, 0, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 1, None, 0, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 1, 3, None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 1, 3, 0, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_peak(None, 1, 3, 0, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_peak("classify", None, 3, 0, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_peak(
                "classify", 1, 3, 0, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_peak("classify", 1, 3, 0, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_sample())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

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

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_missing_is_not_zero(self):
        self.assertFalse(missing_is_zero())

    def test_coincidence_is_not_an_extremum(self):
        self.assertFalse(coincidence_is_peak())
        self.assertFalse(coincidence_is_trough())

    def test_two_sample_is_not_three(self):
        self.assertFalse(two_sample_is_three())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["earlier", "mid", "later", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_peak).parameters
        self.assertEqual(
            list(params),
            ["intent", "earlier", "mid", "later", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
