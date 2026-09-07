"""Contract tests for near_class (P1 complementary).

A distance family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.near_class import (
    AT,
    CLASSIFY,
    FAMILIES,
    FAR,
    INSPECT,
    INTENTS,
    MARK,
    NEAR,
    OBSERVE,
    UNKNOWN,
    NearBind,
    admit_near,
    at_is_send,
    bind_near,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    distance_of,
    far_is_send,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_mark,
    halt_blocks_observe,
    later_disarm_supersedes,
    missing_distance_is_zero,
    mints_run_id,
    near_is_authorized,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
    zero_radius_is_near,
)

_SLOT = "env-near-0001"
_ORIGIN = 10
_RADIUS = 3


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
            classify_intent("center")

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
            classify_family(10, origin=_ORIGIN, radius=_RADIUS), AT)
        self.assertEqual(
            classify_family(12, origin=_ORIGIN, radius=_RADIUS), NEAR)
        self.assertEqual(
            classify_family(14, origin=_ORIGIN, radius=_RADIUS), FAR)
        self.assertEqual(FAMILIES, frozenset({AT, NEAR, FAR}))

    def test_at_records_zero_distance(self):
        self.assertEqual(
            classify_family(10, origin=_ORIGIN, radius=_RADIUS), AT)
        self.assertEqual(
            distance_of(10, origin=_ORIGIN, radius=_RADIUS), 0)

    def test_near_is_inside_radius_not_at(self):
        self.assertEqual(
            classify_family(7, origin=_ORIGIN, radius=_RADIUS), NEAR)
        self.assertEqual(
            distance_of(7, origin=_ORIGIN, radius=_RADIUS), 3)
        self.assertEqual(
            classify_family(13, origin=_ORIGIN, radius=_RADIUS), NEAR)

    def test_far_is_beyond_radius(self):
        self.assertEqual(
            classify_family(6, origin=_ORIGIN, radius=_RADIUS), FAR)
        self.assertEqual(
            distance_of(6, origin=_ORIGIN, radius=_RADIUS), 4)

    def test_zero_radius_is_at_or_far_never_near(self):
        self.assertEqual(classify_family(5, origin=5, radius=0), AT)
        self.assertEqual(classify_family(6, origin=5, radius=0), FAR)
        self.assertFalse(zero_radius_is_near())

    def test_signed_index_is_allowed(self):
        self.assertEqual(classify_family(-1, origin=0, radius=2), NEAR)
        self.assertEqual(classify_family(-4, origin=0, radius=2), FAR)
        self.assertEqual(distance_of(-1, origin=0, radius=2), 1)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, origin=_ORIGIN, radius=_RADIUS))
        self.assertIsNone(classify_family(10, origin=None, radius=_RADIUS))
        self.assertIsNone(classify_family(10, origin=_ORIGIN, radius=None))
        self.assertIsNone(distance_of(None, origin=_ORIGIN, radius=_RADIUS))
        self.assertIsNot(
            classify_family(None, origin=_ORIGIN, radius=_RADIUS), False)
        self.assertIsNot(distance_of(None, origin=_ORIGIN, radius=_RADIUS), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(10, origin=_ORIGIN, radius=_RADIUS, timeout=True))
        self.assertIsNone(
            distance_of(10, origin=_ORIGIN, radius=_RADIUS, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=_ORIGIN, radius=_RADIUS, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=_ORIGIN, radius=_RADIUS, timeout=1)

    def test_bool_index_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, origin=_ORIGIN, radius=_RADIUS)
        with self.assertRaises(FailClosedError):
            classify_family(False, origin=_ORIGIN, radius=_RADIUS)

    def test_bool_origin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=True, radius=_RADIUS)
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=False, radius=_RADIUS)

    def test_bool_radius_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=_ORIGIN, radius=True)
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=_ORIGIN, radius=False)

    def test_negative_radius_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=_ORIGIN, radius=-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10.0, origin=_ORIGIN, radius=_RADIUS)
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=10.0, radius=_RADIUS)
        with self.assertRaises(FailClosedError):
            classify_family(10, origin=_ORIGIN, radius=3.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_near(
                "classify", 12, origin=_ORIGIN, radius=_RADIUS, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_near(
                "observe", 12, origin=_ORIGIN, radius=_RADIUS, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_near(
                "inspect", 14, origin=_ORIGIN, radius=_RADIUS, halted=True),
            True)

    def test_admit_mark_refused_when_halted(self):
        self.assertIs(
            admit_near(
                "mark", 12, origin=_ORIGIN, radius=_RADIUS, halted=True),
            False)
        self.assertIs(
            admit_near(
                "mark", 12, origin=_ORIGIN, radius=_RADIUS, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_near(
                "mark", 12, origin=_ORIGIN, radius=_RADIUS, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(
            admit_near(None, 12, origin=_ORIGIN, radius=_RADIUS))
        self.assertIsNone(
            admit_near("classify", None, origin=_ORIGIN, radius=_RADIUS))
        self.assertIsNone(
            admit_near("classify", 12, origin=None, radius=_RADIUS))
        self.assertIsNone(
            admit_near("classify", 12, origin=_ORIGIN, radius=None))

    def test_admit_far_is_not_a_send_false(self):
        self.assertIs(
            admit_near("classify", 14, origin=_ORIGIN, radius=_RADIUS),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_near(
                "classify", 10, origin=_ORIGIN, radius=_RADIUS, halted="yes")

    def test_bind_records_distance(self):
        bound = bind_near(
            "classify", 12, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)
        self.assertIsInstance(bound, NearBind)
        self.assertEqual(bound.family, NEAR)
        self.assertEqual(bound.distance, 2)
        self.assertEqual(bound.index, 12)
        self.assertEqual(bound.origin, _ORIGIN)
        self.assertEqual(bound.radius, _RADIUS)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, 10, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, origin=None, radius=_RADIUS, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, origin=_ORIGIN, radius=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", 10, origin=_ORIGIN, radius=_RADIUS, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_near(None, 10, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_near("classify", None, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_near(
                "classify", 10, origin=_ORIGIN, radius=_RADIUS,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_near(
                "classify", 10, origin=_ORIGIN, radius=_RADIUS, slot="")


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

    def test_missing_distance_is_not_zero(self):
        self.assertFalse(missing_distance_is_zero())

    def test_families_are_not_sends(self):
        self.assertFalse(at_is_send())
        self.assertFalse(near_is_authorized())
        self.assertFalse(far_is_send())
        self.assertFalse(zero_radius_is_near())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["index", "origin", "radius", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_near).parameters
        self.assertEqual(
            list(params),
            ["intent", "index", "origin", "radius", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
