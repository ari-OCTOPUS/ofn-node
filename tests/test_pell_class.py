"""Contract tests for pell_class (P1 complementary).

A Pell family is not a send. Missing is UNKNOWN, not FALSE
and not 0. Timeout does not prove a writer. Ready is not
authorized. Distinct from catalan/nest, cube/cubic,
square/root, fibonacci/sequence, lucas/companion,
triangular/series, remainder/leftover, stride/step.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.pell_class import (
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    OTHER,
    PELL,
    SAMPLE,
    UNKNOWN,
    ZERO,
    PellBind,
    admit_pell,
    bind_pell,
    catalan_is_pell,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    fibonacci_is_pell,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    index_of,
    later_disarm_supersedes,
    lucas_is_pell,
    measured_one_is_unknown,
    measured_zero_is_pell,
    measured_zero_is_unknown,
    mints_run_id,
    missing_index_is_zero,
    negative_is_other,
    other_is_false,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    stride_is_pell,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-pel-0001"


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
        self.assertEqual(classify_family(1), PELL)
        self.assertEqual(classify_family(3), OTHER)
        self.assertEqual(FAMILIES, frozenset({ZERO, PELL, OTHER}))

    def test_zero_is_zero_never_unknown_or_pell(self):
        self.assertEqual(classify_family(0), ZERO)
        self.assertIsNone(index_of(0))
        self.assertFalse(measured_zero_is_unknown())
        self.assertFalse(measured_zero_is_pell())

    def test_one_is_pell_index_one(self):
        self.assertEqual(classify_family(1), PELL)
        self.assertEqual(index_of(1), 1)
        self.assertFalse(measured_one_is_unknown())

    def test_known_pell_numbers(self):
        for value, index in (
            (1, 1), (2, 2), (5, 3), (12, 4), (29, 5),
            (70, 6), (169, 7), (408, 8), (985, 9),
        ):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), PELL)
                self.assertEqual(index_of(value), index)

    def test_non_pells_are_other_never_false(self):
        for value in (3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15, 28, 30, 71):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), OTHER)
        self.assertFalse(other_is_false())
        self.assertIsNot(classify_family(3), False)
        self.assertFalse(fibonacci_is_pell())
        self.assertFalse(catalan_is_pell())
        self.assertFalse(lucas_is_pell())
        self.assertFalse(stride_is_pell())

    def test_nearby_integer_is_not_exact(self):
        self.assertEqual(classify_family(4), OTHER)
        with self.assertRaises(FailClosedError):
            index_of(4)
        self.assertEqual(classify_family(13), OTHER)
        with self.assertRaises(FailClosedError):
            index_of(13)

    def test_missing_is_none_not_false_or_zero(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNone(index_of(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(index_of(None), 0)
        self.assertFalse(missing_index_is_zero())

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(5, timeout=True))
        self.assertIsNone(index_of(5, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(5, timeout=1)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5.0)
        with self.assertRaises(FailClosedError):
            classify_family(1.0)

    def test_negative_fails_closed_not_other(self):
        self.assertFalse(negative_is_other())
        with self.assertRaises(FailClosedError):
            classify_family(-1)
        with self.assertRaises(FailClosedError):
            classify_family(-5)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_pell("classify", 5, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_pell("observe", 3, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_pell("inspect", 0, halted=True), True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(admit_pell("sample", 5, halted=True), False)
        self.assertIs(admit_pell("sample", 5, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_pell("sample", 5, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_pell(None, 5))
        self.assertIsNone(admit_pell("classify", None))

    def test_admit_other_is_not_a_send_false(self):
        self.assertIs(admit_pell("classify", 3), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_pell("classify", 5, halted="yes")

    def test_bind_records_pell(self):
        bound = bind_pell("classify", 12, slot=_SLOT)
        self.assertIsInstance(bound, PellBind)
        self.assertEqual(bound.family, PELL)
        self.assertEqual(bound.value, 12)
        self.assertEqual(bound.index, 4)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_records_one_as_index_one(self):
        bound = bind_pell("classify", 1, slot=_SLOT)
        self.assertEqual(bound.family, PELL)
        self.assertEqual(bound.value, 1)
        self.assertEqual(bound.index, 1)

    def test_bind_records_zero_without_index(self):
        bound = bind_pell("classify", 0, slot=_SLOT)
        self.assertEqual(bound.family, ZERO)
        self.assertIsNone(bound.index)

    def test_bind_records_other_without_index(self):
        bound = bind_pell("classify", 3, slot=_SLOT)
        self.assertEqual(bound.family, OTHER)
        self.assertIsNone(bound.index)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 5, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 5, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_pell(None, 5, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_pell("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_pell("classify", 5, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_pell("classify", 5, slot="")


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

    def test_missing_index_is_not_zero(self):
        self.assertFalse(missing_index_is_zero())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["value", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_pell).parameters
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
