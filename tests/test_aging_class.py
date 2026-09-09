"""Contract tests for aging_class (P1 complementary).

An age family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.aging_class import (
    CLASSIFY,
    DECAY,
    DECAYED,
    DUE,
    FAMILIES,
    FRESH,
    INSPECT,
    INTENTS,
    OBSERVE,
    UNKNOWN,
    AgingBind,
    admit_aging,
    age_is_zero,
    bind_aging,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    due_is_send,
    fresh_is_authorized,
    grants_send,
    halt_blocks_classify,
    halt_blocks_decay,
    halt_blocks_inspect,
    halt_blocks_observe,
    later_disarm_supersedes,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    remaining_of,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_SLOT = "env-age-0001"
_AFTER = 8


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("decay"), DECAY)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(INTENTS, frozenset({DECAY, CLASSIFY, OBSERVE, INSPECT}))

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
        self.assertEqual(classify_family(3, decay_after=_AFTER), FRESH)
        self.assertEqual(classify_family(8, decay_after=_AFTER), DUE)
        self.assertEqual(classify_family(9, decay_after=_AFTER), DECAYED)
        self.assertEqual(classify_family(0, decay_after=_AFTER), FRESH)
        self.assertEqual(FAMILIES, frozenset({FRESH, DUE, DECAYED}))

    def test_fresh_remaining(self):
        self.assertEqual(remaining_of(3, decay_after=_AFTER), 5)

    def test_due_remaining_is_zero_not_negative(self):
        self.assertEqual(remaining_of(8, decay_after=_AFTER), 0)
        self.assertEqual(remaining_of(12, decay_after=_AFTER), 0)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, decay_after=_AFTER))
        self.assertIsNone(classify_family(3, decay_after=None))
        self.assertIsNone(remaining_of(None, decay_after=_AFTER))
        self.assertIsNot(classify_family(None, decay_after=_AFTER), False)
        self.assertIsNot(remaining_of(None, decay_after=_AFTER), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(3, decay_after=_AFTER, timeout=True))
        self.assertIsNone(
            remaining_of(3, decay_after=_AFTER, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, decay_after=_AFTER, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(3, decay_after=_AFTER, timeout=1)

    def test_bool_age_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, decay_after=_AFTER)
        with self.assertRaises(FailClosedError):
            classify_family(False, decay_after=_AFTER)

    def test_bool_decay_after_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, decay_after=True)
        with self.assertRaises(FailClosedError):
            classify_family(3, decay_after=False)

    def test_negative_age_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, decay_after=_AFTER)

    def test_zero_decay_after_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, decay_after=0)

    def test_negative_decay_after_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, decay_after=-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3.0, decay_after=_AFTER)
        with self.assertRaises(FailClosedError):
            classify_family(3, decay_after=8.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_aging("classify", 3, decay_after=_AFTER, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_aging("observe", 3, decay_after=_AFTER, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_aging("inspect", 3, decay_after=_AFTER, halted=True),
            True)

    def test_admit_decay_refused_when_halted(self):
        self.assertIs(
            admit_aging("decay", 8, decay_after=_AFTER, halted=True),
            False)
        self.assertIs(
            admit_aging("decay", 8, decay_after=_AFTER, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_aging("decay", 8, decay_after=_AFTER, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_aging(None, 3, decay_after=_AFTER))
        self.assertIsNone(admit_aging("classify", None, decay_after=_AFTER))
        self.assertIsNone(admit_aging("classify", 3, decay_after=None))

    def test_admit_fresh_is_not_a_send_false(self):
        self.assertIs(
            admit_aging("classify", 3, decay_after=_AFTER),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_aging("classify", 3, decay_after=_AFTER, halted="yes")

    def test_bind_records_age(self):
        bound = bind_aging("classify", 3, decay_after=_AFTER, slot=_SLOT)
        self.assertIsInstance(bound, AgingBind)
        self.assertEqual(bound.family, FRESH)
        self.assertEqual(bound.age_ticks, 3)
        self.assertEqual(bound.decay_after, _AFTER)
        self.assertEqual(bound.remaining, 5)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 3, decay_after=_AFTER, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, decay_after=_AFTER, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 3, decay_after=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 3, decay_after=_AFTER, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_aging(None, 3, decay_after=_AFTER, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_aging("classify", None, decay_after=_AFTER, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_aging(
                "classify", 3, decay_after=_AFTER,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_aging("classify", 3, decay_after=_AFTER, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_decay())

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

    def test_age_missing_is_not_zero(self):
        self.assertFalse(age_is_zero())

    def test_fresh_is_not_authorized(self):
        self.assertFalse(fresh_is_authorized())
        self.assertFalse(due_is_send())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["age_ticks", "decay_after", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_aging).parameters
        self.assertEqual(
            list(params),
            ["intent", "age_ticks", "decay_after", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
