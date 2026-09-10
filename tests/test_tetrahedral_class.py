"""Contract tests for tetrahedral_class (P1 complementary).

A tetrahedral family is not a send. Missing is UNKNOWN, not
FALSE and not 0. Timeout does not prove a writer. Ready is
not authorized. Distinct from pentagonal/figure,
hexagonal/lattice, heptagonal/gonal, octagonal/vertex,
triangular/series, cube/cubic, square/root.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.tetrahedral_class import (
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    OTHER,
    SAMPLE,
    TETRAHEDRAL,
    UNKNOWN,
    ZERO,
    TetrahedralBind,
    admit_tetrahedral,
    bind_tetrahedral,
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
    measured_zero_is_tetrahedral,
    missing_index_is_zero,
    mints_run_id,
    other_is_granted,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    tetrahedral_of,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-tet-0001"


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

    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("send")

    def test_sealed_intent_fails_closed(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_intent(name)


class ClassifyFamily(unittest.TestCase):
    def test_families_closed(self):
        self.assertEqual(FAMILIES, frozenset({ZERO, TETRAHEDRAL, OTHER}))

    def test_zero_is_zero_never_tetrahedral(self):
        self.assertEqual(classify_family(0), ZERO)
        self.assertNotEqual(classify_family(0), TETRAHEDRAL)
        self.assertFalse(measured_zero_is_tetrahedral())

    def test_one_is_tetrahedral_never_unknown(self):
        self.assertEqual(classify_family(1), TETRAHEDRAL)
        self.assertEqual(index_of(1), 1)
        self.assertFalse(measured_one_is_unknown())

    def test_known_tetrahedrals(self):
        known = {
            1: 1,
            4: 2,
            10: 3,
            20: 4,
            35: 5,
            56: 6,
            84: 7,
            120: 8,
        }
        for value, n in known.items():
            with self.subTest(value=value, n=n):
                self.assertEqual(classify_family(value), TETRAHEDRAL)
                self.assertEqual(index_of(value), n)
                self.assertEqual(tetrahedral_of(n), value)

    def test_other_is_recorded(self):
        for value in (2, 3, 5, 6, 7, 8, 9, 11):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), OTHER)
                self.assertIsNone(index_of(value))
        self.assertFalse(other_is_granted())

    def test_missing_is_unknown_not_false_or_zero(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNone(index_of(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(index_of(None), 0)
        self.assertFalse(missing_index_is_zero())

    def test_timeout_is_unknown(self):
        self.assertIsNone(classify_family(10, timeout=True))
        self.assertIsNone(index_of(10, timeout=True))
        self.assertIsNone(tetrahedral_of(3, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, timeout="yes")

    def test_bool_value_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10.0)

    def test_tetrahedral_of_zero_index(self):
        self.assertEqual(tetrahedral_of(0), 0)

    def test_tetrahedral_of_missing_is_none(self):
        self.assertIsNone(tetrahedral_of(None))


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_tetrahedral("classify", 10, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_tetrahedral("observe", 2, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_tetrahedral("inspect", 0, halted=True), True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(admit_tetrahedral("sample", 10, halted=True), False)
        self.assertIs(admit_tetrahedral("sample", 10, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_tetrahedral("sample", 10, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_tetrahedral(None, 10))
        self.assertIsNone(admit_tetrahedral("classify", None))

    def test_admit_other_is_not_a_send_false(self):
        self.assertIs(admit_tetrahedral("classify", 2), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_tetrahedral("classify", 10, halted="yes")

    def test_bind_records_tetrahedral(self):
        bound = bind_tetrahedral("classify", 10, slot=_SLOT)
        self.assertIsInstance(bound, TetrahedralBind)
        self.assertEqual(bound.family, TETRAHEDRAL)
        self.assertEqual(bound.value, 10)
        self.assertEqual(bound.index, 3)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_zero_index_is_none(self):
        bound = bind_tetrahedral("inspect", 0, slot=_SLOT)
        self.assertEqual(bound.family, ZERO)
        self.assertIsNone(bound.index)

    def test_bind_other_index_is_none(self):
        bound = bind_tetrahedral("observe", 2, slot=_SLOT)
        self.assertEqual(bound.family, OTHER)
        self.assertIsNone(bound.index)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 10, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 10, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_tetrahedral(None, 10, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_tetrahedral("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_tetrahedral(
                "classify", 10, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_tetrahedral("classify", 10, slot="")


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

    def test_other_is_not_granted(self):
        self.assertFalse(other_is_granted())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["value", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_tetrahedral).parameters
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
