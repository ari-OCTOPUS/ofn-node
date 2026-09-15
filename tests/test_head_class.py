"""Contract tests for head_class (P1 complementary).

An end family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.head_class import (
    CLASSIFY,
    EMPTY,
    FAMILIES,
    HEAD,
    INSPECT,
    INTENTS,
    INTERIOR,
    OBSERVE,
    PAST,
    SINGLE,
    TAIL,
    TAKE,
    UNKNOWN,
    HeadBind,
    admit_head,
    bind_head,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    empty_is_zero,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_take,
    head_is_authorized,
    later_disarm_supersedes,
    mints_run_id,
    past_is_false,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    tail_is_send,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-head-0001"


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("take"), TAKE)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(INTENTS, frozenset({TAKE, CLASSIFY, OBSERVE, INSPECT}))

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
        self.assertEqual(classify_family(0, index=0), EMPTY)
        self.assertEqual(classify_family(1, index=0), SINGLE)
        self.assertEqual(classify_family(4, index=0), HEAD)
        self.assertEqual(classify_family(4, index=3), TAIL)
        self.assertEqual(classify_family(4, index=1), INTERIOR)
        self.assertEqual(classify_family(4, index=4), PAST)
        self.assertEqual(
            FAMILIES, frozenset({EMPTY, SINGLE, HEAD, TAIL, INTERIOR, PAST}))

    def test_empty_zero_index_is_empty_not_past(self):
        self.assertEqual(classify_family(0, index=0), EMPTY)

    def test_empty_nonzero_index_is_past(self):
        self.assertEqual(classify_family(0, index=1), PAST)

    def test_single_is_not_head_only(self):
        self.assertEqual(classify_family(1, index=0), SINGLE)
        self.assertNotEqual(classify_family(1, index=0), HEAD)
        self.assertNotEqual(classify_family(1, index=0), TAIL)

    def test_two_item_has_head_and_tail_no_interior(self):
        self.assertEqual(classify_family(2, index=0), HEAD)
        self.assertEqual(classify_family(2, index=1), TAIL)
        self.assertNotEqual(classify_family(2, index=0), INTERIOR)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, index=0))
        self.assertIsNone(classify_family(4, index=None))
        self.assertIsNot(classify_family(None, index=0), False)
        self.assertIsNot(classify_family(None, index=0), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(4, index=0, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(4, index=0, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(4, index=0, timeout=1)

    def test_bool_length_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, index=0)
        with self.assertRaises(FailClosedError):
            classify_family(False, index=0)

    def test_bool_index_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(4, index=True)
        with self.assertRaises(FailClosedError):
            classify_family(4, index=False)

    def test_negative_length_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, index=0)

    def test_negative_index_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(4, index=-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(4.0, index=0)
        with self.assertRaises(FailClosedError):
            classify_family(4, index=0.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_head("classify", 4, index=0, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_head("observe", 4, index=3, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_head("inspect", 4, index=1, halted=True),
            True)

    def test_admit_take_refused_when_halted(self):
        self.assertIs(
            admit_head("take", 4, index=3, halted=True),
            False)
        self.assertIs(
            admit_head("take", 4, index=3, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_head("take", 4, index=3, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_head(None, 4, index=0))
        self.assertIsNone(admit_head("classify", None, index=0))
        self.assertIsNone(admit_head("classify", 4, index=None))

    def test_admit_past_is_not_a_send_false(self):
        self.assertIs(
            admit_head("classify", 4, index=4),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_head("classify", 4, index=0, halted="yes")

    def test_bind_records_family(self):
        bound = bind_head("classify", 4, index=3, slot=_SLOT)
        self.assertIsInstance(bound, HeadBind)
        self.assertEqual(bound.family, TAIL)
        self.assertEqual(bound.length, 4)
        self.assertEqual(bound.index, 3)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 4, index=0, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, index=0, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 4, index=None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 4, index=0, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_head(None, 4, index=0, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_head("classify", None, index=0, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_head(
                "classify", 4, index=0,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_head("classify", 4, index=0, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_take())

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

    def test_empty_missing_is_not_zero(self):
        self.assertFalse(empty_is_zero())

    def test_head_is_not_authorized(self):
        self.assertFalse(head_is_authorized())
        self.assertFalse(tail_is_send())
        self.assertFalse(past_is_false())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["length", "index", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_head).parameters
        self.assertEqual(
            list(params),
            ["intent", "length", "index", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
