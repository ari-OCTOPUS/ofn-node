"""Contract tests for left_class (P1 complementary).

A signed-side family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.left_class import (
    AT,
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    LEFT,
    MARK,
    OBSERVE,
    RIGHT,
    UNKNOWN,
    LeftBind,
    admit_left,
    at_is_left,
    at_is_right,
    at_is_send,
    bind_left,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_mark,
    halt_blocks_observe,
    later_disarm_supersedes,
    left_is_authorized,
    missing_signed_is_zero,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    right_is_send,
    signed_of,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-left-0001"
_ORIGIN = 10


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("mark"), MARK)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(INTENTS, frozenset({MARK, CLASSIFY, OBSERVE, INSPECT}))

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
            classify_intent("near")

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
        self.assertEqual(classify_family(10, origin=_ORIGIN), AT)
        self.assertEqual(classify_family(7, origin=_ORIGIN), LEFT)
        self.assertEqual(classify_family(14, origin=_ORIGIN), RIGHT)
        self.assertEqual(FAMILIES, frozenset({AT, LEFT, RIGHT}))

    def test_at_records_zero_signed(self):
        self.assertEqual(classify_family(10, origin=_ORIGIN), AT)
        self.assertEqual(signed_of(10, origin=_ORIGIN), 0)

    def test_left_is_below_origin(self):
        self.assertEqual(classify_family(7, origin=_ORIGIN), LEFT)
        self.assertEqual(signed_of(7, origin=_ORIGIN), -3)
        self.assertEqual(classify_family(9, origin=_ORIGIN), LEFT)

    def test_right_is_above_origin(self):
        self.assertEqual(classify_family(14, origin=_ORIGIN), RIGHT)
        self.assertEqual(signed_of(14, origin=_ORIGIN), 4)

    def test_origin_coincidence_is_at_never_left_or_right(self):
        self.assertEqual(classify_family(5, origin=5), AT)
        self.assertFalse(at_is_left())
        self.assertFalse(at_is_right())

    def test_signed_index_is_allowed(self):
        self.assertEqual(classify_family(-1, origin=0), LEFT)
        self.assertEqual(classify_family(4, origin=0), RIGHT)
        self.assertEqual(signed_of(-1, origin=0), -1)
        self.assertEqual(signed_of(4, origin=0), 4)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, origin=_ORIGIN))
        self.assertIsNone(classify_family(10, origin=None))
        self.assertIsNone(signed_of(None, origin=_ORIGIN))
        self.assertIsNot(classify_family(None, origin=_ORIGIN), False)
        self.assertIsNot(signed_of(None, origin=_ORIGIN), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(10, origin=_ORIGIN, timeout=True))
        self.assertIsNone(signed_of(10, origin=_ORIGIN, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=_ORIGIN, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=_ORIGIN, timeout=1)

    def test_bool_index_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, origin=_ORIGIN)
        with self.assertRaises(FailClosedError):
            classify_family(False, origin=_ORIGIN)

    def test_bool_origin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=True)
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=False)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10.0, origin=_ORIGIN)
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=10.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_left("classify", 7, origin=_ORIGIN, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_left("observe", 7, origin=_ORIGIN, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_left("inspect", 14, origin=_ORIGIN, halted=True),
            True)

    def test_admit_mark_refused_when_halted(self):
        self.assertIs(
            admit_left("mark", 7, origin=_ORIGIN, halted=True),
            False)
        self.assertIs(
            admit_left("mark", 7, origin=_ORIGIN, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_left("mark", 7, origin=_ORIGIN, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_left(None, 7, origin=_ORIGIN))
        self.assertIsNone(admit_left("classify", None, origin=_ORIGIN))
        self.assertIsNone(admit_left("classify", 7, origin=None))

    def test_admit_right_is_not_a_send_false(self):
        self.assertIs(
            admit_left("classify", 14, origin=_ORIGIN),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_left("classify", 10, origin=_ORIGIN, halted="yes")

    def test_bind_records_signed(self):
        bound = bind_left("classify", 7, origin=_ORIGIN, slot=_SLOT)
        self.assertIsInstance(bound, LeftBind)
        self.assertEqual(bound.family, LEFT)
        self.assertEqual(bound.signed, -3)
        self.assertEqual(bound.index, 7)
        self.assertEqual(bound.origin, _ORIGIN)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 10, origin=_ORIGIN, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, origin=_ORIGIN, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, origin=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, origin=_ORIGIN, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_left(None, 10, origin=_ORIGIN, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_left("classify", None, origin=_ORIGIN, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_left(
                "classify", 10, origin=_ORIGIN,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_left("classify", 10, origin=_ORIGIN, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_mark())

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

    def test_missing_signed_is_not_zero(self):
        self.assertFalse(missing_signed_is_zero())

    def test_families_are_not_sends(self):
        self.assertFalse(at_is_send())
        self.assertFalse(left_is_authorized())
        self.assertFalse(right_is_send())
        self.assertFalse(at_is_left())
        self.assertFalse(at_is_right())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["index", "origin", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready", "radius",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_left).parameters
        self.assertEqual(
            list(params),
            ["intent", "index", "origin", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready", "radius",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
