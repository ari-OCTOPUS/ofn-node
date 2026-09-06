"""Owner-Absent chaos — report/verify complementary scenarios.

Each scenario is a rule that must hold while the owner cannot be
reached: an agent report is not a verification, a timeout is not
concurrent writing, one arm's refusal never stops the others, and
every recovery on this page is a reversible decision an agent may
take alone. None of them grant a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.report_class import (
    grants_send as report_grants_send,
    halt_blocks_report,
    mint_report,
    ready_is_authorized as report_ready,
)
from ofn.kernel.verify_class import (
    grants_send as verify_grants_send,
    halt_blocks_verify,
    timeout_proves_concurrent_write,
    unknown_is_false,
    verify_report,
)


class Scenario1AgentReportIsUnknownNotVerified(unittest.TestCase):
    def test_admitted_report_is_not_independently_verified(self):
        d = mint_report(
            kind="agent_report", reporter="body-a", subject="job-1")
        self.assertTrue(d.admitted)
        self.assertFalse(d.independently_verified)
        self.assertFalse(d.grants_send)

    def test_agent_report_cannot_verify_another_report(self):
        first = mint_report(
            kind="agent_report", reporter="body-a", subject="job-1")
        d = verify_report(
            first,
            witness_id="body-b",
            witness_kind="agent_report",
            witness_ref="session-note",
        )
        self.assertFalse(d.verified)
        self.assertEqual(d.reason, "not_independent")
        self.assertFalse(unknown_is_false())


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_timeout_does_not_block_a_sibling_verify(self):
        report = mint_report(
            kind="measurement_note", reporter="arm-a", subject="run-1")
        timed_out = verify_report(
            report,
            witness_id="arm-a-timer",
            witness_kind="timeout",
            witness_ref="budget",
        )
        self.assertEqual(timed_out.reason, "timeout_unknown")
        self.assertFalse(timeout_proves_concurrent_write())
        sibling = verify_report(
            report,
            witness_id="probe-b",
            witness_kind="direct_observation",
            witness_ref="sha-b",
        )
        self.assertTrue(sibling.verified)
        self.assertFalse(sibling.grants_send)


class Scenario3SelfVerifyIsNotASecondWitness(unittest.TestCase):
    def test_reporter_cannot_verify_own_report(self):
        report = mint_report(
            kind="agent_report", reporter="body-a", subject="job-1")
        d = verify_report(
            report,
            witness_id="body-a",
            witness_kind="direct_observation",
            witness_ref="sha-1",
        )
        self.assertEqual(d.reason, "self_verify")
        self.assertFalse(d.independently_verified)


class Scenario4OneRefusalDoesNotStopOthers(unittest.TestCase):
    def test_sealed_refusal_leaves_other_kinds_open(self):
        blocked = mint_report(
            kind="quote_sent", reporter="body-a", subject="job-1")
        self.assertFalse(blocked.admitted)
        other = mint_report(
            kind="proposal_note", reporter="body-a", subject="job-2")
        self.assertTrue(other.admitted)
        self.assertFalse(other.grants_send)


class Scenario5NoFabricatedWitness(unittest.TestCase):
    def test_unknown_witness_kind_fails_closed(self):
        report = mint_report(
            kind="agent_report", reporter="body-a", subject="job-1")
        with self.assertRaises(FailClosedError):
            verify_report(
                report,
                witness_id="probe-1",
                witness_kind="invented",
                witness_ref="sha-1",
            )


class Scenario6HaltDoesNotBlockClassify(unittest.TestCase):
    def test_no_halt_knob_and_halt_does_not_block(self):
        self.assertFalse(halt_blocks_report())
        self.assertFalse(halt_blocks_verify())
        self.assertNotIn("halt", inspect.signature(mint_report).parameters)
        self.assertNotIn("halt", inspect.signature(verify_report).parameters)
        self.assertNotIn("halt_raw", inspect.signature(mint_report).parameters)
        self.assertNotIn("halt_raw", inspect.signature(verify_report).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_direct_witness_and_not_a_send(self):
        blocked = mint_report(
            kind="send_authorized", reporter="body-a", subject="job-1")
        self.assertFalse(blocked.admitted)
        resumed = mint_report(
            kind="agent_report", reporter="body-a", subject="job-1")
        verified = verify_report(
            resumed,
            witness_id="probe-1",
            witness_kind="direct_observation",
            witness_ref="sha-1",
        )
        self.assertTrue(resumed.admitted)
        self.assertTrue(verified.verified)
        self.assertFalse(verified.grants_send)
        self.assertFalse(report_grants_send())
        self.assertFalse(verify_grants_send())
        self.assertFalse(report_ready())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = mint_report(
            kind="campaign_envelope_ready", reporter="body-a",
            subject="job-1")
        auth = mint_report(
            kind="send_authorized", reporter="body-a", subject="job-1")
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertFalse(ready.admitted)
        self.assertFalse(auth.admitted)
        self.assertNotEqual(ready.kind, auth.kind)


if __name__ == "__main__":
    unittest.main()
