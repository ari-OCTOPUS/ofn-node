"""Contract tests for octagonal_class (P1 complementary).

An octagonal figure is not a send. Missing is UNKNOWN, not FALSE
and not 0. Timeout does not prove a writer. Ready is not
authorized. Distinct from heptagonal/gonal, pentagonal/figure,
hexagonal/lattice, triangular/series, square/root, cube/cubic,
pell/silver, catalan/nest, fibonacci/sequence.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.octagonal_class import (
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    OCTAGONAL,
    OTHER,
    SAMPLE,
    UNKNOWN,
    ZERO,
    OctagonalBind,
    admit_octagonal,
    bind_octagonal,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    index_of,
    later_disarm_supersedes,
    measured_one_is_unknown,
    measured_zero_is_octagonal,
    missing_value_is_zero,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-oct-0001"


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
            classify_intent("cut")

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
        self.assertEqual(classify_family(1), OCTAGONAL)
        self.assertEqual(classify_family(8), OCTAGONAL)
        self.assertEqual(classify_family(2), OTHER)
        self.assertEqual(FAMILIES, frozenset({ZERO, OCTAGONAL, OTHER}))

    def test_zero_is_zero_never_octagonal(self):
        self.assertEqual(classify_family(0), ZERO)
        self.assertEqual(index_of(0), 0)
        self.assertFalse(measured_zero_is_octagonal())

    def test_one_is_octagonal_index_one_never_unknown(self):
        self.assertEqual(classify_family(1), OCTAGONAL)
        self.assertEqual(index_of(1), 1)
        self.assertFalse(measured_one_is_unknown())

    def test_known_octagonals(self):
        # O_n = n(3n-2) : 0,1,8,21,40,65,96,133
        expected = {1: 1, 8: 2, 21: 3, 40: 4, 65: 5, 96: 6, 133: 7}
        for value, idx in expected.items():
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), OCTAGONAL)
                self.assertEqual(index_of(value), idx)

    def test_neighbors_are_other(self):
        for value in (2, 3, 4, 5, 6, 7, 9, 20, 22, 39, 41, 64, 66):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), OTHER)
                self.assertIsNone(index_of(value))

    def test_other_figures_are_other_here(self):
        # triangular 3, square 4, pentagonal 5, hexagonal 6,
        # heptagonal 7, square 9/16/25, cube 27/64 (8 is O_2)
        for value in (3, 4, 5, 6, 7, 9, 16, 18, 25, 27, 34, 64):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), OTHER)

    def test_missing_is_none_not_false_or_zero(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNone(index_of(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(index_of(None), 0)
        self.assertFalse(missing_value_is_zero())

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(8, timeout=True))
        self.assertIsNone(index_of(8, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(8, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(8, timeout=1)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(8.0)
        with self.assertRaises(FailClosedError):
            classify_family(1.0)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1)
        with self.assertRaises(FailClosedError):
            classify_family(-8)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_octagonal("classify", 8, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_octagonal("observe", 8, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_octagonal("inspect", 2, halted=True), True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(admit_octagonal("sample", 1, halted=True), False)
        self.assertIs(admit_octagonal("sample", 1, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_octagonal("sample", 1, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_octagonal(None, 8))
        self.assertIsNone(admit_octagonal("classify", None))

    def test_admit_other_is_not_a_send_false(self):
        self.assertIs(admit_octagonal("classify", 2), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_octagonal("classify", 8, halted="yes")

    def test_bind_records_index(self):
        bound = bind_octagonal("classify", 8, slot=_SLOT)
        self.assertIsInstance(bound, OctagonalBind)
        self.assertEqual(bound.family, OCTAGONAL)
        self.assertEqual(bound.value, 8)
        self.assertEqual(bound.index, 2)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_zero_records_index_zero(self):
        bound = bind_octagonal("classify", 0, slot=_SLOT)
        self.assertEqual(bound.family, ZERO)
        self.assertEqual(bound.index, 0)

    def test_bind_other_has_no_index(self):
        bound = bind_octagonal("classify", 2, slot=_SLOT)
        self.assertEqual(bound.family, OTHER)
        self.assertIsNone(bound.index)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 8, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 8, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_octagonal(None, 8, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_octagonal("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_octagonal(
                "classify", 8, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_octagonal("classify", 8, slot="")

    def test_bind_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_octagonal("classify", -1, slot=_SLOT)


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

    def test_missing_value_is_not_zero(self):
        self.assertFalse(missing_value_is_zero())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["value", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_octagonal).parameters
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
