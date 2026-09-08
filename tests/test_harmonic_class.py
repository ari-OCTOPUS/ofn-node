"""Contract tests for harmonic_class (P1 complementary).

A harmonic family is not a send. Missing is UNKNOWN, not FALSE
and not 1. MIXED mean is UNKNOWN, not 0. Timeout does not
prove a writer. Ready is not authorized. Distinct from
mean/average, geometric/product, ratio/share, floor/ceil.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.harmonic_class import (
    CLASSIFY,
    EXACT,
    FAMILIES,
    INSPECT,
    INTENTS,
    MIXED,
    OBSERVE,
    SAMPLE,
    UNKNOWN,
    HarmonicBind,
    admit_harmonic,
    bind_harmonic,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    harmonic_of,
    later_disarm_supersedes,
    measured_one_is_unknown,
    missing_harmonic_is_one,
    mints_run_id,
    mixed_mean_is_zero,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-har-0001"
_EXACT_BAG = (2, 3, 6)
_MIXED_BAG = (2, 3)
_ONES = (1, 1, 1)


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
        self.assertEqual(classify_family(_EXACT_BAG), EXACT)
        self.assertEqual(classify_family(_MIXED_BAG), MIXED)
        self.assertEqual(FAMILIES, frozenset({EXACT, MIXED}))

    def test_ones_are_exact_never_unknown(self):
        self.assertEqual(classify_family(_ONES), EXACT)
        self.assertEqual(harmonic_of(_ONES), 1)
        self.assertFalse(measured_one_is_unknown())

    def test_single_value_is_itself(self):
        self.assertEqual(classify_family((6,)), EXACT)
        self.assertEqual(harmonic_of((6,)), 6)
        self.assertEqual(classify_family([4]), EXACT)
        self.assertEqual(harmonic_of([4]), 4)

    def test_pair_exact_and_mixed(self):
        self.assertEqual(classify_family((3, 6)), EXACT)
        self.assertEqual(harmonic_of((3, 6)), 4)
        self.assertEqual(classify_family((2, 2)), EXACT)
        self.assertEqual(harmonic_of((2, 2)), 2)
        self.assertEqual(classify_family((2, 3)), MIXED)
        self.assertIsNone(harmonic_of((2, 3)))
        self.assertFalse(mixed_mean_is_zero())
        self.assertIsNot(harmonic_of((2, 3)), 0)

    def test_triple_exact(self):
        self.assertEqual(classify_family((2, 3, 6)), EXACT)
        self.assertEqual(harmonic_of((2, 3, 6)), 3)

    def test_permuted_bag_same_family(self):
        self.assertEqual(classify_family((6, 2, 3)), EXACT)
        self.assertEqual(harmonic_of((6, 2, 3)), 3)
        self.assertEqual(classify_family((3, 2)), MIXED)

    def test_missing_bag_is_none_not_false_or_one(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNone(harmonic_of(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(harmonic_of(None), 1)
        self.assertIsNot(harmonic_of(None), 0)
        self.assertFalse(missing_harmonic_is_one())

    def test_none_member_is_unknown(self):
        self.assertIsNone(classify_family((2, None, 6)))
        self.assertIsNone(harmonic_of((2, None)))
        self.assertIsNot(classify_family((None,)), False)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(_EXACT_BAG, timeout=True))
        self.assertIsNone(harmonic_of(_EXACT_BAG, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(_EXACT_BAG, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(_EXACT_BAG, timeout=1)

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_family(())
        self.assertIn("empty", str(ctx.exception))
        with self.assertRaises(FailClosedError):
            classify_family([])
        with self.assertRaises(FailClosedError):
            harmonic_of(())

    def test_zero_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family((0,))
        with self.assertRaises(FailClosedError):
            classify_family((2, 0))
        with self.assertRaises(FailClosedError):
            harmonic_of((0, 2))

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family((-2, 3))
        with self.assertRaises(FailClosedError):
            harmonic_of((-1,))

    def test_bool_member_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family((True, 3))
        with self.assertRaises(FailClosedError):
            classify_family((2, False))

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family((2.0, 3))
        with self.assertRaises(FailClosedError):
            classify_family((2, 3.0))

    def test_string_bag_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family("2,3,6")
        with self.assertRaises(FailClosedError):
            classify_family(b"2")

    def test_int_as_bag_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(6)

    def test_dict_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family({2: 3})


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_harmonic("classify", _MIXED_BAG, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_harmonic("observe", _MIXED_BAG, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_harmonic("inspect", _EXACT_BAG, halted=True),
            True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(
            admit_harmonic("sample", _EXACT_BAG, halted=True),
            False)
        self.assertIs(
            admit_harmonic("sample", _EXACT_BAG, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_harmonic("sample", _EXACT_BAG, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_harmonic(None, _EXACT_BAG))
        self.assertIsNone(admit_harmonic("classify", None))
        self.assertIsNone(admit_harmonic("classify", (2, None)))

    def test_admit_mixed_is_not_a_send_false(self):
        self.assertIs(admit_harmonic("classify", _MIXED_BAG), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_harmonic("classify", _EXACT_BAG, halted="yes")

    def test_bind_records_exact(self):
        bound = bind_harmonic("classify", _EXACT_BAG, slot=_SLOT)
        self.assertIsInstance(bound, HarmonicBind)
        self.assertEqual(bound.family, EXACT)
        self.assertEqual(bound.harmonic, 3)
        self.assertEqual(bound.values, _EXACT_BAG)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_records_mixed_without_inventing_zero(self):
        bound = bind_harmonic("classify", _MIXED_BAG, slot=_SLOT)
        self.assertEqual(bound.family, MIXED)
        self.assertIsNone(bound.harmonic)
        self.assertIsNot(bound.harmonic, 0)

    def test_bind_keeps_presented_order(self):
        bound = bind_harmonic("classify", (6, 2, 3), slot=_SLOT)
        self.assertEqual(bound.values, (6, 2, 3))
        self.assertEqual(bound.harmonic, 3)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, _EXACT_BAG, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", _EXACT_BAG, slot=None))
        self.assertIsNone(try_bind("classify", (2, None), slot=_SLOT))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_harmonic(None, _EXACT_BAG, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_harmonic("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_harmonic(
                "classify", _EXACT_BAG, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_harmonic("classify", _EXACT_BAG, slot="")

    def test_bind_empty_bag_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_harmonic("classify", (), slot=_SLOT)

    def test_bind_zero_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_harmonic("classify", (0, 2), slot=_SLOT)


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

    def test_missing_harmonic_is_not_one(self):
        self.assertFalse(missing_harmonic_is_one())

    def test_mixed_mean_is_not_zero(self):
        self.assertFalse(mixed_mean_is_zero())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["values", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_harmonic).parameters
        self.assertEqual(
            list(params),
            ["intent", "values", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
