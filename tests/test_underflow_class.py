"""Contract tests for underflow_class (P1 complementary).

A subtraction family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.underflow_class import (
    CLASSIFY,
    EXACT,
    FAMILIES,
    INTENTS,
    MEASURE,
    OBSERVE,
    UNDERFLOW,
    UNKNOWN,
    WRAP,
    UnderflowBind,
    admit_sub,
    bind_sub,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_measure,
    halt_blocks_observe,
    later_disarm_supersedes,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-sub-0001"
_FLOOR = 0


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("measure"), MEASURE)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(INTENTS, frozenset({MEASURE, CLASSIFY, OBSERVE}))

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
        self.assertEqual(
            classify_family(8, 3, floor=_FLOOR), EXACT)
        self.assertEqual(
            classify_family(3, 8, floor=_FLOOR), UNDERFLOW)
        self.assertEqual(
            classify_family(3, 8, floor=_FLOOR, wrap_requested=True), WRAP)
        self.assertEqual(FAMILIES, frozenset({EXACT, UNDERFLOW, WRAP}))

    def test_exact_floor_is_exact(self):
        self.assertEqual(classify_family(5, 5, floor=0), EXACT)
        self.assertEqual(classify_family(8, 3, floor=5), EXACT)

    def test_just_below_floor_is_underflow(self):
        self.assertEqual(classify_family(8, 4, floor=5), UNDERFLOW)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, 3, floor=_FLOOR))
        self.assertIsNone(classify_family(8, None, floor=_FLOOR))
        self.assertIsNot(classify_family(None, 3, floor=_FLOOR), False)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(8, 3, floor=_FLOOR, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(8, 3, floor=_FLOOR, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(8, 3, floor=_FLOOR, timeout=1)

    def test_bool_operand_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, 1, floor=_FLOOR)
        with self.assertRaises(FailClosedError):
            classify_family(8, False, floor=_FLOOR)

    def test_bool_floor_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(8, 3, floor=True)
        with self.assertRaises(FailClosedError):
            classify_family(8, 3, floor=False)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, 3, floor=_FLOOR)
        with self.assertRaises(FailClosedError):
            classify_family(8, -1, floor=_FLOOR)
        with self.assertRaises(FailClosedError):
            classify_family(8, 3, floor=-1)

    def test_wrap_flag_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, 8, floor=_FLOOR, wrap_requested=1)
        with self.assertRaises(FailClosedError):
            classify_family(3, 8, floor=_FLOOR, wrap_requested="yes")

    def test_wrap_requested_on_exact_stays_exact(self):
        self.assertEqual(
            classify_family(8, 3, floor=_FLOOR, wrap_requested=True),
            EXACT)

    def test_zero_floor_zero_minus_zero_is_exact(self):
        self.assertEqual(classify_family(0, 0, floor=0), EXACT)

    def test_zero_minus_one_is_underflow(self):
        self.assertEqual(classify_family(0, 1, floor=0), UNDERFLOW)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_sub("classify", 8, 3, floor=_FLOOR, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_sub("observe", 8, 3, floor=_FLOOR, halted=True),
            True)

    def test_admit_measure_refused_when_halted(self):
        self.assertIs(
            admit_sub("measure", 8, 3, floor=_FLOOR, halted=True),
            False)
        self.assertIs(
            admit_sub("measure", 8, 3, floor=_FLOOR, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_sub("measure", 8, 3, floor=_FLOOR, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_sub(None, 8, 3, floor=_FLOOR))
        self.assertIsNone(admit_sub("classify", None, 3, floor=_FLOOR))
        self.assertIsNone(admit_sub("classify", 8, None, floor=_FLOOR))

    def test_admit_underflow_is_not_a_send_false(self):
        self.assertIs(
            admit_sub("classify", 3, 8, floor=_FLOOR),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_sub("classify", 8, 3, floor=_FLOOR, halted="yes")

    def test_bind_records_operands(self):
        bound = bind_sub("classify", 8, 3, floor=_FLOOR, slot=_SLOT)
        self.assertIsInstance(bound, UnderflowBind)
        self.assertEqual(bound.family, EXACT)
        self.assertEqual(bound.minuend, 8)
        self.assertEqual(bound.subtrahend, 3)
        self.assertEqual(bound.floor, _FLOOR)
        self.assertIs(bound.wrap_requested, False)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 8, 3, floor=_FLOOR, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, 3, floor=_FLOOR, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 8, None, floor=_FLOOR, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 8, 3, floor=_FLOOR, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_sub(None, 8, 3, floor=_FLOOR, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_sub("classify", None, 3, floor=_FLOOR, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_sub(
                "classify", 8, 3, floor=_FLOOR,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_sub("classify", 8, 3, floor=_FLOOR, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertTrue(halt_blocks_measure())

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

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(
            list(params),
            ["minuend", "subtrahend", "floor", "wrap_requested", "timeout"],
        )
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_sub).parameters
        self.assertEqual(
            list(params),
            [
                "intent", "minuend", "subtrahend", "floor",
                "wrap_requested", "halted", "timeout",
            ],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
