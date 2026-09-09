"""Contract tests for overflow_class (P1 complementary).

An overflow family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.overflow_class import (
    CLASSIFY,
    CONSUME,
    FAMILIES,
    FITS,
    INTENTS,
    OBSERVE,
    OVERFLOW,
    UNKNOWN,
    OverflowBind,
    admit_overflow,
    bind_overflow,
    carry_is_zero,
    carry_of,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_consume,
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

_SLOT = "env-ovf-0001"
_CAP = 8


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
        self.assertEqual(
            classify_family(5, add=3, capacity=_CAP), FITS)
        self.assertEqual(
            classify_family(6, add=3, capacity=_CAP), OVERFLOW)
        self.assertEqual(
            classify_family(0, add=0, capacity=_CAP), FITS)
        self.assertEqual(FAMILIES, frozenset({FITS, OVERFLOW}))

    def test_exact_fill_is_fits(self):
        self.assertEqual(
            classify_family(5, add=3, capacity=_CAP), FITS)
        self.assertEqual(carry_of(5, add=3, capacity=_CAP), 0)

    def test_overflow_records_carry(self):
        self.assertEqual(
            classify_family(6, add=3, capacity=_CAP), OVERFLOW)
        self.assertEqual(carry_of(6, add=3, capacity=_CAP), 1)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, add=3, capacity=_CAP))
        self.assertIsNone(classify_family(5, add=None, capacity=_CAP))
        self.assertIsNone(classify_family(5, add=3, capacity=None))
        self.assertIsNone(carry_of(None, add=3, capacity=_CAP))
        self.assertIsNot(classify_family(None, add=3, capacity=_CAP), False)
        self.assertIsNot(carry_of(None, add=3, capacity=_CAP), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(5, add=3, capacity=_CAP, timeout=True))
        self.assertIsNone(
            carry_of(5, add=3, capacity=_CAP, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5, add=3, capacity=_CAP, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(5, add=3, capacity=_CAP, timeout=1)

    def test_bool_used_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, add=3, capacity=_CAP)
        with self.assertRaises(FailClosedError):
            classify_family(False, add=3, capacity=_CAP)

    def test_bool_add_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5, add=True, capacity=_CAP)
        with self.assertRaises(FailClosedError):
            classify_family(5, add=False, capacity=_CAP)

    def test_bool_capacity_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5, add=3, capacity=True)
        with self.assertRaises(FailClosedError):
            classify_family(5, add=3, capacity=False)

    def test_negative_used_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, add=3, capacity=_CAP)

    def test_negative_add_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5, add=-1, capacity=_CAP)

    def test_zero_capacity_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(0, add=0, capacity=0)

    def test_negative_capacity_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5, add=3, capacity=-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5.0, add=3, capacity=_CAP)
        with self.assertRaises(FailClosedError):
            classify_family(5, add=3.0, capacity=_CAP)
        with self.assertRaises(FailClosedError):
            classify_family(5, add=3, capacity=8.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_overflow(
                "classify", 6, add=3, capacity=_CAP, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_overflow(
                "observe", 6, add=3, capacity=_CAP, halted=True),
            True)

    def test_admit_consume_refused_when_halted(self):
        self.assertIs(
            admit_overflow(
                "consume", 5, add=3, capacity=_CAP, halted=True),
            False)
        self.assertIs(
            admit_overflow(
                "consume", 5, add=3, capacity=_CAP, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_overflow(
                "consume", 5, add=3, capacity=_CAP, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(
            admit_overflow(None, 5, add=3, capacity=_CAP))
        self.assertIsNone(
            admit_overflow("classify", None, add=3, capacity=_CAP))
        self.assertIsNone(
            admit_overflow("classify", 5, add=None, capacity=_CAP))
        self.assertIsNone(
            admit_overflow("classify", 5, add=3, capacity=None))

    def test_admit_overflow_is_not_a_send_false(self):
        self.assertIs(
            admit_overflow("classify", 6, add=3, capacity=_CAP),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_overflow(
                "classify", 5, add=3, capacity=_CAP, halted="yes")

    def test_bind_records_carry(self):
        bound = bind_overflow(
            "classify", 6, add=3, capacity=_CAP, slot=_SLOT)
        self.assertIsInstance(bound, OverflowBind)
        self.assertEqual(bound.family, OVERFLOW)
        self.assertEqual(bound.carry, 1)
        self.assertEqual(bound.used, 6)
        self.assertEqual(bound.add, 3)
        self.assertEqual(bound.capacity, _CAP)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 5, add=3, capacity=_CAP, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, add=3, capacity=_CAP, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 5, add=None, capacity=_CAP, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 5, add=3, capacity=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 5, add=3, capacity=_CAP, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_overflow(None, 5, add=3, capacity=_CAP, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_overflow("classify", None, add=3, capacity=_CAP, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_overflow(
                "classify", 5, add=3, capacity=_CAP,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_overflow("classify", 5, add=3, capacity=_CAP, slot="")


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

    def test_carry_missing_is_not_zero(self):
        self.assertFalse(carry_is_zero())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(
            list(params), ["used", "add", "capacity", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_overflow).parameters
        self.assertEqual(
            list(params),
            ["intent", "used", "add", "capacity", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
