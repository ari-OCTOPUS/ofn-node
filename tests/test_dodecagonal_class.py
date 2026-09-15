"""Contract tests for dodecagonal_class (P1 complementary).

A 12-gonal family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.dodecagonal_class import (
    CLASSIFY,
    DODECAGONAL,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    OTHER,
    SAMPLE,
    UNKNOWN,
    ZERO,
    DodecaBind,
    admit_dodeca,
    bind_dodeca,
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
    measured_zero_is_dodecagonal,
    mints_run_id,
    missing_index_is_zero,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    square_is_other_here,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_SLOT = "env-do-0001"


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
        self.assertEqual(classify_family(1), DODECAGONAL)
        self.assertEqual(classify_family(2), OTHER)
        self.assertEqual(FAMILIES, frozenset({ZERO, DODECAGONAL, OTHER}))

    def test_known_dodeca_values(self):
        # Do_n = n(5n-4) : 1, 12, 33, 64, 105, 156, 217, 288
        expected = {1: 1, 12: 2, 33: 3, 64: 4, 105: 5, 156: 6, 217: 7, 288: 8}
        for value, index in expected.items():
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), DODECAGONAL)
                self.assertEqual(index_of(value), index)

    def test_measured_zero_is_zero_never_dodecagonal(self):
        self.assertEqual(classify_family(0), ZERO)
        self.assertNotEqual(classify_family(0), DODECAGONAL)
        self.assertEqual(index_of(0), 0)
        self.assertFalse(measured_zero_is_dodecagonal())

    def test_measured_one_is_dodecagonal_never_unknown(self):
        self.assertEqual(classify_family(1), DODECAGONAL)
        self.assertEqual(index_of(1), 1)
        self.assertIsNotNone(classify_family(1))
        self.assertFalse(measured_one_is_unknown())

    def test_neighbors_are_other(self):
        for value in (2, 3, 11, 13, 32, 34, 63, 65):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), OTHER)
                self.assertIsNone(index_of(value))
                self.assertIsNot(index_of(value), 0)

    def test_unrelated_squares_and_cubes_are_other_here(self):
        for value in (4, 9, 16, 25, 36, 49, 81, 8, 27, 125):
            with self.subTest(value=value):
                self.assertEqual(classify_family(value), OTHER)

    def test_sixty_four_is_dodecagonal_not_other(self):
        # 64 is 8^2 and also Do_4. This witness records DODECAGONAL.
        self.assertEqual(classify_family(64), DODECAGONAL)
        self.assertEqual(index_of(64), 4)
        self.assertFalse(square_is_other_here())

    def test_missing_is_none_not_false_or_zero(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNone(index_of(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(index_of(None), 0)
        self.assertFalse(missing_index_is_zero())

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(12, timeout=True))
        self.assertIsNone(index_of(12, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(12, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(12, timeout=1)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(12.0)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1)
        with self.assertRaises(FailClosedError):
            classify_family(-12)

    def test_replay_is_deterministic(self):
        self.assertEqual(classify_family(33), classify_family(33))
        self.assertEqual(index_of(64), index_of(64))


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_dodeca("classify", 12, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_dodeca("observe", 12, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_dodeca("inspect", 2, halted=True), True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(admit_dodeca("sample", 12, halted=True), False)
        self.assertIs(admit_dodeca("sample", 12, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_dodeca("sample", 12, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_dodeca(None, 12))
        self.assertIsNone(admit_dodeca("classify", None))

    def test_admit_other_is_not_a_send_false(self):
        self.assertIs(admit_dodeca("classify", 2), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_dodeca("classify", 12, halted="yes")

    def test_bind_records_index(self):
        bound = bind_dodeca("classify", 33, slot=_SLOT)
        self.assertIsInstance(bound, DodecaBind)
        self.assertEqual(bound.family, DODECAGONAL)
        self.assertEqual(bound.value, 33)
        self.assertEqual(bound.index, 3)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_zero_records_index_zero(self):
        bound = bind_dodeca("classify", 0, slot=_SLOT)
        self.assertEqual(bound.family, ZERO)
        self.assertEqual(bound.index, 0)

    def test_bind_other_index_is_none(self):
        bound = bind_dodeca("classify", 2, slot=_SLOT)
        self.assertEqual(bound.family, OTHER)
        self.assertIsNone(bound.index)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 12, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 12, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_dodeca(None, 12, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_dodeca("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_dodeca(
                "classify", 12, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_dodeca("classify", 12, slot="")

    def test_classify_family_has_no_halt_param(self):
        self.assertNotIn("halted", inspect.signature(classify_family).parameters)


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

    def test_does_not_promote_ready(self):
        self.assertFalse(promotes_ready_to_send())

    def test_later_disarm_holds(self):
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
