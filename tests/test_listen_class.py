"""Kernel-pure listen class — complementary to timeout_verdict / ports.

UNKNOWN is not FALSE. Timeout is not absence. Wildcard is not local.
Ready is not authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.listen_class import (
    FAMILIES,
    INTENTS,
    ListenDecision,
    admit_listen,
    claims_immutable,
    classify_family,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    lan_is_local,
    missing_lan_proves_absent,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_absent,
    timeout_proves_concurrent,
    unknown_is_false,
    wildcard_is_local,
    wires_into_run_store,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent_or_absent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertFalse(timeout_proves_absent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_missing_lan_does_not_prove_absent(self):
        self.assertFalse(missing_lan_proves_absent())

    def test_wildcard_and_lan_are_not_local(self):
        self.assertFalse(wildcard_is_local())
        self.assertFalse(lan_is_local())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())
        self.assertFalse(promotes_ready_to_send())
        self.assertFalse(wires_into_run_store())

    def test_closed_vocabularies(self):
        self.assertEqual(INTENTS, {"bind", "classify", "observe"})
        self.assertEqual(FAMILIES, {"loopback", "wildcard", "lan", "unknown"})

    def test_admit_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_listen).parameters
        self.assertEqual(
            list(params),
            ["intended", "address", "halted", "timed_out", "lan_probe"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            ListenDecision(
                allowed=False, reason="unknown_address",
                family="unknown", intended="bind",
                address="nope", status="VERIFIED",
                timed_out=False, grants_send=True)

    def test_constructor_refuses_bind_of_non_loopback(self):
        with self.assertRaises(FailClosedError):
            ListenDecision(
                allowed=True, reason=None,
                family="wildcard", intended="bind",
                address="0.0.0.0", status="VERIFIED",
                timed_out=False)

    def test_constructor_refuses_bind_while_unknown(self):
        with self.assertRaises(FailClosedError):
            ListenDecision(
                allowed=True, reason=None,
                family="loopback", intended="bind",
                address="127.0.0.1", status="UNKNOWN",
                timed_out=True)

    def test_constructor_refuses_sealed_address(self):
        with self.assertRaises(FailClosedError):
            ListenDecision(
                allowed=False, reason="unknown_address",
                family="unknown", intended="bind",
                address="send_authorized", status="VERIFIED",
                timed_out=False)


class ClassifyFamily(unittest.TestCase):
    def test_loopback_literals(self):
        self.assertEqual(classify_family("127.0.0.1"), "loopback")
        self.assertEqual(classify_family("::1"), "loopback")

    def test_wildcard_literals(self):
        self.assertEqual(classify_family("0.0.0.0"), "wildcard")
        self.assertEqual(classify_family("::"), "wildcard")
        self.assertEqual(classify_family("*"), "wildcard")

    def test_other_ipv4_is_lan_not_local(self):
        self.assertEqual(classify_family("192.168.0.1"), "lan")
        self.assertFalse(lan_is_local())

    def test_other_ipv6_is_lan(self):
        self.assertEqual(classify_family("fe80::1"), "lan")

    def test_garbage_is_unknown_not_lan(self):
        self.assertEqual(classify_family("not-an-address"), "unknown")

    def test_leading_zero_octet_is_unknown(self):
        self.assertEqual(classify_family("127.0.0.01"), "unknown")

    def test_octet_over_255_is_unknown(self):
        self.assertEqual(classify_family("127.0.0.256"), "unknown")

    def test_sealed_address_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family("send_authorized")
        with self.assertRaises(FailClosedError):
            classify_family("campaign_envelope_ready")


class AdmitBind(unittest.TestCase):
    def test_loopback_bind_with_open_probe_is_admitted(self):
        d = admit_listen(
            intended="bind", address="127.0.0.1",
            lan_probe="open")
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertEqual(d.family, "loopback")
        self.assertEqual(d.status, "VERIFIED")
        self.assertFalse(d.grants_send)

    def test_ipv6_loopback_bind_is_admitted(self):
        d = admit_listen(
            intended="bind", address="::1", lan_probe="open")
        self.assertTrue(d.allowed)
        self.assertEqual(d.family, "loopback")

    def test_wildcard_bind_is_refused(self):
        for addr in ("0.0.0.0", "::", "*"):
            with self.subTest(addr=addr):
                d = admit_listen(
                    intended="bind", address=addr, lan_probe="open")
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_wildcard")
                self.assertEqual(d.family, "wildcard")
                self.assertFalse(wildcard_is_local())
                self.assertFalse(d.grants_send)

    def test_lan_bind_is_refused(self):
        d = admit_listen(
            intended="bind", address="192.168.0.1", lan_probe="open")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "lan_not_local")
        self.assertFalse(lan_is_local())

    def test_unknown_address_bind_is_refused(self):
        d = admit_listen(
            intended="bind", address="nope", lan_probe="open")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_address")
        self.assertEqual(d.family, "unknown")

    def test_halt_refuses_bind_only(self):
        blocked = admit_listen(
            intended="bind", address="127.0.0.1",
            halted=True, lan_probe="open")
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.reason, "halt_active")
        named = admit_listen(
            intended="classify", address="0.0.0.0",
            halted=True, lan_probe="open")
        self.assertTrue(named.allowed)
        self.assertEqual(named.family, "wildcard")
        self.assertFalse(halt_blocks_classify())


class AdmitClassifyObserve(unittest.TestCase):
    def test_classify_wildcard_is_not_a_bind(self):
        d = admit_listen(
            intended="classify", address="0.0.0.0", lan_probe="open")
        self.assertTrue(d.allowed)
        self.assertEqual(d.family, "wildcard")
        self.assertFalse(d.grants_send)
        self.assertFalse(proposal_is_execution())

    def test_observe_lan_closed_is_not_loopback_absent(self):
        d = admit_listen(
            intended="observe", address="10.0.0.1", lan_probe="closed")
        self.assertTrue(d.allowed)
        self.assertEqual(d.family, "lan")
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(missing_lan_proves_absent())

    def test_closed_lan_does_not_block_loopback_bind(self):
        d = admit_listen(
            intended="bind", address="127.0.0.1", lan_probe="closed")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(missing_lan_proves_absent())


class TimeoutIsUnknown(unittest.TestCase):
    def test_timeout_flag_outranks_open_probe(self):
        d = admit_listen(
            intended="bind", address="127.0.0.1",
            timed_out=True, lan_probe="open")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_probe")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent())
        self.assertFalse(timeout_proves_absent())

    def test_timeout_probe_is_unknown_not_closed(self):
        d = admit_listen(
            intended="bind", address="127.0.0.1", lan_probe="timeout")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_probe")
        self.assertFalse(d.allowed)

    def test_classify_under_timeout_still_names(self):
        d = admit_listen(
            intended="classify", address="127.0.0.1",
            timed_out=True, lan_probe="open")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(classify_timeout(), "UNKNOWN")


class FailClosedInputs(unittest.TestCase):
    def test_missing_probe_is_unknown_not_closed(self):
        with self.assertRaises(FailClosedError):
            admit_listen(
                intended="bind", address="127.0.0.1", lan_probe=None)

    def test_string_halted_is_not_a_claim(self):
        with self.assertRaises(FailClosedError):
            admit_listen(
                intended="bind", address="127.0.0.1",
                halted="yes", lan_probe="open")

    def test_string_timed_out_is_not_a_claim(self):
        with self.assertRaises(FailClosedError):
            admit_listen(
                intended="bind", address="127.0.0.1",
                timed_out="yes", lan_probe="open")

    def test_blank_and_bool_address_refuse(self):
        with self.assertRaises(FailClosedError):
            admit_listen(intended="bind", address="", lan_probe="open")
        with self.assertRaises(FailClosedError):
            admit_listen(intended="bind", address=True, lan_probe="open")

    def test_unknown_intent_refuses(self):
        with self.assertRaises(FailClosedError):
            admit_listen(
                intended="resend", address="127.0.0.1", lan_probe="open")

    def test_unknown_probe_name_refuses(self):
        with self.assertRaises(FailClosedError):
            admit_listen(
                intended="bind", address="127.0.0.1", lan_probe="ok")

    def test_sealed_address_refuses(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                d = admit_listen(
                    intended="bind", address=name, lan_probe="open")
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")

    def test_sealed_intent_refuses(self):
        d = admit_listen(
            intended="send_authorized", address="127.0.0.1",
            lan_probe="open")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")


if __name__ == "__main__":
    unittest.main()
