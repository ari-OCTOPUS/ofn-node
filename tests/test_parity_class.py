"""Contract tests for parity_class (P1 complementary).

A parity family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.parity_class import (
    CLASSIFY,
    EVEN,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    ODD,
    RECORD,
    UNKNOWN,
    ParityBind,
    admit_parity,
    bind_parity,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    even_is_authorized,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_record,
    later_disarm_supersedes,
    mints_run_id,
    odd_is_false,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-par-0001"


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("record"), RECORD)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(
            INTENTS, frozenset({RECORD, CLASSIFY, OBSERVE, INSPECT}))

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
            classify_intent("consume")
        with self.assertRaises(FailClosedError):
            classify_intent("send")
        with self.assertRaises(FailClosedError):
            classify_intent("reserve")

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
        self.assertEqual(classify_family(0), EVEN)
        self.assertEqual(classify_family(2), EVEN)
        self.assertEqual(classify_family(1), ODD)
        self.assertEqual(classify_family(7), ODD)
        self.assertEqual(FAMILIES, frozenset({EVEN, ODD}))

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(classify_family(None), EVEN)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(2, timeout=True))
        self.assertIsNone(classify_family(1, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(2, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(2, timeout=1)

    def test_bool_count_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_negative_count_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(2.0)  # type: ignore[arg-type]

    def test_even_is_not_authorized(self):
        self.assertEqual(classify_family(4), EVEN)
        self.assertFalse(even_is_authorized())

    def test_odd_is_not_false(self):
        self.assertEqual(classify_family(3), ODD)
        self.assertFalse(odd_is_false())


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_parity("classify", 3, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_parity("observe", 4, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_parity("inspect", 1, halted=True), True)

    def test_admit_record_refused_when_halted(self):
        self.assertIs(admit_parity("record", 2, halted=True), False)
        self.assertIs(admit_parity("record", 2, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_parity("record", 2, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_parity(None, 2))
        self.assertIsNone(admit_parity("classify", None))

    def test_admit_odd_is_not_a_send_false(self):
        self.assertIs(admit_parity("classify", 3), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_parity("classify", 2, halted="yes")

    def test_bind_records_even(self):
        bound = bind_parity("classify", 4, slot=_SLOT)
        self.assertIsInstance(bound, ParityBind)
        self.assertEqual(bound.family, EVEN)
        self.assertEqual(bound.count, 4)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_records_odd(self):
        bound = bind_parity("classify", 5, slot=_SLOT)
        self.assertEqual(bound.family, ODD)
        self.assertEqual(bound.count, 5)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 2, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 2, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_parity(None, 2, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_parity("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_parity("classify", 2, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_parity("classify", 2, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_record())

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
        self.assertEqual(list(params), ["count", "timeout"])
        for forbidden in (
            "halted", "now", "modulus", "remainder", "resend",
            "send_authorized", "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_parity).parameters
        self.assertEqual(
            list(params),
            ["intent", "count", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
