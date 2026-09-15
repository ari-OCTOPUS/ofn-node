"""Contract tests for quorum_class (P1 complementary).

A quorum family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
required < 1 fails closed. This is a decision threshold, not
occupancy vs limit and not even/odd.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.quorum_class import (
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    QUORUM,
    RECORD,
    SHORT,
    UNKNOWN,
    QuorumBind,
    admit_quorum,
    bind_quorum,
    claims_immutable,
    classify_intent,
    classify_threshold,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_record,
    later_disarm_supersedes,
    lowering_required_satisfies,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    quorum_is_authorized,
    ready_is_authorized,
    short_is_false,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
    zero_required_satisfies,
)

_SEAT = "env-qrm-0001"


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


class ClassifyThreshold(unittest.TestCase):
    def test_closed_families(self):
        self.assertEqual(classify_threshold(3, 3), QUORUM)
        self.assertEqual(classify_threshold(4, 3), QUORUM)
        self.assertEqual(classify_threshold(2, 3), SHORT)
        self.assertEqual(classify_threshold(0, 1), SHORT)
        self.assertEqual(FAMILIES, frozenset({QUORUM, SHORT}))

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_threshold(None, 3))
        self.assertIsNone(classify_threshold(3, None))
        self.assertIsNone(classify_threshold(None, None))
        self.assertIsNot(classify_threshold(None, 3), False)
        self.assertIsNot(classify_threshold(None, 3), QUORUM)
        self.assertIsNot(classify_threshold(None, 3), SHORT)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_threshold(3, 3, timeout=True))
        self.assertIsNone(classify_threshold(1, 3, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_threshold(3, 3, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_threshold(3, 3, timeout=1)

    def test_bool_present_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_threshold(True, 1)
        with self.assertRaises(FailClosedError):
            classify_threshold(False, 1)

    def test_bool_required_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_threshold(1, True)
        with self.assertRaises(FailClosedError):
            classify_threshold(1, False)

    def test_negative_present_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_threshold(-1, 1)

    def test_zero_required_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_threshold(0, 0)
        self.assertFalse(zero_required_satisfies())
        self.assertFalse(lowering_required_satisfies())

    def test_negative_required_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_threshold(1, -1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_threshold(3.0, 3)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            classify_threshold(3, 3.0)  # type: ignore[arg-type]

    def test_quorum_is_not_authorized(self):
        self.assertEqual(classify_threshold(5, 3), QUORUM)
        self.assertFalse(quorum_is_authorized())

    def test_short_is_not_false(self):
        self.assertEqual(classify_threshold(1, 3), SHORT)
        self.assertFalse(short_is_false())

    def test_not_occupancy_or_parity(self):
        # 2 vs 3 is SHORT (threshold), not "room remaining = 1"
        # and not even/odd of 2.
        self.assertEqual(classify_threshold(2, 3), SHORT)
        self.assertNotEqual(classify_threshold(2, 3), "even")
        self.assertNotEqual(classify_threshold(2, 3), "odd")
        self.assertNotEqual(classify_threshold(2, 3), "room")


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_quorum("classify", 2, 3, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_quorum("observe", 3, 3, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_quorum("inspect", 0, 1, halted=True), True)

    def test_admit_record_refused_when_halted(self):
        self.assertIs(admit_quorum("record", 3, 3, halted=True), False)
        self.assertIs(admit_quorum("record", 3, 3, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_quorum("record", 3, 3, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_quorum(None, 3, 3))
        self.assertIsNone(admit_quorum("classify", None, 3))
        self.assertIsNone(admit_quorum("classify", 3, None))

    def test_admit_short_is_not_a_send_false(self):
        self.assertIs(admit_quorum("classify", 1, 3), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_quorum("classify", 3, 3, halted="yes")

    def test_bind_records_quorum(self):
        bound = bind_quorum("classify", 3, 3, seat=_SEAT)
        self.assertIsInstance(bound, QuorumBind)
        self.assertEqual(bound.family, QUORUM)
        self.assertEqual(bound.present, 3)
        self.assertEqual(bound.required, 3)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.seat, _SEAT)

    def test_bind_records_short(self):
        bound = bind_quorum("classify", 1, 3, seat=_SEAT)
        self.assertEqual(bound.family, SHORT)
        self.assertEqual(bound.present, 1)
        self.assertEqual(bound.required, 3)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 3, 3, seat=_SEAT))
        self.assertIsNone(try_bind("classify", None, 3, seat=_SEAT))
        self.assertIsNone(try_bind("classify", 3, None, seat=_SEAT))
        self.assertIsNone(try_bind("classify", 3, 3, seat=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_quorum(None, 3, 3, seat=_SEAT)
        with self.assertRaises(FailClosedError):
            bind_quorum("classify", None, 3, seat=_SEAT)
        with self.assertRaises(FailClosedError):
            bind_quorum("classify", 3, None, seat=_SEAT)

    def test_bind_sealed_seat_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_quorum("classify", 3, 3, seat="campaign_envelope_ready")

    def test_bind_empty_seat_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_quorum("classify", 3, 3, seat="")


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

    def test_classify_threshold_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_threshold).parameters
        self.assertEqual(list(params), ["present", "required", "timeout"])
        for forbidden in (
            "halted", "now", "modulus", "remainder", "resend",
            "send_authorized", "quote_sent", "campaign_envelope_ready",
            "occupancy", "capacity",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_quorum).parameters
        self.assertEqual(
            list(params),
            ["intent", "present", "required", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
