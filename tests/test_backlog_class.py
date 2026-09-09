"""Contract tests for backlog_class (P1 complementary).

A backlog family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.backlog_class import (
    AT,
    BELOW,
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    OBSERVE,
    OVER,
    SHED,
    UNKNOWN,
    BacklogBind,
    admit_backlog,
    bind_backlog,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_shed,
    later_disarm_supersedes,
    mints_run_id,
    over_is_negative,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    room_is_zero,
    room_to_shed,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_SLOT = "env-bl-0001"
_LINE = 8


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("shed"), SHED)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(INTENTS, frozenset({SHED, CLASSIFY, OBSERVE, INSPECT}))

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
        self.assertEqual(classify_family(3, threshold=_LINE), BELOW)
        self.assertEqual(classify_family(8, threshold=_LINE), AT)
        self.assertEqual(classify_family(11, threshold=_LINE), OVER)
        self.assertEqual(classify_family(0, threshold=_LINE), BELOW)
        self.assertEqual(FAMILIES, frozenset({BELOW, AT, OVER}))

    def test_room_below_and_at(self):
        self.assertEqual(room_to_shed(3, threshold=_LINE), 5)
        self.assertEqual(room_to_shed(8, threshold=_LINE), 0)

    def test_over_room_is_unknown_not_negative(self):
        self.assertIsNone(room_to_shed(11, threshold=_LINE))
        self.assertIsNot(room_to_shed(11, threshold=_LINE), 0)
        self.assertFalse(over_is_negative())

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, threshold=_LINE))
        self.assertIsNone(classify_family(3, threshold=None))
        self.assertIsNone(room_to_shed(None, threshold=_LINE))
        self.assertIsNot(classify_family(None, threshold=_LINE), False)
        self.assertIsNot(room_to_shed(None, threshold=_LINE), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(3, threshold=_LINE, timeout=True))
        self.assertIsNone(
            room_to_shed(3, threshold=_LINE, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, threshold=_LINE, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(3, threshold=_LINE, timeout=1)

    def test_bool_depth_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, threshold=_LINE)
        with self.assertRaises(FailClosedError):
            classify_family(False, threshold=_LINE)

    def test_bool_threshold_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, threshold=True)
        with self.assertRaises(FailClosedError):
            classify_family(3, threshold=False)

    def test_negative_depth_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, threshold=_LINE)

    def test_zero_threshold_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, threshold=0)

    def test_negative_threshold_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, threshold=-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3.0, threshold=_LINE)
        with self.assertRaises(FailClosedError):
            classify_family(3, threshold=8.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_backlog("classify", 11, threshold=_LINE, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_backlog("observe", 11, threshold=_LINE, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_backlog("inspect", 11, threshold=_LINE, halted=True),
            True)

    def test_admit_shed_refused_when_halted(self):
        self.assertIs(
            admit_backlog("shed", 11, threshold=_LINE, halted=True),
            False)
        self.assertIs(
            admit_backlog("shed", 11, threshold=_LINE, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_backlog("shed", 11, threshold=_LINE, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_backlog(None, 3, threshold=_LINE))
        self.assertIsNone(admit_backlog("classify", None, threshold=_LINE))
        self.assertIsNone(admit_backlog("classify", 3, threshold=None))

    def test_admit_over_is_not_a_send_false(self):
        self.assertIs(
            admit_backlog("classify", 11, threshold=_LINE),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_backlog("classify", 3, threshold=_LINE, halted="yes")

    def test_bind_records_over(self):
        bound = bind_backlog("classify", 11, threshold=_LINE, slot=_SLOT)
        self.assertIsInstance(bound, BacklogBind)
        self.assertEqual(bound.family, OVER)
        self.assertEqual(bound.depth, 11)
        self.assertEqual(bound.threshold, _LINE)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 3, threshold=_LINE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, threshold=_LINE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 3, threshold=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 3, threshold=_LINE, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_backlog(None, 3, threshold=_LINE, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_backlog("classify", None, threshold=_LINE, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_backlog(
                "classify", 3, threshold=_LINE,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_backlog("classify", 3, threshold=_LINE, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_shed())

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

    def test_room_missing_is_not_zero(self):
        self.assertFalse(room_is_zero())
        self.assertFalse(over_is_negative())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["depth", "threshold", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_backlog).parameters
        self.assertEqual(
            list(params),
            ["intent", "depth", "threshold", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
