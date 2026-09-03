"""Kernel-pure verify class — complementary to report_class.

Independent verification requires a second, distinct, direct
witness. An agent report cannot verify itself or another report.
A timeout is UNKNOWN, not concurrent writing. Ready is not
authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.report_class import mint_report
from ofn.kernel.verify_class import (
    REFUSAL_REASONS,
    REFUSED_WITNESS,
    WITNESS_KINDS,
    VerifyDecision,
    claims_immutable,
    grants_send,
    halt_blocks_verify,
    proposal_is_execution,
    ready_is_authorized,
    report_is_verification,
    timeout_proves_concurrent_write,
    unknown_is_false,
    verify_report,
)


def _report(kind: str = "agent_report", reporter: str = "body-a",
            subject: str = "job-1"):
    return mint_report(kind=kind, reporter=reporter, subject=subject)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_verify(self):
        self.assertFalse(halt_blocks_verify())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_report_is_not_verification(self):
        self.assertFalse(report_is_verification())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(verify_report).parameters
        self.assertEqual(
            list(params),
            ["report", "witness_id", "witness_kind", "witness_ref", "payload"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            VerifyDecision(
                verified=True, reason=None,
                witness_kind="direct_observation", witness_id="probe-1",
                independently_verified=True, grants_send=True)
        with self.assertRaises(FailClosedError):
            VerifyDecision(
                verified=False, reason="self_verify",
                witness_kind="direct_observation", witness_id="body-a",
                independently_verified=False, grants_send=True)

    def test_verified_and_independently_verified_must_agree(self):
        with self.assertRaises(FailClosedError):
            VerifyDecision(
                verified=True, reason=None,
                witness_kind="direct_observation", witness_id="probe-1",
                independently_verified=False)
        with self.assertRaises(FailClosedError):
            VerifyDecision(
                verified=False, reason="self_verify",
                witness_kind="direct_observation", witness_id="body-a",
                independently_verified=True)

    def test_verified_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            VerifyDecision(
                verified=True, reason="self_verify",
                witness_kind="direct_observation", witness_id="probe-1",
                independently_verified=True)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            VerifyDecision(
                verified=False, reason=None,
                witness_kind="direct_observation", witness_id="probe-1",
                independently_verified=False)
        with self.assertRaises(FailClosedError):
            VerifyDecision(
                verified=False, reason="send_authorized",
                witness_kind="direct_observation", witness_id="probe-1",
                independently_verified=False)
        for reason in ("self_verify", "not_independent", "timeout_unknown",
                       "proposal_is_not_execution", "report_not_admitted",
                       "sealed_effect", "smuggled_effect"):
            self.assertIn(reason, REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_verified_decision_refuses_sealed_names(self):
        with self.assertRaises(FailClosedError):
            VerifyDecision(
                verified=True, reason=None,
                witness_kind="send_authorized", witness_id="probe-1",
                independently_verified=True)

    def test_closed_witness_vocabularies(self):
        self.assertEqual(
            WITNESS_KINDS,
            frozenset({"direct_observation", "artifact_ref"}))
        self.assertEqual(
            REFUSED_WITNESS,
            frozenset({"agent_report", "measurement_note",
                       "proposal_note", "timeout"}))
        self.assertTrue(WITNESS_KINDS.isdisjoint(REFUSED_WITNESS))
        self.assertNotIn("send_authorized", WITNESS_KINDS)


class VerifyAdmitted(unittest.TestCase):
    def test_distinct_direct_observation_verifies(self):
        d = verify_report(
            _report(),
            witness_id="probe-1",
            witness_kind="direct_observation",
            witness_ref="sha-1",
        )
        self.assertTrue(d.verified)
        self.assertTrue(d.independently_verified)
        self.assertFalse(d.grants_send)
        self.assertIsNone(d.reason)
        self.assertFalse(grants_send())
        self.assertFalse(ready_is_authorized())

    def test_distinct_artifact_ref_verifies(self):
        d = verify_report(
            _report(kind="measurement_note"),
            witness_id="receipt-1",
            witness_kind="artifact_ref",
            witness_ref="docs/receipt.json",
        )
        self.assertTrue(d.verified)
        self.assertTrue(d.independently_verified)
        self.assertFalse(d.grants_send)

    def test_verification_does_not_grant_send(self):
        d = verify_report(
            _report(),
            witness_id="probe-1",
            witness_kind="direct_observation",
            witness_ref="sha-1",
        )
        self.assertTrue(d.verified)
        self.assertFalse(d.grants_send)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class VerifyRefusals(unittest.TestCase):
    def test_same_reporter_is_self_verify(self):
        d = verify_report(
            _report(reporter="body-a"),
            witness_id="body-a",
            witness_kind="direct_observation",
            witness_ref="sha-1",
        )
        self.assertFalse(d.verified)
        self.assertEqual(d.reason, "self_verify")
        self.assertFalse(d.independently_verified)
        self.assertFalse(report_is_verification())

    def test_agent_report_witness_is_not_independent(self):
        for kind in ("agent_report", "measurement_note"):
            with self.subTest(kind=kind):
                d = verify_report(
                    _report(),
                    witness_id="body-b",
                    witness_kind=kind,
                    witness_ref="note-1",
                )
                self.assertFalse(d.verified)
                self.assertEqual(d.reason, "not_independent")

    def test_timeout_is_unknown_not_concurrent_write(self):
        d = verify_report(
            _report(),
            witness_id="job-100493656547",
            witness_kind="timeout",
            witness_ref="check-suite",
        )
        self.assertFalse(d.verified)
        self.assertEqual(d.reason, "timeout_unknown")
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(unknown_is_false())

    def test_proposal_note_is_not_execution(self):
        d = verify_report(
            _report(kind="proposal_note"),
            witness_id="body-b",
            witness_kind="proposal_note",
            witness_ref="draft-1",
        )
        self.assertFalse(d.verified)
        self.assertEqual(d.reason, "proposal_is_not_execution")
        self.assertFalse(proposal_is_execution())

    def test_refused_report_cannot_be_verified(self):
        refused = mint_report(
            kind="send_authorized", reporter="body-a", subject="job-1")
        self.assertFalse(refused.admitted)
        d = verify_report(
            refused,
            witness_id="probe-1",
            witness_kind="direct_observation",
            witness_ref="sha-1",
        )
        self.assertFalse(d.verified)
        self.assertEqual(d.reason, "report_not_admitted")

    def test_foreign_report_fails_closed(self):
        with self.assertRaises(FailClosedError):
            verify_report(
                {"kind": "agent_report"},
                witness_id="probe-1",
                witness_kind="direct_observation",
                witness_ref="sha-1",
            )

    def test_unknown_witness_kind_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            verify_report(
                _report(),
                witness_id="probe-1",
                witness_kind="hearsay",
                witness_ref="sha-1",
            )
        self.assertIn("UNKNOWN", str(ctx.exception))
        self.assertFalse(unknown_is_false())

    def test_bool_and_blank_fail_closed(self):
        r = _report()
        with self.assertRaises(FailClosedError):
            verify_report(
                r, witness_id=True, witness_kind="direct_observation",
                witness_ref="sha-1")
        with self.assertRaises(FailClosedError):
            verify_report(
                r, witness_id="probe-1", witness_kind="",
                witness_ref="sha-1")
        with self.assertRaises(FailClosedError):
            verify_report(
                r, witness_id="probe-1",
                witness_kind="direct_observation", witness_ref=None)


class VerifySealed(unittest.TestCase):
    def test_sealed_witness_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent", "campaign-envelope-ready"):
            with self.subTest(name=name):
                d = verify_report(
                    _report(),
                    witness_id=name,
                    witness_kind="direct_observation",
                    witness_ref="sha-1",
                )
                self.assertFalse(d.verified)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_sealed_kind_and_ref(self):
        kind = verify_report(
            _report(),
            witness_id="probe-1",
            witness_kind="campaign_envelope_ready",
            witness_ref="sha-1",
        )
        ref = verify_report(
            _report(),
            witness_id="probe-1",
            witness_kind="direct_observation",
            witness_ref="quote_sent",
        )
        self.assertEqual(kind.reason, "sealed_effect")
        self.assertEqual(ref.reason, "sealed_effect")
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_smuggled_payload_is_known_refusal(self):
        d = verify_report(
            _report(),
            witness_id="probe-1",
            witness_kind="direct_observation",
            witness_ref="sha-1",
            payload={"effect": "send_authorized"},
        )
        self.assertFalse(d.verified)
        self.assertEqual(d.reason, "smuggled_effect")

    def test_non_mapping_payload_fails_closed(self):
        with self.assertRaises(FailClosedError):
            verify_report(
                _report(),
                witness_id="probe-1",
                witness_kind="direct_observation",
                witness_ref="sha-1",
                payload="quote_sent",
            )


if __name__ == "__main__":
    unittest.main()
