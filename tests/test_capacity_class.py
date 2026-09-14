"""Contract tests for capacity_class (P1 complementary).

An occupancy family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.capacity_class import (
    CLASSIFY,
    EMPTY,
    FAMILIES,
    FULL,
    HAS_ROOM,
    INSPECT,
    INTENTS,
    OBSERVE,
    OVER_CAP,
    RESERVE,
    UNKNOWN,
    CapacityBind,
    admit_capacity,
    bind_capacity,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_reserve,
    later_disarm_supersedes,
    mints_run_id,
    over_cap_is_negative,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    room_is_zero,
    room_of,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_SLOT = "env-cap-0001"
_LIMIT = 8


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("reserve"), RESERVE)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(
            INTENTS, frozenset({RESERVE, CLASSIFY, OBSERVE, INSPECT}))

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
        self.assertEqual(classify_family(0, limit=_LIMIT), EMPTY)
        self.assertEqual(classify_family(3, limit=_LIMIT), HAS_ROOM)
        self.assertEqual(classify_family(_LIMIT, limit=_LIMIT), FULL)
        self.assertEqual(classify_family(9, limit=_LIMIT), OVER_CAP)
        self.assertEqual(
            FAMILIES, frozenset({EMPTY, HAS_ROOM, FULL, OVER_CAP}))

    def test_empty_records_full_room(self):
        self.assertEqual(room_of(0, limit=_LIMIT), _LIMIT)

    def test_has_room_records_remaining(self):
        self.assertEqual(room_of(3, limit=_LIMIT), 5)

    def test_full_records_zero_room(self):
        self.assertEqual(room_of(_LIMIT, limit=_LIMIT), 0)

    def test_over_cap_room_is_none_not_negative(self):
        self.assertIsNone(room_of(9, limit=_LIMIT))
        self.assertFalse(over_cap_is_negative())

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, limit=_LIMIT))
        self.assertIsNone(classify_family(3, limit=None))
        self.assertIsNone(room_of(None, limit=_LIMIT))
        self.assertIsNot(classify_family(None, limit=_LIMIT), False)
        self.assertIsNot(room_of(None, limit=_LIMIT), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(3, limit=_LIMIT, timeout=True))
        self.assertIsNone(room_of(3, limit=_LIMIT, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, limit=_LIMIT, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(3, limit=_LIMIT, timeout=1)

    def test_bool_used_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, limit=_LIMIT)
        with self.assertRaises(FailClosedError):
            classify_family(False, limit=_LIMIT)

    def test_bool_limit_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3, limit=True)
        with self.assertRaises(FailClosedError):
            classify_family(3, limit=False)

    def test_negative_used_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, limit=_LIMIT)

    def test_zero_limit_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(0, limit=0)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(3.0, limit=_LIMIT)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            classify_family(3, limit=8.0)  # type: ignore[arg-type]


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_capacity("classify", 9, limit=_LIMIT, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_capacity("observe", 9, limit=_LIMIT, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_capacity("inspect", 9, limit=_LIMIT, halted=True),
            True)

    def test_admit_reserve_refused_when_halted(self):
        self.assertIs(
            admit_capacity("reserve", 3, limit=_LIMIT, halted=True),
            False)
        self.assertIs(
            admit_capacity("reserve", 3, limit=_LIMIT, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_capacity("reserve", 3, limit=_LIMIT, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_capacity(None, 3, limit=_LIMIT))
        self.assertIsNone(admit_capacity("classify", None, limit=_LIMIT))
        self.assertIsNone(admit_capacity("classify", 3, limit=None))

    def test_admit_over_cap_is_not_a_send_false(self):
        self.assertIs(admit_capacity("classify", 9, limit=_LIMIT), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_capacity("classify", 3, limit=_LIMIT, halted="yes")

    def test_bind_records_room(self):
        bound = bind_capacity("classify", 3, limit=_LIMIT, slot=_SLOT)
        self.assertIsInstance(bound, CapacityBind)
        self.assertEqual(bound.family, HAS_ROOM)
        self.assertEqual(bound.room, 5)
        self.assertEqual(bound.used, 3)
        self.assertEqual(bound.limit, _LIMIT)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_over_cap_room_is_none(self):
        bound = bind_capacity("classify", 9, limit=_LIMIT, slot=_SLOT)
        self.assertEqual(bound.family, OVER_CAP)
        self.assertIsNone(bound.room)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 3, limit=_LIMIT, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, limit=_LIMIT, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 3, limit=None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 3, limit=_LIMIT, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_capacity(None, 3, limit=_LIMIT, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_capacity("classify", None, limit=_LIMIT, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_capacity(
                "classify", 3, limit=_LIMIT,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_capacity("classify", 3, limit=_LIMIT, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_reserve())

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

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["used", "limit", "timeout"])
        for forbidden in (
            "halted", "now", "add", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_capacity).parameters
        self.assertEqual(
            list(params),
            ["intent", "used", "limit", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
