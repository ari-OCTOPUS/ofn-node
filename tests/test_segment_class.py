"""Contract tests for segment_class (P1 complementary).

A payload segment is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.segment_class import (
    BODY,
    CLASSIFY,
    CUT,
    EMPTY,
    FIT,
    HEADER,
    INTENTS,
    KINDS,
    OBSERVE,
    OVERFLOW,
    SPANS,
    TRAILER,
    UNKNOWN,
    SegmentBind,
    admit_segment,
    bind_segment,
    claims_immutable,
    classify_intent,
    classify_kind,
    classify_span,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_cut,
    halt_blocks_observe,
    later_disarm_supersedes,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-seg-0001"
_LENGTH = 8


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("cut"), CUT)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(INTENTS, frozenset({CUT, CLASSIFY, OBSERVE}))

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


class ClassifyKind(unittest.TestCase):
    def test_closed_kinds(self):
        self.assertEqual(classify_kind("header"), HEADER)
        self.assertEqual(classify_kind("body"), BODY)
        self.assertEqual(classify_kind("trailer"), TRAILER)
        self.assertEqual(KINDS, frozenset({HEADER, BODY, TRAILER}))

    def test_missing_is_unknown_not_false(self):
        self.assertEqual(classify_kind(None), UNKNOWN)
        self.assertIsNot(classify_kind(None), False)

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_kind("")

    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_kind("payload")

    def test_sealed_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_kind("send_authorized")


class ClassifySpan(unittest.TestCase):
    def test_closed_spans(self):
        self.assertEqual(classify_span(0, 3, _LENGTH), FIT)
        self.assertEqual(classify_span(3, 3, _LENGTH), EMPTY)
        self.assertEqual(classify_span(0, 9, _LENGTH), OVERFLOW)
        self.assertEqual(SPANS, frozenset({FIT, EMPTY, OVERFLOW}))

    def test_exact_end_is_fit(self):
        self.assertEqual(classify_span(0, 8, 8), FIT)

    def test_start_past_length_is_overflow(self):
        self.assertEqual(classify_span(9, 9, 8), OVERFLOW)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_span(None, 3, _LENGTH))
        self.assertIsNone(classify_span(0, None, _LENGTH))
        self.assertIsNone(classify_span(0, 3, None))
        self.assertIsNot(classify_span(None, 3, _LENGTH), False)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_span(0, 3, _LENGTH, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_span(0, 3, _LENGTH, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_span(0, 3, _LENGTH, timeout=1)

    def test_bool_offset_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_span(True, 3, _LENGTH)
        with self.assertRaises(FailClosedError):
            classify_span(0, False, _LENGTH)
        with self.assertRaises(FailClosedError):
            classify_span(0, 3, True)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_span(-1, 3, _LENGTH)
        with self.assertRaises(FailClosedError):
            classify_span(0, -1, _LENGTH)

    def test_start_after_end_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_span(5, 2, _LENGTH)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_segment(
                "classify", "header", start=0, end=3, length=_LENGTH,
                halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_segment(
                "observe", "body", start=2, end=5, length=_LENGTH,
                halted=True),
            True)

    def test_admit_cut_refused_when_halted(self):
        self.assertIs(
            admit_segment(
                "cut", "header", start=0, end=3, length=_LENGTH,
                halted=True),
            False)
        self.assertIs(
            admit_segment(
                "cut", "header", start=0, end=3, length=_LENGTH,
                halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_segment(
                "cut", "header", start=0, end=3, length=_LENGTH,
                timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(
            admit_segment(None, "header", start=0, end=3, length=_LENGTH))
        self.assertIsNone(
            admit_segment("classify", None, start=0, end=3, length=_LENGTH))
        self.assertIsNone(
            admit_segment(
                "classify", "header", start=None, end=3, length=_LENGTH))

    def test_admit_overflow_is_not_a_send_false(self):
        self.assertIs(
            admit_segment(
                "classify", "trailer", start=0, end=12, length=_LENGTH),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_segment(
                "classify", "header", start=0, end=3, length=_LENGTH,
                halted="yes")

    def test_bind_records_slice(self):
        bound = bind_segment(
            "classify", "header", start=0, end=3, length=_LENGTH, slot=_SLOT)
        self.assertIsInstance(bound, SegmentBind)
        self.assertEqual(bound.kind, HEADER)
        self.assertEqual(bound.span, FIT)
        self.assertEqual(bound.start, 0)
        self.assertEqual(bound.end, 3)
        self.assertEqual(bound.length, _LENGTH)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(
                None, "header", start=0, end=3, length=_LENGTH, slot=_SLOT))
        self.assertIsNone(
            try_bind(
                "classify", None, start=0, end=3, length=_LENGTH, slot=_SLOT))
        self.assertIsNone(
            try_bind(
                "classify", "header", start=0, end=3, length=_LENGTH,
                slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_segment(
                None, "header", start=0, end=3, length=_LENGTH, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_segment(
                "classify", None, start=0, end=3, length=_LENGTH, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_segment(
                "classify", "header", start=0, end=3, length=_LENGTH,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_segment(
                "classify", "header", start=0, end=3, length=_LENGTH,
                slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertTrue(halt_blocks_cut())

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

    def test_classify_span_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_span).parameters
        self.assertEqual(list(params), ["start", "end", "length", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_segment).parameters
        self.assertEqual(
            list(params),
            ["intent", "kind", "start", "end", "length", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
