"""Contract tests for front_class (P1 complementary).

A signed-depth family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.front_class import (
    AT,
    BACK,
    CLASSIFY,
    FAMILIES,
    FRONT,
    INSPECT,
    INTENTS,
    MARK,
    OBSERVE,
    UNKNOWN,
    FrontBind,
    admit_front,
    at_is_back,
    at_is_front,
    at_is_send,
    back_is_authorized,
    bind_front,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    front_is_send,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_mark,
    halt_blocks_observe,
    later_disarm_supersedes,
    missing_signed_is_zero,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    signed_of,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-front-0001"
_PLANE = 10


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
            classify_intent("left")

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
        self.assertEqual(classify_family(10, plane=_PLANE), AT)
        self.assertEqual(classify_family(7, plane=_PLANE), BACK)
        self.assertEqual(classify_family(14, plane=_PLANE), FRONT)
        self.assertEqual(FAMILIES, frozenset({AT, BACK, FRONT}))

    def test_at_records_zero_signed(self):
        self.assertEqual(classify_family(10, plane=_PLANE), AT)
        self.assertEqual(signed_of(10, plane=_PLANE), 0)

    def test_back_is_behind_plane(self):
        self.assertEqual(classify_family(7, plane=_PLANE), BACK)
        self.assertEqual(signed_of(7, plane=_PLANE), -3)
        self.assertEqual(classify_family(9, plane=_PLANE), BACK)

    def test_front_is_ahead_of_plane(self):
        self.assertEqual(classify_family(14, plane=_PLANE), FRONT)
        self.assertEqual(signed_of(14, plane=_PLANE), 4)

    def test_plane_coincidence_is_at_never_back_or_front(self):
        self.assertEqual(classify_family(5, plane=5), AT)
        self.assertFalse(at_is_back())
        self.assertFalse(at_is_front())

    def test_signed_depth_is_allowed(self):
        self.assertEqual(classify_family(-1, plane=0), BACK)
        self.assertEqual(classify_family(4, plane=0), FRONT)
        self.assertEqual(signed_of(-1, plane=0), -1)
        self.assertEqual(signed_of(4, plane=0), 4)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, plane=_PLANE))
        self.assertIsNone(classify_family(10, plane=None))
        self.assertIsNone(signed_of(None, plane=_PLANE))
        self.assertIsNot(classify_family(None, plane=_PLANE), False)
        self.assertIsNot(signed_of(None, plane=_PLANE), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(10, plane=_PLANE, timeout=True))
        self.assertIsNone(signed_of(10, plane=_PLANE, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, plane=_PLANE, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(10, plane=_PLANE, timeout=1)

    def test_bool_depth_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, plane=_PLANE)
        with self.assertRaises(FailClosedError):
            classify_family(False, plane=_PLANE)

    def test_bool_plane_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, plane=True)
        with self.assertRaises(FailClosedError):
            classify_family(10, plane=False)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10.0, plane=_PLANE)
        with self.assertRaises(FailClosedError):
            classify_family(10, plane=10.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_front("classify", 7, plane=_PLANE, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_front("observe", 7, plane=_PLANE, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_front("inspect", 14, plane=_PLANE, halted=True),
            True)

    def test_admit_mark_refused_when_halted(self):
        self.assertIs(
            admit_front("mark", 7, plane=_PLANE, halted=True),
            False)
        self.assertIs(
            admit_front("mark", 7, plane=_PLANE, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_front("mark", 7, plane=_PLANE, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_front(None, 7, plane=_PLANE))
        self.assertIsNone(admit_front("classify", None, plane=_PLANE))
        self.assertIsNone(admit_front("classify", 7, plane=None))

    def test_admit_front_is_not_a_send_false(self):
        self.assertIs(
            admit_front("classify", 14, plane=_PLANE),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_front("classify", 10, plane=_PLANE, halted="yes")

    def test_bind_records_signed(self):
        bound = bind_front("classify", 7, plane=_PLANE, slot=_SLOT)
        self.assertIsInstance(bound, FrontBind)
        self.assertEqual(bound.family, BACK)
        self.assertEqual(bound.signed, -3)
        self.assertEqual(bound.depth, 7)
        self.assertEqual(bound.plane, _PLANE)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 10, plane=_PLANE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, plane=_PLANE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, plane=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, plane=_PLANE, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_front(None, 10, plane=_PLANE, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_front("classify", None, plane=_PLANE, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_front(
                "classify", 10, plane=_PLANE,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_front("classify", 10, plane=_PLANE, slot="")


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
        self.assertFalse(back_is_authorized())
        self.assertFalse(front_is_send())
        self.assertFalse(at_is_back())
        self.assertFalse(at_is_front())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["depth", "plane", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready", "radius",
            "index", "origin",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_front).parameters
        self.assertEqual(
            list(params),
            ["intent", "depth", "plane", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready", "radius", "index", "origin",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
