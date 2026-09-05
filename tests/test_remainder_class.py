"""Contract tests for remainder_class (P1 complementary).

A leftover family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.remainder_class import (
    CLASSIFY,
    CONSUME,
    EXACT,
    FAMILIES,
    INTENTS,
    OBSERVE,
    PARTIAL,
    UNKNOWN,
    RemainderBind,
    admit_remainder,
    bind_remainder,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_consume,
    halt_blocks_observe,
    later_disarm_supersedes,
    leftover_is_zero,
    leftover_of,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-rem-0001"
_STRIDE = 8


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("consume"), CONSUME)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(INTENTS, frozenset({CONSUME, CLASSIFY, OBSERVE}))

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
        self.assertEqual(classify_family(16, stride=_STRIDE), EXACT)
        self.assertEqual(classify_family(19, stride=_STRIDE), PARTIAL)
        self.assertEqual(classify_family(0, stride=_STRIDE), EXACT)
        self.assertEqual(FAMILIES, frozenset({EXACT, PARTIAL}))

    def test_exact_multiple_is_exact(self):
        self.assertEqual(classify_family(24, stride=8), EXACT)
        self.assertEqual(leftover_of(24, stride=8), 0)

    def test_partial_records_leftover(self):
        self.assertEqual(classify_family(19, stride=8), PARTIAL)
        self.assertEqual(leftover_of(19, stride=8), 3)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, stride=_STRIDE))
        self.assertIsNone(classify_family(16, stride=None))
        self.assertIsNone(leftover_of(None, stride=_STRIDE))
        self.assertIsNot(classify_family(None, stride=_STRIDE), False)
        self.assertIsNot(leftover_of(None, stride=_STRIDE), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(16, stride=_STRIDE, timeout=True))
        self.assertIsNone(
            leftover_of(16, stride=_STRIDE, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(16, stride=_STRIDE, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(16, stride=_STRIDE, timeout=1)

    def test_bool_length_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, stride=_STRIDE)
        with self.assertRaises(FailClosedError):
            classify_family(False, stride=_STRIDE)

    def test_bool_stride_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(16, stride=True)
        with self.assertRaises(FailClosedError):
            classify_family(16, stride=False)

    def test_negative_length_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, stride=_STRIDE)

    def test_zero_stride_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(16, stride=0)

    def test_negative_stride_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(16, stride=-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(16.0, stride=_STRIDE)
        with self.assertRaises(FailClosedError):
            classify_family(16, stride=8.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_remainder("classify", 19, stride=_STRIDE, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_remainder("observe", 19, stride=_STRIDE, halted=True),
            True)

    def test_admit_consume_refused_when_halted(self):
        self.assertIs(
            admit_remainder("consume", 16, stride=_STRIDE, halted=True),
            False)
        self.assertIs(
            admit_remainder("consume", 16, stride=_STRIDE, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_remainder("consume", 16, stride=_STRIDE, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_remainder(None, 16, stride=_STRIDE))
        self.assertIsNone(admit_remainder("classify", None, stride=_STRIDE))
        self.assertIsNone(admit_remainder("classify", 16, stride=None))

    def test_admit_partial_is_not_a_send_false(self):
        self.assertIs(
            admit_remainder("classify", 19, stride=_STRIDE),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_remainder("classify", 16, stride=_STRIDE, halted="yes")

    def test_bind_records_leftover(self):
        bound = bind_remainder("classify", 19, stride=_STRIDE, slot=_SLOT)
        self.assertIsInstance(bound, RemainderBind)
        self.assertEqual(bound.family, PARTIAL)
        self.assertEqual(bound.leftover, 3)
        self.assertEqual(bound.length, 19)
        self.assertEqual(bound.stride, _STRIDE)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 16, stride=_STRIDE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, stride=_STRIDE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 16, stride=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 16, stride=_STRIDE, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_remainder(None, 16, stride=_STRIDE, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_remainder("classify", None, stride=_STRIDE, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_remainder(
                "classify", 16, stride=_STRIDE,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_remainder("classify", 16, stride=_STRIDE, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertTrue(halt_blocks_consume())

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

    def test_leftover_missing_is_not_zero(self):
        self.assertFalse(leftover_is_zero())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["length", "stride", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_remainder).parameters
        self.assertEqual(
            list(params),
            ["intent", "length", "stride", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
