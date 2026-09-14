"""Contract tests for stride_class (P1 complementary).

A walk-distance family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.stride_class import (
    ADMIT,
    CLASSIFY,
    FAMILIES,
    INTENTS,
    OBSERVE,
    SKIP,
    UNIT,
    UNKNOWN,
    StrideBind,
    admit_stride,
    bind_stride,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_admit,
    halt_blocks_classify,
    halt_blocks_observe,
    later_disarm_supersedes,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    replaces_seq_cursor,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-stride-0001"
_FROM = 10


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("admit"), ADMIT)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(INTENTS, frozenset({ADMIT, CLASSIFY, OBSERVE}))

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
        self.assertEqual(classify_family(1), UNIT)
        self.assertEqual(classify_family(2), SKIP)
        self.assertEqual(classify_family(8), SKIP)
        self.assertEqual(FAMILIES, frozenset({UNIT, SKIP}))

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNot(classify_family(None), False)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(1, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(1, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(1, timeout=1)

    def test_bool_stride_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_zero_stride_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(0)

    def test_negative_stride_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1)

    def test_str_is_not_int(self):
        with self.assertRaises(FailClosedError):
            classify_family("1")

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(1.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_stride("classify", 1, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_stride("observe", 2, halted=True), True)

    def test_admit_start_refused_when_halted(self):
        self.assertIs(admit_stride("admit", 1, halted=True), False)
        self.assertIs(admit_stride("admit", 1, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_stride("admit", 1, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_stride(None, 1))
        self.assertIsNone(admit_stride("classify", None))

    def test_admit_skip_is_not_a_send_false(self):
        self.assertIs(admit_stride("classify", 8), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_stride("classify", 1, halted="yes")

    def test_bind_records_next_index(self):
        bound = bind_stride(
            "classify", 3, from_index=_FROM, slot=_SLOT)
        self.assertIsInstance(bound, StrideBind)
        self.assertEqual(bound.family, SKIP)
        self.assertEqual(bound.stride, 3)
        self.assertEqual(bound.from_index, _FROM)
        self.assertEqual(bound.next_index, 13)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_unit_next_is_plus_one(self):
        bound = bind_stride("admit", 1, from_index=0, slot=_SLOT)
        self.assertEqual(bound.family, UNIT)
        self.assertEqual(bound.next_index, 1)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 1, from_index=_FROM, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, from_index=_FROM, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 1, from_index=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 1, from_index=_FROM, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_stride(None, 1, from_index=_FROM, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_stride("classify", None, from_index=_FROM, slot=_SLOT)

    def test_bind_negative_from_index_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_stride("classify", 1, from_index=-1, slot=_SLOT)

    def test_bind_bool_from_index_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_stride("classify", 1, from_index=True, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_stride(
                "classify", 1, from_index=_FROM,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_stride("classify", 1, from_index=_FROM, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertTrue(halt_blocks_admit())

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

    def test_does_not_replace_seq_cursor(self):
        self.assertFalse(replaces_seq_cursor())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["stride", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_stride).parameters
        self.assertEqual(
            list(params),
            ["intent", "stride", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
