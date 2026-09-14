"""Contract tests for coprime_class (P1 complementary).

A gcd family is not a send. Missing is UNKNOWN, not FALSE
and not 0. Timeout does not prove a writer. Ready is not
authorized. Distinct from prime/composite, even/odd,
remainder/leftover, min/max, sign/magnitude.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.coprime_class import (
    CLASSIFY,
    COMMON,
    COPRIME,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    SAMPLE,
    UNKNOWN,
    CoprimeBind,
    admit_coprime,
    bind_coprime,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    gcd_of,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    later_disarm_supersedes,
    measured_one_is_unknown,
    missing_gcd_is_zero,
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

_SLOT = "env-cop-0001"


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
        self.assertEqual(classify_family(8, right=9), COPRIME)
        self.assertEqual(classify_family(8, right=12), COMMON)
        self.assertEqual(FAMILIES, frozenset({COPRIME, COMMON}))

    def test_gcd_one_is_coprime_never_unknown(self):
        self.assertEqual(classify_family(8, right=9), COPRIME)
        self.assertEqual(gcd_of(8, right=9), 1)
        self.assertFalse(measured_one_is_unknown())

    def test_gcd_greater_than_one_is_common(self):
        self.assertEqual(classify_family(8, right=12), COMMON)
        self.assertEqual(gcd_of(8, right=12), 4)

    def test_unit_pair_is_coprime(self):
        self.assertEqual(classify_family(1, right=1), COPRIME)
        self.assertEqual(gcd_of(1, right=1), 1)

    def test_same_composite_is_common(self):
        self.assertEqual(classify_family(7, right=7), COMMON)
        self.assertEqual(gcd_of(7, right=7), 7)

    def test_zero_and_one_is_coprime(self):
        self.assertEqual(classify_family(0, right=1), COPRIME)
        self.assertEqual(classify_family(1, right=0), COPRIME)
        self.assertEqual(gcd_of(0, right=1), 1)

    def test_zero_and_nonzero_gt_one_is_common(self):
        self.assertEqual(classify_family(0, right=5), COMMON)
        self.assertEqual(gcd_of(0, right=5), 5)

    def test_zero_zero_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_family(0, right=0)
        self.assertIn("0, 0", str(ctx.exception))
        with self.assertRaises(FailClosedError):
            gcd_of(0, right=0)

    def test_negatives_use_abs(self):
        self.assertEqual(classify_family(-8, right=12), COMMON)
        self.assertEqual(gcd_of(-8, right=12), 4)
        self.assertEqual(classify_family(-8, right=-9), COPRIME)
        self.assertEqual(gcd_of(-8, right=-9), 1)

    def test_missing_is_none_not_false_or_zero(self):
        self.assertIsNone(classify_family(None, right=9))
        self.assertIsNone(classify_family(8, right=None))
        self.assertIsNone(gcd_of(None, right=9))
        self.assertIsNot(classify_family(None, right=9), False)
        self.assertIsNot(gcd_of(None, right=9), 0)
        self.assertFalse(missing_gcd_is_zero())

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(8, right=9, timeout=True))
        self.assertIsNone(gcd_of(8, right=9, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(8, right=9, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(8, right=9, timeout=1)

    def test_bool_left_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, right=9)
        with self.assertRaises(FailClosedError):
            classify_family(False, right=9)

    def test_bool_right_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(8, right=True)
        with self.assertRaises(FailClosedError):
            classify_family(8, right=False)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(8.0, right=9)
        with self.assertRaises(FailClosedError):
            classify_family(8, right=9.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_coprime("classify", 8, right=12, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_coprime("observe", 8, right=12, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_coprime("inspect", 8, right=9, halted=True),
            True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(
            admit_coprime("sample", 8, right=9, halted=True),
            False)
        self.assertIs(
            admit_coprime("sample", 8, right=9, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_coprime("sample", 8, right=9, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_coprime(None, 8, right=9))
        self.assertIsNone(admit_coprime("classify", None, right=9))
        self.assertIsNone(admit_coprime("classify", 8, right=None))

    def test_admit_common_is_not_a_send_false(self):
        self.assertIs(admit_coprime("classify", 8, right=12), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_coprime("classify", 8, right=9, halted="yes")

    def test_bind_records_gcd(self):
        bound = bind_coprime("classify", 8, right=12, slot=_SLOT)
        self.assertIsInstance(bound, CoprimeBind)
        self.assertEqual(bound.family, COMMON)
        self.assertEqual(bound.gcd, 4)
        self.assertEqual(bound.left, 8)
        self.assertEqual(bound.right, 12)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 8, right=9, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, right=9, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 8, right=None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 8, right=9, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_coprime(None, 8, right=9, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_coprime("classify", None, right=9, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_coprime(
                "classify", 8, right=9, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_coprime("classify", 8, right=9, slot="")

    def test_bind_zero_zero_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_coprime("classify", 0, right=0, slot=_SLOT)


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

    def test_missing_gcd_is_not_zero(self):
        self.assertFalse(missing_gcd_is_zero())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["left", "right", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_coprime).parameters
        self.assertEqual(
            list(params),
            ["intent", "left", "right", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
