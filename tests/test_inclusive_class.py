"""Contract tests for inclusive_class (P1 complementary).

An inclusion family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
Exclusive + equal is OUT, not ON. Measured 0 is a family.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.inclusive_class import (
    ABOVE,
    BELOW,
    CLASSIFY,
    EXCLUSIVE,
    FAMILIES,
    INCLUSIVE,
    INSPECT,
    INTENTS,
    KINDS,
    OBSERVE,
    ON,
    OUT,
    SAMPLE,
    UNKNOWN,
    InclusiveBind,
    admit_inclusive,
    bind_inclusive,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_kind,
    classify_timeout,
    exclusive_on_bound_is_on,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    later_disarm_supersedes,
    measured_zero_is_unknown,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-inc-0001"
_BOUND = 10


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
        self.assertEqual(classify_kind("inclusive"), INCLUSIVE)
        self.assertEqual(classify_kind("exclusive"), EXCLUSIVE)
        self.assertEqual(classify_kind("INCLUSIVE"), INCLUSIVE)
        self.assertEqual(KINDS, frozenset({INCLUSIVE, EXCLUSIVE}))

    def test_missing_is_unknown_not_false(self):
        self.assertEqual(classify_kind(None), UNKNOWN)
        self.assertNotEqual(classify_kind(None), "FALSE")

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_kind("")

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_kind(True)

    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_kind("half_open")
        with self.assertRaises(FailClosedError):
            classify_kind("send")

    def test_sealed_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_kind("send_authorized")


class ClassifyFamily(unittest.TestCase):
    def test_closed_families(self):
        self.assertEqual(
            classify_family(9, bound=_BOUND, kind=INCLUSIVE), BELOW)
        self.assertEqual(
            classify_family(10, bound=_BOUND, kind=INCLUSIVE), ON)
        self.assertEqual(
            classify_family(11, bound=_BOUND, kind=INCLUSIVE), ABOVE)
        self.assertEqual(
            classify_family(10, bound=_BOUND, kind=EXCLUSIVE), OUT)
        self.assertEqual(FAMILIES, frozenset({BELOW, ON, ABOVE, OUT}))

    def test_exclusive_equal_is_out_not_on(self):
        self.assertEqual(
            classify_family(10, bound=10, kind=EXCLUSIVE), OUT)
        self.assertNotEqual(
            classify_family(10, bound=10, kind=EXCLUSIVE), ON)
        self.assertFalse(exclusive_on_bound_is_on())

    def test_measured_zero_is_a_family(self):
        self.assertEqual(classify_family(0, bound=0, kind=INCLUSIVE), ON)
        self.assertEqual(classify_family(0, bound=0, kind=EXCLUSIVE), OUT)
        self.assertEqual(classify_family(0, bound=1, kind=INCLUSIVE), BELOW)
        self.assertFalse(measured_zero_is_unknown())

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, bound=_BOUND, kind=INCLUSIVE))
        self.assertIsNone(classify_family(10, bound=None, kind=INCLUSIVE))
        self.assertIsNone(classify_family(10, bound=_BOUND, kind=None))
        self.assertIsNot(
            classify_family(None, bound=_BOUND, kind=INCLUSIVE), False)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(10, bound=_BOUND, kind=INCLUSIVE, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, bound=_BOUND, kind=INCLUSIVE, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(10, bound=_BOUND, kind=INCLUSIVE, timeout=1)

    def test_bool_value_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, bound=_BOUND, kind=INCLUSIVE)
        with self.assertRaises(FailClosedError):
            classify_family(False, bound=_BOUND, kind=INCLUSIVE)

    def test_bool_bound_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, bound=True, kind=INCLUSIVE)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10.0, bound=_BOUND, kind=INCLUSIVE)
        with self.assertRaises(FailClosedError):
            classify_family(10, bound=10.0, kind=INCLUSIVE)

    def test_negative_value_is_a_family(self):
        self.assertEqual(
            classify_family(-1, bound=0, kind=INCLUSIVE), BELOW)
        self.assertEqual(
            classify_family(-1, bound=-1, kind=EXCLUSIVE), OUT)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_inclusive(
                "classify", 9, bound=_BOUND, kind=INCLUSIVE, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_inclusive(
                "observe", 9, bound=_BOUND, kind=INCLUSIVE, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_inclusive(
                "inspect", 9, bound=_BOUND, kind=INCLUSIVE, halted=True),
            True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(
            admit_inclusive(
                "sample", 10, bound=_BOUND, kind=INCLUSIVE, halted=True),
            False)
        self.assertIs(
            admit_inclusive(
                "sample", 10, bound=_BOUND, kind=INCLUSIVE, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_inclusive(
                "sample", 10, bound=_BOUND, kind=INCLUSIVE, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(
            admit_inclusive(None, 10, bound=_BOUND, kind=INCLUSIVE))
        self.assertIsNone(
            admit_inclusive("classify", None, bound=_BOUND, kind=INCLUSIVE))
        self.assertIsNone(
            admit_inclusive("classify", 10, bound=None, kind=INCLUSIVE))
        self.assertIsNone(
            admit_inclusive("classify", 10, bound=_BOUND, kind=None))

    def test_admit_exclusive_out_is_not_a_send_false(self):
        self.assertIs(
            admit_inclusive("classify", 10, bound=_BOUND, kind=EXCLUSIVE),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_inclusive(
                "classify", 10, bound=_BOUND, kind=INCLUSIVE, halted="yes")

    def test_bind_records_out(self):
        bound = bind_inclusive(
            "classify", 10, bound=_BOUND, kind=EXCLUSIVE, slot=_SLOT)
        self.assertIsInstance(bound, InclusiveBind)
        self.assertEqual(bound.family, OUT)
        self.assertEqual(bound.kind, EXCLUSIVE)
        self.assertEqual(bound.value, 10)
        self.assertEqual(bound.bound, _BOUND)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 10, bound=_BOUND, kind=INCLUSIVE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, bound=_BOUND, kind=INCLUSIVE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, bound=None, kind=INCLUSIVE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, bound=_BOUND, kind=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, bound=_BOUND, kind=INCLUSIVE, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_inclusive(None, 10, bound=_BOUND, kind=INCLUSIVE, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_inclusive(
                "classify", None, bound=_BOUND, kind=INCLUSIVE, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_inclusive(
                "classify", 10, bound=_BOUND, kind=INCLUSIVE,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_inclusive(
                "classify", 10, bound=_BOUND, kind=INCLUSIVE, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())

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

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["value", "bound", "kind", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_inclusive).parameters
        self.assertEqual(
            list(params),
            ["intent", "value", "bound", "kind", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
