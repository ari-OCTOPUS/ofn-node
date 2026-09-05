"""Contract tests for byte_class (P1 complementary).

A payload length family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.byte_class import (
    BOUNDED,
    CLASSIFY,
    EMPTY,
    FAMILIES,
    INTENTS,
    MEASURE,
    OBSERVE,
    OVERSIZE,
    UNKNOWN,
    ByteBind,
    admit_bytes,
    bind_bytes,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_measure,
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
from ofn.kernel.errors import FailClosedError

_SLOT = "env-byte-0001"
_BOUND = 8


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("measure"), MEASURE)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(INTENTS, frozenset({MEASURE, CLASSIFY, OBSERVE}))

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
        self.assertEqual(classify_family(b"", bound=_BOUND), EMPTY)
        self.assertEqual(classify_family(b"abcd", bound=_BOUND), BOUNDED)
        self.assertEqual(
            classify_family(b"0123456789", bound=_BOUND), OVERSIZE)
        self.assertEqual(FAMILIES, frozenset({EMPTY, BOUNDED, OVERSIZE}))

    def test_exact_bound_is_bounded(self):
        self.assertEqual(classify_family(b"12345678", bound=8), BOUNDED)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, bound=_BOUND))
        self.assertIsNot(classify_family(None, bound=_BOUND), False)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(b"abcd", bound=_BOUND, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(b"ab", bound=_BOUND, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(b"ab", bound=_BOUND, timeout=1)

    def test_str_is_not_bytes(self):
        with self.assertRaises(FailClosedError):
            classify_family("abcd", bound=_BOUND)

    def test_bytearray_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(bytearray(b"ab"), bound=_BOUND)

    def test_bool_bound_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(b"ab", bound=True)
        with self.assertRaises(FailClosedError):
            classify_family(b"ab", bound=False)

    def test_negative_bound_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(b"ab", bound=-1)

    def test_zero_bound_empty_ok_nonzero_oversize(self):
        self.assertEqual(classify_family(b"", bound=0), EMPTY)
        self.assertEqual(classify_family(b"x", bound=0), OVERSIZE)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_bytes("classify", b"ab", bound=_BOUND, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_bytes("observe", b"ab", bound=_BOUND, halted=True),
            True)

    def test_admit_measure_refused_when_halted(self):
        self.assertIs(
            admit_bytes("measure", b"ab", bound=_BOUND, halted=True),
            False)
        self.assertIs(
            admit_bytes("measure", b"ab", bound=_BOUND, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_bytes("measure", b"ab", bound=_BOUND, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_bytes(None, b"ab", bound=_BOUND))
        self.assertIsNone(admit_bytes("classify", None, bound=_BOUND))

    def test_admit_oversize_is_not_a_send_false(self):
        self.assertIs(
            admit_bytes("classify", b"0123456789", bound=_BOUND),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_bytes("classify", b"ab", bound=_BOUND, halted="yes")

    def test_bind_records_size(self):
        bound = bind_bytes("classify", b"abcd", bound=_BOUND, slot=_SLOT)
        self.assertIsInstance(bound, ByteBind)
        self.assertEqual(bound.family, BOUNDED)
        self.assertEqual(bound.size, 4)
        self.assertEqual(bound.bound, _BOUND)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, b"ab", bound=_BOUND, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, bound=_BOUND, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", b"ab", bound=_BOUND, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_bytes(None, b"ab", bound=_BOUND, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_bytes("classify", None, bound=_BOUND, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_bytes(
                "classify", b"ab", bound=_BOUND,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_bytes("classify", b"ab", bound=_BOUND, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertTrue(halt_blocks_measure())

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

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["payload", "bound", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_bytes).parameters
        self.assertEqual(
            list(params),
            ["intent", "payload", "bound", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
