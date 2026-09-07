"""Contract tests for carve_class (P1 complementary).

An extract family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.carve_class import (
    CARVE,
    CLASSIFY,
    FAMILIES,
    FITS,
    INSPECT,
    INTENTS,
    OBSERVE,
    OVERHANG,
    PAST,
    UNKNOWN,
    CarveBind,
    admit_carve,
    bind_carve,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    extracted_is_zero,
    extracted_of,
    grants_send,
    halt_blocks_carve,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    later_disarm_supersedes,
    mints_run_id,
    overhang_is_granted,
    past_is_granted,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_SLOT = "env-crv-0001"
_HOST = 10


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("carve"), CARVE)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(INTENTS, frozenset({CARVE, CLASSIFY, OBSERVE, INSPECT}))

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
        self.assertEqual(
            classify_family(_HOST, cut_at=0, guest_len=10), FITS)
        self.assertEqual(
            classify_family(_HOST, cut_at=8, guest_len=3), OVERHANG)
        self.assertEqual(
            classify_family(_HOST, cut_at=10, guest_len=1), PAST)
        self.assertEqual(FAMILIES, frozenset({FITS, OVERHANG, PAST}))

    def test_fits_inside_and_at_end(self):
        self.assertEqual(
            classify_family(_HOST, cut_at=0, guest_len=10), FITS)
        self.assertEqual(
            classify_family(_HOST, cut_at=8, guest_len=2), FITS)
        self.assertEqual(extracted_of(_HOST, cut_at=8, guest_len=2), 2)

    def test_empty_extract_at_end_is_fits(self):
        self.assertEqual(
            classify_family(_HOST, cut_at=10, guest_len=0), FITS)
        self.assertEqual(extracted_of(_HOST, cut_at=10, guest_len=0), 0)

    def test_empty_extract_inside_is_fits(self):
        self.assertEqual(
            classify_family(_HOST, cut_at=5, guest_len=0), FITS)
        self.assertEqual(extracted_of(_HOST, cut_at=5, guest_len=0), 0)

    def test_overhang_records_available(self):
        self.assertEqual(
            classify_family(_HOST, cut_at=8, guest_len=3), OVERHANG)
        self.assertEqual(extracted_of(_HOST, cut_at=8, guest_len=3), 2)

    def test_past_extracted_is_none_not_zero(self):
        self.assertEqual(
            classify_family(_HOST, cut_at=10, guest_len=1), PAST)
        self.assertIsNone(extracted_of(_HOST, cut_at=10, guest_len=1))
        self.assertIsNot(extracted_of(_HOST, cut_at=10, guest_len=1), 0)
        self.assertEqual(
            classify_family(_HOST, cut_at=11, guest_len=0), PAST)

    def test_empty_host_nonempty_guest_is_past(self):
        self.assertEqual(
            classify_family(0, cut_at=0, guest_len=1), PAST)
        self.assertEqual(
            classify_family(0, cut_at=0, guest_len=0), FITS)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_family(None, cut_at=0, guest_len=2))
        self.assertIsNone(classify_family(_HOST, cut_at=None, guest_len=2))
        self.assertIsNone(classify_family(_HOST, cut_at=0, guest_len=None))
        self.assertIsNone(extracted_of(None, cut_at=0, guest_len=2))
        self.assertIsNot(
            classify_family(None, cut_at=0, guest_len=2), False)
        self.assertIsNot(extracted_of(None, cut_at=0, guest_len=2), 0)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(
            classify_family(_HOST, cut_at=0, guest_len=2, timeout=True))
        self.assertIsNone(
            extracted_of(_HOST, cut_at=0, guest_len=2, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(_HOST, cut_at=0, guest_len=2, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(_HOST, cut_at=0, guest_len=2, timeout=1)

    def test_bool_sides_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True, cut_at=0, guest_len=2)
        with self.assertRaises(FailClosedError):
            classify_family(_HOST, cut_at=False, guest_len=2)
        with self.assertRaises(FailClosedError):
            classify_family(_HOST, cut_at=0, guest_len=True)

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(-1, cut_at=0, guest_len=2)
        with self.assertRaises(FailClosedError):
            classify_family(_HOST, cut_at=-1, guest_len=2)
        with self.assertRaises(FailClosedError):
            classify_family(_HOST, cut_at=0, guest_len=-1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(10.0, cut_at=0, guest_len=2)
        with self.assertRaises(FailClosedError):
            classify_family(_HOST, cut_at=0.0, guest_len=2)
        with self.assertRaises(FailClosedError):
            classify_family(_HOST, cut_at=0, guest_len=2.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(
            admit_carve(
                "classify", _HOST, cut_at=8, guest_len=3, halted=True),
            True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(
            admit_carve(
                "observe", _HOST, cut_at=8, guest_len=3, halted=True),
            True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(
            admit_carve(
                "inspect", _HOST, cut_at=8, guest_len=3, halted=True),
            True)

    def test_admit_carve_refused_when_halted(self):
        self.assertIs(
            admit_carve(
                "carve", _HOST, cut_at=0, guest_len=2, halted=True),
            False)
        self.assertIs(
            admit_carve(
                "carve", _HOST, cut_at=0, guest_len=2, halted=False),
            True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(
            admit_carve(
                "carve", _HOST, cut_at=0, guest_len=2, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(
            admit_carve(None, _HOST, cut_at=0, guest_len=2))
        self.assertIsNone(
            admit_carve("classify", None, cut_at=0, guest_len=2))
        self.assertIsNone(
            admit_carve("classify", _HOST, cut_at=None, guest_len=2))
        self.assertIsNone(
            admit_carve("classify", _HOST, cut_at=0, guest_len=None))

    def test_admit_overhang_is_not_a_send_false(self):
        self.assertIs(
            admit_carve("classify", _HOST, cut_at=8, guest_len=3),
            True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_carve(
                "classify", _HOST, cut_at=0, guest_len=2, halted="yes")

    def test_bind_records_overhang(self):
        bound = bind_carve(
            "classify", _HOST, cut_at=8, guest_len=3, slot=_SLOT)
        self.assertIsInstance(bound, CarveBind)
        self.assertEqual(bound.family, OVERHANG)
        self.assertEqual(bound.extracted, 2)
        self.assertEqual(bound.host_len, _HOST)
        self.assertEqual(bound.cut_at, 8)
        self.assertEqual(bound.guest_len, 3)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_past_extracted_is_none(self):
        bound = bind_carve(
            "inspect", _HOST, cut_at=11, guest_len=0, slot=_SLOT)
        self.assertEqual(bound.family, PAST)
        self.assertIsNone(bound.extracted)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(
            try_bind(None, _HOST, cut_at=0, guest_len=2, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, cut_at=0, guest_len=2, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", _HOST, cut_at=None, guest_len=2, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", _HOST, cut_at=0, guest_len=None, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", _HOST, cut_at=0, guest_len=2, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_carve(None, _HOST, cut_at=0, guest_len=2, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_carve("classify", None, cut_at=0, guest_len=2, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_carve(
                "classify", _HOST, cut_at=0, guest_len=2,
                slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_carve("classify", _HOST, cut_at=0, guest_len=2, slot="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_carve())

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

    def test_extracted_missing_is_not_zero(self):
        self.assertFalse(extracted_is_zero())

    def test_past_and_overhang_are_not_granted(self):
        self.assertFalse(past_is_granted())
        self.assertFalse(overhang_is_granted())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(
            list(params), ["host_len", "cut_at", "guest_len", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_carve).parameters
        self.assertEqual(
            list(params),
            ["intent", "host_len", "cut_at", "guest_len", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
