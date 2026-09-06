"""Kernel-pure report class — complementary to unknown_seal and receipts.

An admitted report is not independently verified. HALT is not a
parameter. A sealed send/ready name refuses. Ready is not
authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.report_class import (
    REFUSAL_REASONS,
    REPORT_KINDS,
    SCOPES,
    ReportDecision,
    claims_immutable,
    default_scope,
    grants_send,
    halt_blocks_report,
    mint_report,
    proposal_is_execution,
    ready_is_authorized,
    report_is_verified,
    unknown_is_false,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_report(self):
        self.assertFalse(halt_blocks_report())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_report_is_not_verified(self):
        self.assertFalse(report_is_verified())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_default_scope_is_this_host_only(self):
        self.assertEqual(default_scope(), "this_host_only")
        self.assertEqual(SCOPES, frozenset({"this_host_only"}))
        self.assertNotIn("system_wide", SCOPES)

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(mint_report).parameters
        self.assertEqual(list(params), ["kind", "reporter", "subject", "payload"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            ReportDecision(
                admitted=True, reason=None, kind="agent_report",
                reporter="body-a", subject="job-1", grants_send=True)
        with self.assertRaises(FailClosedError):
            ReportDecision(
                admitted=False, reason="sealed_effect",
                kind="agent_report", reporter="body-a", subject="job-1",
                grants_send=True)

    def test_constructor_refuses_independently_verified_true(self):
        with self.assertRaises(FailClosedError):
            ReportDecision(
                admitted=True, reason=None, kind="agent_report",
                reporter="body-a", subject="job-1",
                independently_verified=True)

    def test_constructor_refuses_system_wide(self):
        with self.assertRaises(FailClosedError):
            ReportDecision(
                admitted=True, reason=None, kind="agent_report",
                reporter="body-a", subject="job-1",
                scope="system_wide")

    def test_admitted_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            ReportDecision(
                admitted=True, reason="sealed_effect",
                kind="agent_report", reporter="body-a", subject="job-1")

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            ReportDecision(
                admitted=False, reason=None,
                kind="agent_report", reporter="body-a", subject="job-1")
        with self.assertRaises(FailClosedError):
            ReportDecision(
                admitted=False, reason="send_authorized",
                kind="agent_report", reporter="body-a", subject="job-1")
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("smuggled_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_admitted_decision_refuses_sealed_names(self):
        for sealed in ("send_authorized", "quote_sent",
                       "campaign_envelope_ready"):
            with self.subTest(sealed=sealed):
                with self.assertRaises(FailClosedError):
                    ReportDecision(
                        admitted=True, reason=None, kind=sealed,
                        reporter="body-a", subject="job-1")
                with self.assertRaises(FailClosedError):
                    ReportDecision(
                        admitted=True, reason=None, kind="agent_report",
                        reporter=sealed, subject="job-1")

    def test_closed_kinds(self):
        self.assertEqual(
            REPORT_KINDS,
            frozenset({"agent_report", "measurement_note", "proposal_note"}))
        self.assertNotIn("send_authorized", REPORT_KINDS)
        self.assertNotIn("EXECUTION_RECEIPT", REPORT_KINDS)


class MintAdmitted(unittest.TestCase):
    def test_every_known_kind_admits_and_is_unverified(self):
        for kind in sorted(REPORT_KINDS):
            with self.subTest(kind=kind):
                d = mint_report(
                    kind=kind, reporter="body-a", subject="job-1")
                self.assertTrue(d.admitted)
                self.assertIsNone(d.reason)
                self.assertFalse(d.independently_verified)
                self.assertFalse(d.grants_send)
                self.assertEqual(d.scope, "this_host_only")
                self.assertFalse(report_is_verified())

    def test_proposal_note_is_not_execution(self):
        d = mint_report(
            kind="proposal_note", reporter="body-a", subject="draft-1")
        self.assertTrue(d.admitted)
        self.assertFalse(proposal_is_execution())
        self.assertNotEqual(d.kind, "EXECUTION_RECEIPT")

    def test_strips_whitespace(self):
        d = mint_report(
            kind="  agent_report  ", reporter="  body-a  ",
            subject="  job-1  ")
        self.assertEqual(d.kind, "agent_report")
        self.assertEqual(d.reporter, "body-a")
        self.assertEqual(d.subject, "job-1")


class MintSealed(unittest.TestCase):
    def test_sealed_kind_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent", "campaign-envelope-ready"):
            with self.subTest(name=name):
                d = mint_report(
                    kind=name, reporter="body-a", subject="job-1")
                self.assertFalse(d.admitted)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)
                self.assertFalse(d.independently_verified)

    def test_sealed_reporter_and_subject(self):
        for field, kwargs in (
            ("reporter", {"kind": "agent_report", "reporter": "quote_sent",
                          "subject": "job-1"}),
            ("subject", {"kind": "agent_report", "reporter": "body-a",
                         "subject": "send_authorized"}),
        ):
            with self.subTest(field=field):
                d = mint_report(**kwargs)
                self.assertFalse(d.admitted)
                self.assertEqual(d.reason, "sealed_effect")

    def test_ready_and_authorized_are_both_sealed(self):
        ready = mint_report(
            kind="campaign_envelope_ready", reporter="body-a",
            subject="job-1")
        auth = mint_report(
            kind="send_authorized", reporter="body-a", subject="job-1")
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertNotEqual(ready.kind, auth.kind)


class MintUnknownAndTypes(unittest.TestCase):
    def test_unknown_kind_fails_closed_not_as_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            mint_report(kind="rumor", reporter="body-a", subject="job-1")
        self.assertIn("UNKNOWN", str(ctx.exception))
        self.assertFalse(unknown_is_false())

    def test_bool_and_blank_fail_closed(self):
        with self.assertRaises(FailClosedError):
            mint_report(kind=True, reporter="body-a", subject="job-1")
        with self.assertRaises(FailClosedError):
            mint_report(kind="agent_report", reporter=False, subject="job-1")
        with self.assertRaises(FailClosedError):
            mint_report(kind="agent_report", reporter="body-a", subject="")
        with self.assertRaises(FailClosedError):
            mint_report(kind="agent_report", reporter="body-a", subject=None)

    def test_non_mapping_payload_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_report(
                kind="agent_report", reporter="body-a", subject="job-1",
                payload="send_authorized")
        with self.assertRaises(FailClosedError):
            mint_report(
                kind="agent_report", reporter="body-a", subject="job-1",
                payload=["quote_sent"])

    def test_smuggled_payload_is_known_refusal(self):
        d = mint_report(
            kind="agent_report", reporter="body-a", subject="job-1",
            payload={"state": "send_authorized"})
        self.assertFalse(d.admitted)
        self.assertEqual(d.reason, "smuggled_effect")
        self.assertFalse(d.grants_send)

    def test_empty_payload_is_admitted(self):
        d = mint_report(
            kind="measurement_note", reporter="body-a", subject="job-1",
            payload={})
        self.assertTrue(d.admitted)
        self.assertFalse(d.independently_verified)


if __name__ == "__main__":
    unittest.main()
