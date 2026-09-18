"""Contract tests for mean_class (P1 complementary).

An arithmetic mean of exact ints is not a send. Missing is
UNKNOWN, not FALSE. Timeout does not prove a writer. Ready
is not authorized. MIXED is a family, never FALSE.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.mean_class import (
    CLASSIFY,
    EXACT,
    FAMILIES,
    INSPECT,
    INTENTS,
    MIXED,
    OBSERVE,
    SAMPLE,
    UNKNOWN,
    MeanBind,
    admit_mean,
    bag_count,
    bag_total,
    bind_mean,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    empty_is_zero,
    exact_mean,
    exact_mean_is_authorized,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    later_disarm_supersedes,
    leftover_is_mean,
    measured_zero_is_unknown,
    mints_run_id,
    missing_is_zero,
    mixed_is_false,
    order_statistic_is_mean,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-mean-0001"


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
        self.assertEqual(classify_family((2, 4)), EXACT)
        self.assertEqual(classify_family((1, 2)), MIXED)
        self.assertEqual(FAMILIES, frozenset({EXACT, MIXED}))

    def test_single_zero_is_exact_never_unknown(self):
        self.assertEqual(classify_family((0,)), EXACT)
        self.assertEqual(exact_mean((0,)), 0)
        self.assertIsNot(classify_family((0,)), None)
        self.assertNotEqual(classify_family((0,)), UNKNOWN)

    def test_balanced_pair_is_exact(self):
        self.assertEqual(classify_family((-1, 1)), EXACT)
        self.assertEqual(exact_mean((-1, 1)), 0)
        self.assertEqual(classify_family((2, 4)), EXACT)
        self.assertEqual(exact_mean((2, 4)), 3)

    def test_odd_pair_is_mixed(self):
        self.assertEqual(classify_family((1, 2)), MIXED)
        self.assertIsNone(exact_mean((1, 2)))
        self.assertIsNot(exact_mean((1, 2)), False)
        self.assertIsNot(exact_mean((1, 2)), 0)

    def test_list_and_tuple_agree(self):
        self.assertEqual(classify_family([1, 5, 3]), EXACT)
        self.assertEqual(classify_family((1, 5, 3)), EXACT)
        self.assertEqual(exact_mean([1, 5, 3]), 3)

    def test_permutation_same_family(self):
        self.assertEqual(classify_family((1, 2, 3)), EXACT)
        self.assertEqual(classify_family((3, 2, 1)), EXACT)
        self.assertEqual(exact_mean((1, 2, 3)), exact_mean((3, 2, 1)))

    def test_missing_is_none_not_false_or_zero(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNone(exact_mean(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(classify_family(None), 0)
        self.assertIsNot(classify_family(None), EXACT)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family((2, 4), timeout=True))
        self.assertIsNone(exact_mean((2, 4), timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family((2, 4), timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family((2, 4), timeout=1)

    def test_empty_bag_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(())
        with self.assertRaises(FailClosedError):
            classify_family([])

    def test_bool_element_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family((True, 1))
        with self.assertRaises(FailClosedError):
            classify_family((1, False))

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family((1.0, 2))
        with self.assertRaises(FailClosedError):
            classify_family((1, 2.0))

    def test_str_and_set_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family("12")
        with self.assertRaises(FailClosedError):
            classify_family({1, 2})

    def test_bag_helpers_on_present(self):
        self.assertEqual(bag_count((1, 2, 3)), 3)
        self.assertEqual(bag_total((1, 2, 3)), 6)
        with self.assertRaises(FailClosedError):
            bag_count(None)
        with self.assertRaises(FailClosedError):
            bag_total(None)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_mean("classify", (2, 4), halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_mean("observe", (1, 2), halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_mean("inspect", (0,), halted=True), True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(admit_mean("sample", (2, 4), halted=True), False)
        self.assertIs(admit_mean("sample", (2, 4), halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_mean("sample", (2, 4), timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_mean(None, (2, 4)))
        self.assertIsNone(admit_mean("classify", None))

    def test_admit_mixed_is_not_a_send_false(self):
        self.assertIs(admit_mean("classify", (1, 2)), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mean("classify", (2, 4), halted="yes")

    def test_bind_records_exact(self):
        bound = bind_mean("classify", (2, 4), slot=_SLOT)
        self.assertIsInstance(bound, MeanBind)
        self.assertEqual(bound.family, EXACT)
        self.assertEqual(bound.count, 2)
        self.assertEqual(bound.total, 6)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_records_mixed(self):
        bound = bind_mean("inspect", (1, 2), slot=_SLOT)
        self.assertEqual(bound.family, MIXED)
        self.assertEqual(bound.intent, INSPECT)
        self.assertEqual(bound.count, 2)
        self.assertEqual(bound.total, 3)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, (2, 4), slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", (2, 4), slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mean(None, (2, 4), slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_mean("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mean("classify", (2, 4), slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mean("classify", (2, 4), slot="")


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

    def test_mixed_is_not_false(self):
        self.assertFalse(mixed_is_false())

    def test_exact_mean_is_not_authorized(self):
        self.assertFalse(exact_mean_is_authorized())

    def test_empty_is_not_zero(self):
        self.assertFalse(empty_is_zero())

    def test_measured_zero_is_not_unknown(self):
        self.assertFalse(measured_zero_is_unknown())

    def test_not_median_or_leftover(self):
        self.assertFalse(order_statistic_is_mean())
        self.assertFalse(leftover_is_mean())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["samples", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_mean).parameters
        self.assertEqual(
            list(params),
            ["intent", "samples", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
