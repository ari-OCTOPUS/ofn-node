"""Contract tests for grace_class (P1 complementary).

A linger family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.grace_class import (
    CLASSIFY,
    FAMILIES,
    GRACE,
    INSPECT,
    INTENTS,
    LAPSED,
    LINGER,
    LIVE,
    OBSERVE,
    UNKNOWN,
    GraceBind,
    admit_grace,
    bind_grace,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    elapsed_is_zero,
    grace_is_send,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_linger,
    halt_blocks_observe,
    lapsed_is_false,
    later_disarm_supersedes,
    live_is_authorized,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    remaining_of,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    until_due_of,
    wires_into_run_store,
)

_SLOT = "env-grace-0001"
_DUE = 8
_LINGER = 4


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("linger"), LINGER)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(INTENTS, frozenset({LINGER, CLASSIFY, OBSERVE, INSPECT}))

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
            classify_intent("decay")

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
        self.assertEqual(
            classify_family(3, due_after=_DUE, linger_after=_LINGER), LIVE)
        self.assertEqual(
            classify_family(8, due_after=_DUE, linger_after=_LINGER), GRACE)
        self.assertEqual(
            classify_family(11, due_after=_DUE, linger_after=_LINGER), GRACE)
        self.assertEqual(
            classify_family(12, due_after=_DUE, linger_after=_LINGER), LAPSED)
        self.assertEqual(
            classify_family(0, due_after=_DUE, linger_after=_LINGER), LIVE)
        self.assertEqual(FAMILIES, frozenset({LIVE, GRACE, LAPSED}))

    def test_due_boundary_is_grace_not_live(self):
        self.assertEqual(
            classify_family(8, due_after=_DUE, linger_after=_LINGER), GRACE)
        self.assertNotEqual(
            classify_family(8, due_after=_DUE, linger_after=_LINGER), LIVE)

    def test_close_boundary_is_lapsed(self):
        self.assertEqual(
            classify_family(12, due_after=_DUE, linger_after=_LINGER), LAPSED)

    def test_live_remaining_includes_linger(self):
        self.assertEqual(
            remaining_of(3, due_after=_DUE, linger_after=_LINGER), 9)
        self.assertEqual(
            until_due_of(3, due_after=_DUE, linger_after=_LINGER), 5)

    def test_grace_remaining_until_lapse(self):
        self.assertEqual(
            remaining_of(8, due_after=_DUE, linger_after=_LINGER), 4)
        self.assertEqual(
            until_due_of(8, due_after=_DUE, linger_after=_LINGER), 0)
        self.assertEqual(
            remaining_of(11, due_after=_DUE, linger_after=_LINGER), 1)

    def test_lapsed_remaining_is_zero_not_negative(self):
        self.assertEqual(
            remaining_of(12, due_after=_DUE, linger_after=_LINGER), 0)
        self.assertEqual(
            remaining_of(20, due_after=_DUE, linger_after=_LINGER), 0)
        self.assertEqual(
            until_due_of(12, due_after=_DUE, linger_after=_LINGER), 0)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(
            classify_family(None, due_after=_DUE, linger_after=_LINGER))
        self.assertIsNone(
            classify_family(3, due_after=None, linger_after=_LINGER))
        self.assertIsNone(
            classify_family(3, due_after=_DUE, linger_after=None))
        self.assertIsNone(
            remaining_of(None, due_after=_DUE, linger_after=_LINGER))
        self.assertIsNone(
            until_due_of(None, due_after=_DUE, linger_after=_LINGER))
        self.assertIsNot(
            classify_family(None, due_after=_DUE, linger_after=_LINGER), False)
        self.assertIsNot(
            remaining_of(None, due_after=_DUE, linger_after=_LINGER), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(
                3, due_after=_DUE, linger_after=_LINGER, timeout=True))
        self.assertIsNone(
            remaining_of(
                3, due_after=_DUE, linger_after=_LINGER, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(
                3, due_after=_DUE, linger_after=_LINGER, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(
                3, due_after=_DUE, linger_after=_LINGER, timeout=1)

    def test_bool_elapsed_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, due_after=_DUE, linger_after=_LINGER)
        with self.assertRaises(FailClosedError):
            classify_family(False, due_after=_DUE, linger_after=_LINGER)

    def test_bool_due_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, due_after=True, linger_after=_LINGER)
        with self.assertRaises(FailClosedError):
            classify_family(3, due_after=False, linger_after=_LINGER)

    def test_bool_linger_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, due_after=_DUE, linger_after=True)

    def test_negative_elapsed_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, due_after=_DUE, linger_after=_LINGER)

    def test_zero_due_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, due_after=0, linger_after=_LINGER)

    def test_zero_linger_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, due_after=_DUE, linger_after=0)

    def test_negative_thresholds_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, due_after=-1, linger_after=_LINGER)
        with self.assertRaises(FailClosedError):
            classify_family(3, due_after=_DUE, linger_after=-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3.0, due_after=_DUE, linger_after=_LINGER)
        with self.assertRaises(FailClosedError):
            classify_family(3, due_after=8.0, linger_after=_LINGER)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_grace(
                "classify", 3, due_after=_DUE, linger_after=_LINGER,
                halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_grace(
                "observe", 3, due_after=_DUE, linger_after=_LINGER,
                halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_grace(
                "inspect", 3, due_after=_DUE, linger_after=_LINGER,
                halted=True),
            True)

    def test_admit_linger_refused_when_halted(self):
        self.assertIs(
            admit_grace(
                "linger", 8, due_after=_DUE, linger_after=_LINGER,
                halted=True),
            False)
        self.assertIs(
            admit_grace(
                "linger", 8, due_after=_DUE, linger_after=_LINGER,
                halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_grace(
                "linger", 8, due_after=_DUE, linger_after=_LINGER,
                timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(
            admit_grace(None, 3, due_after=_DUE, linger_after=_LINGER))
        self.assertIsNone(
            admit_grace("classify", None, due_after=_DUE, linger_after=_LINGER))
        self.assertIsNone(
            admit_grace("classify", 3, due_after=None, linger_after=_LINGER))
        self.assertIsNone(
            admit_grace("classify", 3, due_after=_DUE, linger_after=None))

    def test_admit_live_is_not_a_send_false(self):
        self.assertIs(
            admit_grace("classify", 3, due_after=_DUE, linger_after=_LINGER),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_grace(
                "classify", 3, due_after=_DUE, linger_after=_LINGER,
                halted="yes")

    def test_bind_records_live(self):
        bound = bind_grace(
            "classify", 3, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        self.assertIsInstance(bound, GraceBind)
        self.assertEqual(bound.family, LIVE)
        self.assertEqual(bound.elapsed_ticks, 3)
        self.assertEqual(bound.due_after, _DUE)
        self.assertEqual(bound.linger_after, _LINGER)
        self.assertEqual(bound.remaining, 9)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_records_grace(self):
        bound = bind_grace(
            "linger", 8, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        self.assertEqual(bound.family, GRACE)
        self.assertEqual(bound.remaining, 4)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 3, due_after=_DUE, linger_after=_LINGER, slot=_SLOT))
        self.assertIsNone(
            try_bind(
                "classify", None, due_after=_DUE, linger_after=_LINGER,
                slot=_SLOT))
        self.assertIsNone(
            try_bind(
                "classify", 3, due_after=None, linger_after=_LINGER,
                slot=_SLOT))
        self.assertIsNone(
            try_bind(
                "classify", 3, due_after=_DUE, linger_after=None, slot=_SLOT))
        self.assertIsNone(
            try_bind(
                "classify", 3, due_after=_DUE, linger_after=_LINGER, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_grace(
                None, 3, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_grace(
                "classify", None, due_after=_DUE, linger_after=_LINGER,
                slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_grace(
                "classify", 3, due_after=_DUE, linger_after=_LINGER,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_grace(
                "classify", 3, due_after=_DUE, linger_after=_LINGER, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_linger())

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

    def test_elapsed_missing_is_not_zero(self):
        self.assertFalse(elapsed_is_zero())

    def test_live_is_not_authorized(self):
        self.assertFalse(live_is_authorized())
        self.assertFalse(grace_is_send())
        self.assertFalse(lapsed_is_false())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(
            list(params),
            ["elapsed_ticks", "due_after", "linger_after", "timeout"],
        )
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_grace).parameters
        self.assertEqual(
            list(params),
            [
                "intent", "elapsed_ticks", "due_after", "linger_after",
                "halted", "timeout",
            ],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
