"""Contract tests for mid_class (P1 complementary).

A middle family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.mid_class import (
    CENTER,
    CLASSIFY,
    EMPTY,
    EVEN_SPLIT,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    ODD_CENTER,
    SINGLE,
    UNKNOWN,
    MidBind,
    admit_mid,
    bind_mid,
    center_of,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    empty_is_zero,
    even_split_is_authorized,
    even_split_is_zero,
    grants_send,
    halt_blocks_center,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    hi_mid_of,
    later_disarm_supersedes,
    lo_mid_of,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unique_center_is_send,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-mid-0001"


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("center"), CENTER)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(INTENTS, frozenset({CENTER, CLASSIFY, OBSERVE, INSPECT}))

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
            classify_intent("take")

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
        self.assertEqual(classify_family(0), EMPTY)
        self.assertEqual(classify_family(1), SINGLE)
        self.assertEqual(classify_family(3), ODD_CENTER)
        self.assertEqual(classify_family(5), ODD_CENTER)
        self.assertEqual(classify_family(2), EVEN_SPLIT)
        self.assertEqual(classify_family(4), EVEN_SPLIT)
        self.assertEqual(
            FAMILIES, frozenset({EMPTY, SINGLE, ODD_CENTER, EVEN_SPLIT}))

    def test_single_is_not_odd_center(self):
        self.assertEqual(classify_family(1), SINGLE)
        self.assertNotEqual(classify_family(1), ODD_CENTER)
        self.assertNotEqual(classify_family(1), EVEN_SPLIT)

    def test_two_item_is_even_split_not_unique(self):
        self.assertEqual(classify_family(2), EVEN_SPLIT)
        self.assertIsNone(center_of(2))

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(classify_family(None), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(5, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(5, timeout=1)

    def test_bool_length_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_negative_length_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(5.0)


class CenterOf(unittest.TestCase):
    def test_unique_centers(self):
        self.assertEqual(center_of(1), 0)
        self.assertEqual(center_of(3), 1)
        self.assertEqual(center_of(5), 2)
        self.assertEqual(center_of(7), 3)

    def test_empty_and_even_are_unknown_not_zero(self):
        self.assertIsNone(center_of(0))
        self.assertIsNone(center_of(2))
        self.assertIsNone(center_of(4))
        self.assertIsNot(center_of(0), 0)
        self.assertIsNot(center_of(4), 0)
        self.assertIsNot(center_of(4), 2)

    def test_missing_and_timeout_are_none(self):
        self.assertIsNone(center_of(None))
        self.assertIsNone(center_of(5, timeout=True))

    def test_lo_hi_for_even_split(self):
        self.assertEqual(lo_mid_of(4), 1)
        self.assertEqual(hi_mid_of(4), 2)
        self.assertEqual(lo_mid_of(2), 0)
        self.assertEqual(hi_mid_of(2), 1)

    def test_lo_hi_share_unique_center(self):
        self.assertEqual(lo_mid_of(5), 2)
        self.assertEqual(hi_mid_of(5), 2)
        self.assertEqual(lo_mid_of(1), 0)
        self.assertEqual(hi_mid_of(1), 0)

    def test_lo_hi_empty_and_missing_are_none(self):
        self.assertIsNone(lo_mid_of(0))
        self.assertIsNone(hi_mid_of(0))
        self.assertIsNone(lo_mid_of(None))
        self.assertIsNone(hi_mid_of(None))
        self.assertIsNot(lo_mid_of(0), 0)
        self.assertIsNot(hi_mid_of(0), 0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_mid("classify", 5, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_mid("observe", 4, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_mid("inspect", 3, halted=True), True)

    def test_admit_center_refused_when_halted(self):
        self.assertIs(admit_mid("center", 5, halted=True), False)
        self.assertIs(admit_mid("center", 5, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_mid("center", 5, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_mid(None, 5))
        self.assertIsNone(admit_mid("classify", None))

    def test_admit_even_split_is_not_a_send_false(self):
        self.assertIs(admit_mid("classify", 4), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mid("classify", 5, halted="yes")

    def test_bind_records_family(self):
        bound = bind_mid("classify", 5, slot=_SLOT)
        self.assertIsInstance(bound, MidBind)
        self.assertEqual(bound.family, ODD_CENTER)
        self.assertEqual(bound.length, 5)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_even_split(self):
        bound = bind_mid("inspect", 4, slot=_SLOT)
        self.assertEqual(bound.family, EVEN_SPLIT)
        self.assertEqual(bound.length, 4)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 5, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 5, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mid(None, 5, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_mid("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mid("classify", 5, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mid("classify", 5, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_center())

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

    def test_empty_and_even_missing_are_not_zero(self):
        self.assertFalse(empty_is_zero())
        self.assertFalse(even_split_is_zero())
        self.assertFalse(unique_center_is_send())
        self.assertFalse(even_split_is_authorized())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["length", "timeout"])
        for forbidden in (
            "halted", "now", "index", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_mid).parameters
        self.assertEqual(
            list(params),
            ["intent", "length", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
