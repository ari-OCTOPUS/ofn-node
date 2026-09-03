"""Kernel-pure slot class — complementary to store_class / write_fence.

A proposed occupy is a START. Release and inspect are not STARTS.
Steal is never admitted. This module does not persist a row and
is not wired into the run store. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.slot_class import (
    ACTIVITIES,
    INTENTS,
    OCCUPANCIES,
    REFUSAL_REASONS,
    STATUSES,
    SlotDecision,
    admit_slot,
    claims_immutable,
    classify_status,
    classify_timeout,
    grants_send,
    halt_blocks_release,
    occupy_is_persist,
    occupy_is_write,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    steals_slot,
    timeout_proves_concurrent,
    unknown_is_false,
    wires_into_run_store,
)

_RUN = "run-1780000000-slotaaaaaa"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_release(self):
        self.assertFalse(halt_blocks_release())

    def test_occupy_is_not_persist(self):
        self.assertFalse(occupy_is_persist())

    def test_occupy_is_not_write(self):
        self.assertFalse(occupy_is_write())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_steal(self):
        self.assertFalse(steals_slot())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(admit_slot).parameters
        self.assertEqual(
            list(params),
            ["intended", "run_id", "occupancy", "activity", "halted", "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt_raw",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            SlotDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="inspect", run_id=_RUN, occupancy="empty",
                timed_out=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            SlotDecision(
                allowed=False, reason="sealed_effect", status="UNKNOWN",
                intended="inspect", run_id="send_authorized",
                occupancy="empty", timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            SlotDecision(
                allowed=True, reason="halt_start", status="VERIFIED",
                intended="occupy", run_id=_RUN, occupancy="empty",
                timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            SlotDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="occupy", run_id=_RUN, occupancy="empty",
                timed_out=False)
        with self.assertRaises(FailClosedError):
            SlotDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="occupy", run_id=_RUN, occupancy="empty",
                timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("halt_start", REFUSAL_REASONS)
        self.assertIn("already_occupied", REFUSAL_REASONS)
        self.assertIn("steal_forbidden", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_occupy_requires_verified(self):
        for status in ("SUSPECTED", "UNKNOWN"):
            with self.subTest(status=status):
                with self.assertRaises(FailClosedError):
                    SlotDecision(
                        allowed=True, reason=None, status=status,
                        intended="occupy", run_id=_RUN, occupancy="empty",
                        timed_out=False)

    def test_allowed_decision_refuses_steal(self):
        with self.assertRaises(FailClosedError):
            SlotDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="steal", run_id=_RUN, occupancy="held",
                timed_out=False)

    def test_allowed_decision_refuses_sealed_run_id(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    SlotDecision(
                        allowed=True, reason=None, status="VERIFIED",
                        intended="inspect", run_id=name, occupancy="empty",
                        timed_out=False)

    def test_non_sealed_refusal_cannot_carry_a_sealed_run_id(self):
        with self.assertRaises(FailClosedError):
            SlotDecision(
                allowed=False, reason="unknown_activity", status="UNKNOWN",
                intended="occupy", run_id="send_authorized",
                occupancy="empty", timed_out=True)

    def test_sealed_effect_refusal_names_the_subject(self):
        d = SlotDecision(
            allowed=False, reason="sealed_effect", status="UNKNOWN",
            intended="inspect", run_id="send_authorized",
            occupancy="empty", timed_out=False)
        self.assertEqual(d.run_id, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            SlotDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="inspect", run_id=_RUN, occupancy="empty",
                timed_out="false")  # type: ignore[arg-type]


class ClosedVocabularies(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))

    def test_activities(self):
        self.assertEqual(ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))

    def test_intents(self):
        self.assertEqual(INTENTS, frozenset({"occupy", "release", "inspect", "steal"}))

    def test_occupancies(self):
        self.assertEqual(OCCUPANCIES, frozenset({"empty", "held", "unknown"}))


class StatusDerivation(unittest.TestCase):
    def test_idle_is_verified(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=False), "VERIFIED")

    def test_concurrent_is_suspected(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=False),
            "SUSPECTED")

    def test_unknown_activity_is_unknown(self):
        self.assertEqual(
            classify_status(activity="unknown", timed_out=False), "UNKNOWN")

    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True), "UNKNOWN")

    def test_timeout_outranks_idle(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=True), "UNKNOWN")

    def test_unknown_activity_token_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_status(activity="racing", timed_out=False)
        self.assertNotIn("FALSE", str(ctx.exception))


class OccupyIsAStart(unittest.TestCase):
    def test_occupy_empty_idle_is_admitted(self):
        d = admit_slot(intended="occupy", run_id=_RUN)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)
        self.assertFalse(occupy_is_persist())

    def test_occupy_halted_is_refused(self):
        d = admit_slot(intended="occupy", run_id=_RUN, halted=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "halt_start")
        self.assertFalse(d.grants_send)

    def test_occupy_unknown_activity_is_refused(self):
        d = admit_slot(
            intended="occupy", run_id=_RUN, activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_occupy_concurrent_is_refused(self):
        d = admit_slot(
            intended="occupy", run_id=_RUN, activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(d.grants_send)

    def test_occupy_timeout_is_unknown_not_suspected(self):
        d = admit_slot(
            intended="occupy", run_id=_RUN,
            activity="concurrent", timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)

    def test_occupy_held_is_already_occupied(self):
        d = admit_slot(
            intended="occupy", run_id=_RUN, occupancy="held")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "already_occupied")
        self.assertFalse(d.grants_send)

    def test_occupy_unknown_occupancy_is_refused(self):
        d = admit_slot(
            intended="occupy", run_id=_RUN, occupancy="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)


class ReleaseAndInspectAreNotStarts(unittest.TestCase):
    def test_release_held_continues_under_halt(self):
        d = admit_slot(
            intended="release", run_id=_RUN, occupancy="held", halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        self.assertFalse(halt_blocks_release())

    def test_inspect_continues_under_halt(self):
        d = admit_slot(
            intended="inspect", run_id=_RUN, occupancy="held", halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_inspect_timeout_is_unknown_and_still_admitted(self):
        d = admit_slot(
            intended="inspect", run_id=_RUN, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_release_empty_is_refused(self):
        d = admit_slot(intended="release", run_id=_RUN, occupancy="empty")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "empty_slot")
        self.assertFalse(d.grants_send)

    def test_inspect_is_byte_identical(self):
        a = admit_slot(intended="inspect", run_id=_RUN, occupancy="held")
        b = admit_slot(intended="inspect", run_id=_RUN, occupancy="held")
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)
        self.assertFalse(a.grants_send)


class StealNeverAdmitted(unittest.TestCase):
    def test_steal_empty_is_refused(self):
        d = admit_slot(intended="steal", run_id=_RUN, occupancy="empty")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "steal_forbidden")
        self.assertFalse(d.grants_send)
        self.assertFalse(steals_slot())

    def test_steal_held_is_refused(self):
        d = admit_slot(intended="steal", run_id=_RUN, occupancy="held")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "steal_forbidden")
        self.assertFalse(d.grants_send)

    def test_steal_under_halt_is_still_steal_not_halt(self):
        d = admit_slot(
            intended="steal", run_id=_RUN, occupancy="held", halted=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "steal_forbidden")
        self.assertNotEqual(d.reason, "halt_start")


class ShapeAndUnknown(unittest.TestCase):
    def test_malformed_run_id_is_refused(self):
        d = admit_slot(intended="occupy", run_id="not-a-run")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "malformed_id")
        self.assertFalse(d.grants_send)

    def test_unknown_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_slot(intended="occupy", run_id=_RUN, activity="racing")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_intended_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_slot(intended="send", run_id=_RUN)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_occupancy_token_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_slot(intended="occupy", run_id=_RUN, occupancy="busy")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_empty_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_slot(intended="occupy", run_id="  ")

    def test_bool_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_slot(intended="occupy", run_id=True)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_slot(intended="occupy", run_id=_RUN, timed_out=1)
        with self.assertRaises(FailClosedError):
            admit_slot(intended="occupy", run_id=_RUN, timed_out="true")

    def test_halted_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_slot(intended="occupy", run_id=_RUN, halted=1)


class SealedNameRefusesSlot(unittest.TestCase):
    def test_sealed_run_id_aliases(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "SEND_AUTHORIZED",
            "quote-sent",
            "campaign-envelope-ready",
        ):
            with self.subTest(name=name):
                d = admit_slot(intended="inspect", run_id=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_ready_and_authorized_stay_distinct_subjects(self):
        ready = admit_slot(
            intended="inspect", run_id="campaign_envelope_ready")
        auth = admit_slot(intended="inspect", run_id="send_authorized")
        self.assertNotEqual(ready.run_id, auth.run_id)
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
