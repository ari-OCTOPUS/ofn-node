"""Kernel-pure unknown seal — complementary to write_fence and dual_record.

UNKNOWN is not FALSE. Timeout is not concurrent writing. Ready is not
authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.unknown_seal import (
    DISK_ABSENCE_LABEL,
    EVIDENCE_KINDS,
    FORCED_UNKNOWN,
    SCOPES,
    TIMEOUT_LABEL,
    VERDICTS,
    UnknownDecision,
    as_bool,
    claims_immutable,
    classify,
    default_scope,
    disk_absence_is_body_missing,
    grants_send,
    halt_blocks_classify,
    missing_port_proves_absent,
    promote_scope,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    unknown_is_true,
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

    def test_unknown_is_not_true(self):
        self.assertFalse(unknown_is_true())

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_missing_port_does_not_prove_absent(self):
        self.assertFalse(missing_port_proves_absent())

    def test_disk_absence_is_not_body_missing(self):
        self.assertFalse(disk_absence_is_body_missing())
        self.assertEqual(DISK_ABSENCE_LABEL, "body_not_on_this_host")
        self.assertNotEqual(DISK_ABSENCE_LABEL, "body_missing")

    def test_default_scope_is_this_host_only(self):
        self.assertEqual(default_scope(), "this_host_only")
        self.assertIn("this_host_only", SCOPES)
        self.assertIn("system_wide", SCOPES)

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(classify).parameters
        self.assertEqual(list(params), ["kind", "witness", "observed", "payload"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            UnknownDecision(
                verdict="UNKNOWN", kind="timeout",
                witness="job-1", label=TIMEOUT_LABEL, grants_send=True)
        with self.assertRaises(FailClosedError):
            UnknownDecision(
                verdict="TRUE", kind="direct_observation",
                witness="probe-1", label="direct_observation",
                grants_send=True)

    def test_forced_unknown_cannot_be_stored_as_true_or_false(self):
        for kind in sorted(FORCED_UNKNOWN):
            with self.subTest(kind=kind):
                with self.assertRaises(FailClosedError):
                    UnknownDecision(
                        verdict="FALSE", kind=kind,
                        witness="w", label="UNKNOWN")
                with self.assertRaises(FailClosedError):
                    UnknownDecision(
                        verdict="TRUE", kind=kind,
                        witness="w", label="UNKNOWN")

    def test_direct_observation_cannot_store_unknown(self):
        with self.assertRaises(FailClosedError):
            UnknownDecision(
                verdict="UNKNOWN", kind="direct_observation",
                witness="w", label="direct_observation")

    def test_foreign_verdict_refused(self):
        with self.assertRaises(FailClosedError):
            UnknownDecision(
                verdict="MAYBE", kind="timeout",
                witness="w", label="UNKNOWN")

    def test_sealed_name_cannot_live_on_the_record(self):
        with self.assertRaises(FailClosedError):
            UnknownDecision(
                verdict="UNKNOWN", kind="timeout",
                witness="send_authorized", label="UNKNOWN")
        with self.assertRaises(FailClosedError):
            UnknownDecision(
                verdict="UNKNOWN", kind="campaign_envelope_ready",
                witness="w", label="UNKNOWN")


class AsBool(unittest.TestCase):
    def test_named_true_and_false(self):
        self.assertTrue(as_bool("TRUE"))
        self.assertFalse(as_bool("FALSE"))

    def test_unknown_refuses_coercion(self):
        with self.assertRaises(FailClosedError) as ctx:
            as_bool("UNKNOWN")
        self.assertIn("UNKNOWN", str(ctx.exception))

    def test_python_bool_is_not_an_observation(self):
        with self.assertRaises(FailClosedError):
            as_bool(True)
        with self.assertRaises(FailClosedError):
            as_bool(False)

    def test_foreign_and_blank_refuse(self):
        with self.assertRaises(FailClosedError):
            as_bool("maybe")
        with self.assertRaises(FailClosedError):
            as_bool("")
        with self.assertRaises(FailClosedError):
            as_bool(None)


class ClassifyForcedUnknown(unittest.TestCase):
    def test_every_forced_kind_is_unknown(self):
        for kind in sorted(FORCED_UNKNOWN):
            with self.subTest(kind=kind):
                d = classify(kind=kind, witness="probe-a")
                self.assertEqual(d.verdict, "UNKNOWN")
                self.assertFalse(d.grants_send)
                self.assertEqual(d.kind, kind)
                with self.assertRaises(FailClosedError):
                    as_bool(d.verdict)

    def test_timeout_label_is_unknown_not_concurrent_write(self):
        d = classify(kind="timeout", witness="job-100464074909")
        self.assertEqual(d.label, TIMEOUT_LABEL)
        self.assertEqual(d.label, "UNKNOWN")
        self.assertNotEqual(d.label, "concurrent_write")
        self.assertFalse(timeout_proves_concurrent_write())

    def test_timeout_ignores_observed_argument(self):
        d = classify(kind="timeout", witness="job-1", observed="TRUE")
        self.assertEqual(d.verdict, "UNKNOWN")

    def test_missing_port_is_inference(self):
        d = classify(kind="missing_port", witness="8791")
        self.assertEqual(d.verdict, "UNKNOWN")
        self.assertEqual(d.label, "inference")
        self.assertFalse(missing_port_proves_absent())

    def test_disk_absence_label(self):
        d = classify(kind="disk_absence", witness="board-138-ledger")
        self.assertEqual(d.verdict, "UNKNOWN")
        self.assertEqual(d.label, "body_not_on_this_host")
        self.assertNotEqual(d.label, "body_missing")

    def test_absent_doc_is_unknown_not_false(self):
        d = classify(kind="absent_doc", witness="MASTER-BLUEPRINT.md")
        self.assertEqual(d.verdict, "UNKNOWN")
        self.assertNotEqual(d.verdict, "FALSE")

    def test_agent_report_only_is_unknown(self):
        d = classify(kind="agent_report_only", witness="session-note")
        self.assertEqual(d.verdict, "UNKNOWN")

    def test_unparsed_is_unknown(self):
        d = classify(kind="unparsed", witness="flag-file")
        self.assertEqual(d.verdict, "UNKNOWN")

    def test_missing_second_node_is_unknown(self):
        d = classify(kind="missing_second_node", witness="node-180")
        self.assertEqual(d.verdict, "UNKNOWN")


class ClassifyDirect(unittest.TestCase):
    def test_explicit_true_and_false(self):
        yes = classify(
            kind="direct_observation", witness="probe-ok", observed="TRUE")
        no = classify(
            kind="direct_observation", witness="probe-no", observed="FALSE")
        self.assertEqual(yes.verdict, "TRUE")
        self.assertEqual(no.verdict, "FALSE")
        self.assertTrue(as_bool(yes.verdict))
        self.assertFalse(as_bool(no.verdict))
        self.assertFalse(yes.grants_send)
        self.assertFalse(no.grants_send)

    def test_missing_observed_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify(kind="direct_observation", witness="probe-1")

    def test_unknown_observed_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify(
                kind="direct_observation", witness="probe-1",
                observed="UNKNOWN")

    def test_python_bool_observed_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify(
                kind="direct_observation", witness="probe-1", observed=True)
        with self.assertRaises(FailClosedError):
            classify(
                kind="direct_observation", witness="probe-1", observed=False)


class FailClosedInputs(unittest.TestCase):
    def test_unknown_kind_is_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify(kind="vibes", witness="w")
        self.assertIn("not FALSE", str(ctx.exception))

    def test_blank_and_bool_names_refuse(self):
        with self.assertRaises(FailClosedError):
            classify(kind="", witness="w")
        with self.assertRaises(FailClosedError):
            classify(kind="timeout", witness="")
        with self.assertRaises(FailClosedError):
            classify(kind=True, witness="w")
        with self.assertRaises(FailClosedError):
            classify(kind="timeout", witness=False)

    def test_sealed_kind_and_witness_refuse(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify(kind=name, witness="w")
                with self.assertRaises(FailClosedError):
                    classify(kind="timeout", witness=name)

    def test_smuggled_payload_refuses(self):
        with self.assertRaises(FailClosedError):
            classify(
                kind="timeout", witness="w",
                payload={"send_authorized": "no"})
        with self.assertRaises(FailClosedError):
            classify(
                kind="timeout", witness="w",
                payload={"phase": "campaign_envelope_ready"})

    def test_payload_must_be_mapping(self):
        with self.assertRaises(FailClosedError):
            classify(kind="timeout", witness="w", payload="nope")
        with self.assertRaises(FailClosedError):
            classify(kind="timeout", witness="w", payload=["x"])

    def test_clean_payload_is_accepted_on_forced_unknown(self):
        d = classify(
            kind="timeout", witness="w",
            payload={"job": "100464074909"})
        self.assertEqual(d.verdict, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_vocabulary_is_closed(self):
        self.assertEqual(VERDICTS, frozenset({"TRUE", "FALSE", "UNKNOWN"}))
        self.assertIn("direct_observation", EVIDENCE_KINDS)
        self.assertTrue(FORCED_UNKNOWN.issubset(EVIDENCE_KINDS))
        self.assertNotIn("direct_observation", FORCED_UNKNOWN)


class PromoteScope(unittest.TestCase):
    def test_two_distinct_nodes(self):
        self.assertEqual(
            promote_scope(("node-180", "node-138")),
            "system_wide")

    def test_one_node_is_not_a_promotion(self):
        with self.assertRaises(FailClosedError):
            promote_scope(("node-180",))

    def test_duplicate_nodes_are_not_two(self):
        with self.assertRaises(FailClosedError):
            promote_scope(("node-180", "node-180"))

    def test_three_nodes_refuse(self):
        with self.assertRaises(FailClosedError):
            promote_scope(("a", "b", "c"))

    def test_string_and_bool_refuse(self):
        with self.assertRaises(FailClosedError):
            promote_scope("node-180")
        with self.assertRaises(FailClosedError):
            promote_scope(True)
        with self.assertRaises(FailClosedError):
            promote_scope(None)

    def test_blank_member_refuses(self):
        with self.assertRaises(FailClosedError):
            promote_scope(("node-180", ""))

    def test_promotion_does_not_grant_send(self):
        self.assertEqual(
            promote_scope(("node-180", "node-138")),
            "system_wide")
        self.assertFalse(grants_send())
        self.assertFalse(ready_is_authorized())


class ReadyVsAuthorized(unittest.TestCase):
    def test_names_remain_structurally_distinct(self):
        ready = "campaign_envelope_ready"
        auth = "send_authorized"
        self.assertNotEqual(ready, auth)
        self.assertFalse(ready_is_authorized())
        for name in (ready, auth, "quote_sent"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify(kind=name, witness="w")


if __name__ == "__main__":
    unittest.main()
