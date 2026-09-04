"""Kernel-pure version class — complementary to envelope.py / envelope_class.

A proposed admit is a START. Classify is not a START.
This module does not mint a run_id and is not wired into the
run store. Ready is not authorized. Unknown version is not FALSE.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.version_class import (
    ACTIVITIES,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    SUPPORTED_VERSION,
    VERSION_CLASSES,
    VersionDecision,
    admit_version,
    claims_immutable,
    classify_status,
    classify_timeout,
    classify_version,
    copies_envelope_class,
    grants_send,
    halt_blocks_classify,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rewrites_supported_version,
    timeout_proves_concurrent,
    unknown_is_false,
    unknown_version_is_false,
    wires_into_run_store,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_does_not_mint_run_id(self):
        self.assertFalse(mints_run_id())

    def test_does_not_rewrite_supported_version(self):
        self.assertFalse(rewrites_supported_version())
        self.assertEqual(SUPPORTED_VERSION, 1)

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_version_is_not_false(self):
        self.assertFalse(unknown_version_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_does_not_copy_envelope_class(self):
        self.assertFalse(copies_envelope_class())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(admit_version).parameters
        self.assertEqual(
            list(params),
            ["intended", "version", "activity", "halted", "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt_raw",
            "run_id",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            VersionDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="admit", version_class="SUPPORTED",
                timed_out=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            VersionDecision(
                allowed=False, reason="sealed_effect", status="UNKNOWN",
                intended="classify", version_class="UNKNOWN",
                timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            VersionDecision(
                allowed=True, reason="halt_active", status="VERIFIED",
                intended="admit", version_class="SUPPORTED", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            VersionDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="admit", version_class="SUPPORTED", timed_out=False)
        with self.assertRaises(FailClosedError):
            VersionDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="admit", version_class="SUPPORTED", timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("halt_active", REFUSAL_REASONS)
        self.assertIn("unknown_version", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_admit_requires_verified_and_supported(self):
        with self.assertRaises(FailClosedError):
            VersionDecision(
                allowed=True, reason=None, status="UNKNOWN",
                intended="admit", version_class="SUPPORTED", timed_out=False)
        with self.assertRaises(FailClosedError):
            VersionDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="admit", version_class="UNKNOWN_VERSION",
                timed_out=False)

    def test_closed_vocabularies(self):
        self.assertEqual(INTENTS, frozenset({"classify", "admit"}))
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))
        self.assertEqual(ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))
        self.assertEqual(
            VERSION_CLASSES,
            frozenset({"SUPPORTED", "UNKNOWN_VERSION", "UNKNOWN"}),
        )


class ClassifyVersion(unittest.TestCase):
    def test_none_is_unknown_not_zero(self):
        self.assertEqual(classify_version(None), "UNKNOWN")
        self.assertNotEqual(classify_version(None), 0)
        self.assertNotEqual(classify_version(None), "FALSE")

    def test_one_is_supported(self):
        self.assertEqual(classify_version(1), "SUPPORTED")

    def test_other_int_is_unknown_version_not_false(self):
        self.assertEqual(classify_version(2), "UNKNOWN_VERSION")
        self.assertEqual(classify_version(0), "UNKNOWN_VERSION")
        self.assertEqual(classify_version(-1), "UNKNOWN_VERSION")
        self.assertFalse(unknown_version_is_false())

    def test_bool_str_float_fail_closed(self):
        for bad in (True, False, "1", 1.0, "SUPPORTED"):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    classify_version(bad)

    def test_sealed_name_fails_closed(self):
        for name in (
            "send_authorized", "quote_sent", "campaign_envelope_ready",
            "send-authorized", "SEND_AUTHORIZED",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError) as ctx:
                    classify_version(name)
                self.assertIn("sealed", str(ctx.exception).lower())


class ClassifyStatus(unittest.TestCase):
    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True),
            "UNKNOWN",
        )
        self.assertNotEqual(
            classify_status(activity="concurrent", timed_out=True),
            "SUSPECTED",
        )

    def test_idle_verified(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=False), "VERIFIED")

    def test_unknown_activity_unknown(self):
        self.assertEqual(
            classify_status(activity="unknown", timed_out=False), "UNKNOWN")

    def test_concurrent_suspected(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=False),
            "SUSPECTED",
        )


class AdmitClassifyContinues(unittest.TestCase):
    def test_classify_supported_allowed(self):
        d = admit_version(intended="classify", version=1)
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertEqual(d.version_class, "SUPPORTED")
        self.assertEqual(d.status, "VERIFIED")
        self.assertFalse(d.grants_send)

    def test_classify_unknown_version_still_allowed(self):
        d = admit_version(intended="classify", version=2)
        self.assertTrue(d.allowed)
        self.assertEqual(d.version_class, "UNKNOWN_VERSION")
        self.assertFalse(d.grants_send)

    def test_classify_missing_is_unknown_and_allowed(self):
        d = admit_version(intended="classify", version=None)
        self.assertTrue(d.allowed)
        self.assertEqual(d.version_class, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_classify_continues_under_halt(self):
        d = admit_version(intended="classify", version=1, halted=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.version_class, "SUPPORTED")
        self.assertFalse(d.grants_send)
        self.assertFalse(halt_blocks_classify())

    def test_classify_timeout_is_unknown_not_suspected(self):
        d = admit_version(
            intended="classify", version=1, activity="concurrent",
            timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class AdmitIsAStart(unittest.TestCase):
    def test_admit_supported_idle(self):
        d = admit_version(intended="admit", version=1)
        self.assertTrue(d.allowed)
        self.assertEqual(d.version_class, "SUPPORTED")
        self.assertEqual(d.status, "VERIFIED")
        self.assertFalse(d.grants_send)

    def test_admit_unknown_version_refused(self):
        d = admit_version(intended="admit", version=2)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_version")
        self.assertEqual(d.version_class, "UNKNOWN_VERSION")
        self.assertFalse(d.grants_send)

    def test_admit_missing_refused_as_unknown_version(self):
        d = admit_version(intended="admit", version=None)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_version")
        self.assertEqual(d.version_class, "UNKNOWN")

    def test_halt_refuses_admit_only(self):
        blocked = admit_version(intended="admit", version=1, halted=True)
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.reason, "halt_active")
        classify = admit_version(intended="classify", version=1, halted=True)
        self.assertTrue(classify.allowed)

    def test_timeout_refuses_admit_as_unknown_not_concurrent(self):
        d = admit_version(
            intended="admit", version=1, activity="concurrent",
            timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertNotEqual(d.reason, "suspected_concurrent")

    def test_concurrent_refuses_admit(self):
        d = admit_version(intended="admit", version=1, activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")

    def test_unknown_activity_refuses_admit(self):
        d = admit_version(intended="admit", version=1, activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")


class FailClosedShapes(unittest.TestCase):
    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_version(intended="DEAD_SOURCE", version=1)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_activity_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_version(intended="classify", version=1, activity="BUSY")

    def test_halted_must_be_exact_bool(self):
        for bad in (1, 0, "true", None):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    admit_version(intended="classify", version=1, halted=bad)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_version(intended="classify", version=1, timed_out=1)

    def test_bool_version_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_version(intended="admit", version=True)

    def test_sealed_intent_is_sealed_effect(self):
        d = admit_version(intended="send_authorized", version=1)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertFalse(d.grants_send)

    def test_sealed_version_is_sealed_effect(self):
        d = admit_version(intended="classify", version="quote_sent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertFalse(d.grants_send)

    def test_ready_is_not_authorized_as_version(self):
        ready = admit_version(
            intended="classify", version="campaign_envelope_ready")
        auth = admit_version(intended="classify", version="send_authorized")
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertNotEqual(ready.version_class, auth.reason)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
