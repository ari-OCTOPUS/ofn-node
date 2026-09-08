"""Contract tests for square_class (P1 complementary).

A square family is not a send. Missing is UNKNOWN, not FALSE
and not 0. Timeout does not prove a writer. Ready is not
authorized. Distinct from pow2/log2, prime/composite,
even/odd, remainder/leftover, quotient/divide.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.square_class import (
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    OTHER,
    SAMPLE,
    SQUARE,
    UNKNOWN,
    ZERO,
    SquareBind,
    admit_square,
    bind_square,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    floor_root_is_exact,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    later_disarm_supersedes,
    measured_zero_is_square,
    measured_zero_is_unknown,
    mints_run_id,
    missing_root_is_zero,
    other_is_false,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    root_of,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-sqr-0001"


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("sample"), SAMPLE)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(
            INTENTS, frozenset({SAMPLE, CLASSIFY, OBSERVE, INSPECT}))

    def test_hyphen_and_case_fold(self):
        self.assertEqual(classify_intent("SAMPLE"), SAMPLE)
        self.assertEqual(classify_intent(" Inspect "), INSPECT)

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

    def test_int_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent(1)

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
        self.assertEqual(classify_family(0), ZERO)
        self.assertEqual(classify_family(1), SQUARE)
        self.assertEqual(classify_family(2), OTHER)
        self.assertEqual(FAMILIES, frozenset({ZERO, SQUARE, OTHER}))

    def test_zero_is_zero_never_unknown_or_square(self):
        self.assertEqual(classify_family(0), ZERO)
        self.assertEqual(root_of(0), 0)
        self.assertFalse(measured_zero_is_unknown())
        self.assertFalse(measured_zero_is_square())

    def test_one_is_square_root_one(self):
        self.assertEqual(classify_family(1), SQUARE)
        self.assertEqual(root_of(1), 1)

    def test_perfect_squares(self):
        for value, root in ((4, 2), (9, 3), (16, 4), (25, 5), (100, 10)):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), SQUARE)
                self.assertEqual(root_of(value), root)

    def test_non_squares_are_other_never_false(self):
        for value in (2, 3, 5, 6, 7, 8, 10, 15, 99):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), OTHER)
        self.assertFalse(other_is_false())
        self.assertIsNot(classify_family(2), False)

    def test_floor_root_is_not_exact(self):
        self.assertEqual(classify_family(8), OTHER)
        self.assertFalse(floor_root_is_exact())
        with self.assertRaises(FailClosedError):
            root_of(8)

    def test_missing_is_none_not_false_or_zero(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNone(root_of(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(root_of(None), 0)
        self.assertFalse(missing_root_is_zero())

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(4, timeout=True))
        self.assertIsNone(root_of(4, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(4, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(4, timeout=1)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(4.0)
        with self.assertRaises(FailClosedError):
            classify_family(9.0)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1)
        with self.assertRaises(FailClosedError):
            classify_family(-4)
        with self.assertRaises(FailClosedError):
            root_of(-1)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_square("classify", 4, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_square("observe", 2, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_square("inspect", 0, halted=True), True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(admit_square("sample", 4, halted=True), False)
        self.assertIs(admit_square("sample", 4, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_square("sample", 4, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_square(None, 4))
        self.assertIsNone(admit_square("classify", None))

    def test_admit_other_is_not_a_send_false(self):
        self.assertIs(admit_square("classify", 2), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_square("classify", 4, halted="yes")

    def test_bind_records_square(self):
        bound = bind_square("classify", 9, slot=_SLOT)
        self.assertIsInstance(bound, SquareBind)
        self.assertEqual(bound.family, SQUARE)
        self.assertEqual(bound.value, 9)
        self.assertEqual(bound.root, 3)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_records_zero(self):
        bound = bind_square("classify", 0, slot=_SLOT)
        self.assertEqual(bound.family, ZERO)
        self.assertEqual(bound.root, 0)

    def test_bind_records_other_without_exact_root(self):
        bound = bind_square("classify", 2, slot=_SLOT)
        self.assertEqual(bound.family, OTHER)
        self.assertIsNone(bound.root)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 4, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 4, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_square(None, 4, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_square("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_square("classify", 4, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_square("classify", 4, slot="")

    def test_bind_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_square("classify", -1, slot=_SLOT)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())

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

    def test_missing_root_is_not_zero(self):
        self.assertFalse(missing_root_is_zero())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["value", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_square).parameters
        self.assertEqual(
            list(params),
            ["intent", "value", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
