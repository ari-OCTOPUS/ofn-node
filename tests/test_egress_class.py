"""Contract tests for egress_class (P1 complementary).

Destination classes are not sends. Missing is UNKNOWN, not FALSE.
external and sealed send/ready names refuse. HALT stops admit_leave
(START) and does not stop classify_dest. Ready ≠ authorized.
Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.egress_class import (
    CLASSES,
    DESTINATIONS,
    EgressClass,
    admit_leave,
    claims_immutable,
    classify_dest,
    grants_send,
    halt_blocks_classify,
    halt_blocks_leave,
    later_disarm_supersedes,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_halt_blocks_leave_start(self):
        self.assertTrue(halt_blocks_leave())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(promotes_ready_to_send())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())
        import ofn.adapters.run_store as rs
        source = inspect.getsource(rs)
        self.assertNotIn("egress_class", source)
        self.assertNotIn("deny_pin", source)

    def test_closed_vocabularies(self):
        self.assertEqual(DESTINATIONS, frozenset({"outbox", "loopback", "external"}))
        self.assertEqual(CLASSES, frozenset({"OUTBOX", "LOOPBACK", "UNKNOWN"}))
        self.assertNotIn("send_authorized", DESTINATIONS)
        self.assertNotIn("campaign_envelope_ready", DESTINATIONS)

    def test_classify_signature_has_no_send_or_resend(self):
        params = inspect.signature(classify_dest).parameters
        self.assertEqual(list(params), ["dest", "kind", "payload"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_admit_leave_halt_is_the_only_start_knob(self):
        params = inspect.signature(admit_leave).parameters
        self.assertEqual(list(params), ["dest", "halt", "kind", "payload"])
        self.assertNotIn("resend", params)
        self.assertNotIn("send_authorized", params)


class ClassifyDest(unittest.TestCase):
    def test_none_is_unknown_not_false(self):
        d = classify_dest(None)
        self.assertEqual(d.klass, "UNKNOWN")
        self.assertEqual(d.dest, "UNKNOWN")
        self.assertFalse(d.grants_send)
        self.assertIsNot(d.klass, False)

    def test_outbox_and_loopback(self):
        self.assertEqual(classify_dest("outbox").klass, "OUTBOX")
        self.assertEqual(classify_dest("OUTBOX").klass, "OUTBOX")
        self.assertEqual(classify_dest("loopback").klass, "LOOPBACK")
        self.assertEqual(classify_dest("LOOPBACK").dest, "loopback")

    def test_external_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_dest("external")

    def test_unknown_string_fails_closed_not_false(self):
        with self.assertRaises(FailClosedError):
            classify_dest("smtp")
        with self.assertRaises(FailClosedError):
            classify_dest("customer")

    def test_bool_and_empty_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_dest(True)
        with self.assertRaises(FailClosedError):
            classify_dest("")
        with self.assertRaises(FailClosedError):
            classify_dest(0)

    def test_timeout_kind_is_unknown(self):
        d = classify_dest("outbox", kind="timeout")
        self.assertEqual(d.klass, "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent_write())

    def test_sealed_names_refuse(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_dest(name)

    def test_payload_smuggle_refused(self):
        with self.assertRaises(FailClosedError):
            classify_dest("outbox", payload={"quote_sent": "held"})

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            EgressClass(klass="OUTBOX", dest="outbox", grants_send=True)

    def test_constructor_refuses_unknown_with_real_dest(self):
        with self.assertRaises(FailClosedError):
            EgressClass(klass="UNKNOWN", dest="outbox")


class AdmitLeave(unittest.TestCase):
    def test_outbox_and_loopback_are_false_not_true(self):
        self.assertIs(admit_leave("outbox"), False)
        self.assertIs(admit_leave("loopback"), False)

    def test_missing_is_none_not_false(self):
        self.assertIsNone(admit_leave(None))
        self.assertIsNot(admit_leave(None), False)

    def test_timeout_is_none(self):
        self.assertIsNone(admit_leave("outbox", kind="timeout"))

    def test_external_and_sealed_fail_closed(self):
        with self.assertRaises(FailClosedError):
            admit_leave("external")
        with self.assertRaises(FailClosedError):
            admit_leave("send_authorized")
        with self.assertRaises(FailClosedError):
            admit_leave("campaign_envelope_ready")

    def test_halt_refuses_start(self):
        with self.assertRaises(FailClosedError):
            admit_leave("outbox", halt=True)

    def test_halt_false_still_denies_leave(self):
        self.assertIs(admit_leave("outbox", halt=False), False)

    def test_halt_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_leave("outbox", halt="yes")


if __name__ == "__main__":
    unittest.main()
