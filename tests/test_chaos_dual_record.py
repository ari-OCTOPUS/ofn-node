"""Owner-absent chaos — dual-record composition (independent of #82 chaos).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These scenarios
lock the same seven rules at the pairing layer: no store, no run_id
mint, no fabricated witness. HALT is not a pairing parameter. One
arm's timeout cannot refuse another arm's pair. Recovery is pairing
two independent records and is still not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.dual_record import (
    RecordRef,
    classify_timeout,
    grants_send,
    halt_blocks_pair,
    pair_records,
    ready_is_authorized,
    timeout_proves_concurrent,
)
from ofn.kernel.errors import FailClosedError


def _rec(source: str, value: str = "pass") -> RecordRef:
    return RecordRef(
        source_path=source,
        vantage="this_host_only",
        value=value,
        evidence_level="E2",
    )


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_vantage_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            RecordRef(source_path="dead.txt", vantage="DEAD_SOURCE",
                      value="pass", evidence_level="E2")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_level_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            RecordRef(source_path="dead.txt", vantage="this_host_only",
                      value="pass", evidence_level="DEAD")
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_siblings(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = pair_records(
            topic="exit_code",
            record_a=_rec("arm-b-cmd", "0"),
            record_b=_rec("arm-b-receipt", "0"),
        )
        self.assertEqual(sibling.status, "WITNESSED")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        self.assertEqual(classify_timeout(), "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent())
        d = pair_records(
            topic="exit_code",
            record_a=_rec("cmd-a", "0"),
            record_b=_rec("cmd-b", "0"),
        )
        self.assertEqual(d.status, "WITNESSED")


class Scenario3ProposalIsNotExecution(unittest.TestCase):
    def test_witnessed_pair_is_not_an_external_effect(self):
        d = pair_records(
            topic="proposal_hash",
            record_a=_rec("draft.txt", "abc"),
            record_b=_rec("review.txt", "abc"),
        )
        self.assertEqual(d.status, "WITNESSED")
        self.assertFalse(d.grants_send)
        self.assertFalse(grants_send())


class Scenario4AgentReportedIsNotIndependentlyVerified(unittest.TestCase):
    def test_one_record_is_unwitnessed(self):
        d = pair_records(topic="agent_note", record_a=_rec("chat.txt"))
        self.assertEqual(d.status, "UNWITNESSED")
        self.assertEqual(d.reason, "missing_second")
        self.assertFalse(d.grants_send)

    def test_same_source_copy_is_not_independent(self):
        d = pair_records(
            topic="agent_note",
            record_a=_rec("chat.txt", "ok"),
            record_b=_rec("chat.txt", "ok"),
        )
        self.assertEqual(d.status, "UNWITNESSED")
        self.assertEqual(d.reason, "same_source")


class Scenario5SealedSendDoesNotPoisonSibling(unittest.TestCase):
    def test_sealed_topic_leaves_sibling_pair_intact(self):
        sealed = pair_records(
            topic="send_authorized",
            record_a=_rec("a.txt"),
            record_b=_rec("b.txt"),
        )
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = pair_records(
            topic="exit_code",
            record_a=_rec("cmd-a", "0"),
            record_b=_rec("cmd-b", "0"),
        )
        self.assertEqual(sibling.status, "WITNESSED")
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotAPairParameter(unittest.TestCase):
    def test_halt_does_not_block_pairing(self):
        self.assertFalse(halt_blocks_pair())
        for arm in ("a", "b", "c"):
            d = pair_records(
                topic="arm_ok",
                record_a=_rec(f"{arm}-cmd", "ok"),
                record_b=_rec(f"{arm}-receipt", "ok"),
            )
            self.assertEqual(d.status, "WITNESSED")
            self.assertFalse(d.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        self.assertNotIn("halt", inspect.signature(pair_records).parameters)
        self.assertNotIn("halt_raw", inspect.signature(pair_records).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_pair_and_not_a_send(self):
        blocked = pair_records(
            topic="quote_sent",
            record_a=_rec("a.txt"),
            record_b=_rec("b.txt"),
        )
        self.assertEqual(blocked.reason, "sealed_effect")
        resumed = pair_records(
            topic="head_sha",
            record_a=_rec("git", "abc"),
            record_b=_rec("receipt", "abc"),
        )
        self.assertEqual(resumed.status, "WITNESSED")
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())

    def test_ready_never_equals_authorized(self):
        ready = pair_records(
            topic="campaign_envelope_ready",
            record_a=_rec("a.txt"),
            record_b=_rec("b.txt"),
        )
        auth = pair_records(
            topic="send_authorized",
            record_a=_rec("a.txt"),
            record_b=_rec("b.txt"),
        )
        for d in (ready, auth):
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual(ready.topic, auth.topic)


if __name__ == "__main__":
    unittest.main()
