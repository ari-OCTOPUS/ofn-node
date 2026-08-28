"""The executor gate: every way a yes becomes a no, and the one way it
doesn't.

The fake provider records calls instead of making them, so these tests can
assert the strongest property the gate has: the provider is reached only
when every rule passes, exactly once per approval. Every rejection —
mutated payload, wrong user, expired, superseded, replayed, missing
policy, missing witness — ends in a DENIED receipt and a provider that was
never touched. A timeout ends in a FAILED receipt, because an attempt was
made and its outcome is genuinely unknown.

Receipts are append-only with terminal statuses only. There is no PENDING
anywhere: the duplicate rules read this same file, so a receipt that could
still change would let one approval execute twice.
"""

import hashlib
import json
import os
import unittest

from ofn.adapters.fake_executor import (
    RECEIPTS_FILENAME,
    TERMINAL_STATUSES,
    STATUS_DENIED,
    STATUS_EXECUTED,
    STATUS_FAILED,
    Approval,
    FakeProvider,
    ProviderTimeout,
    execute_with_approval,
)
from ofn.adapters.owner_decision import OwnerDecision
from tests.tmpdir import temp_dir

NOW = "2026-08-28T12:00:00Z"
PAYLOAD = "Follow up on the exterior repaint quote in Newtown."
EXPIRY = "2027-01-15T09:00:00Z"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_decision(**over) -> OwnerDecision:
    values = dict(
        decision_id="D-138-0001",
        run_id="run-138-1",
        lane="painting",
        action="send_follow_up",
        recipient_masked="telegram:98***21",
        exact_payload=PAYLOAD,
        payload_sha=sha(PAYLOAD),
        artifact_sha=sha("artifact-bytes"),
        verdict_sha=sha("verdict-bytes"),
        idempotency_key="idem-1",
        expires_at=EXPIRY,
        rollback="pause the painting lane",
    )
    values.update(over)
    return OwnerDecision(**values)


def make_approval(decision: OwnerDecision, **over) -> Approval:
    values = dict(
        approval_id="A-1",
        decision_id=decision.decision_id,
        approver_user_id="owner",
        payload_sha=decision.payload_sha,
        idempotency_key=decision.idempotency_key,
        granted_at=NOW,
    )
    values.update(over)
    return Approval(**values)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.state = temp_dir(self)
        self.receipts = os.path.join(self.state, RECEIPTS_FILENAME)
        self.provider = FakeProvider()

    def run_gate(self, decision=None, approval=None, provider=None, **kw):
        decision = decision or make_decision()
        approval = approval or make_approval(decision)
        kw.setdefault("state_dir", self.state)
        kw.setdefault("now_utc", NOW)
        return execute_with_approval(decision, approval,
                                     provider or self.provider, **kw)

    def read_receipts(self):
        with open(self.receipts, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def test_valid_approval_executes_exactly_once(self):
        receipt = self.run_gate()
        self.assertEqual(receipt["status"], STATUS_EXECUTED)
        self.assertEqual(self.provider.calls, [PAYLOAD])
        self.assertEqual(receipt["provider_result"]["payload_sha256"],
                         sha(PAYLOAD))
        self.assertEqual(self.read_receipts(), [receipt])

    def test_duplicate_approval_is_denied_without_a_second_call(self):
        self.run_gate()
        second = self.run_gate()
        self.assertEqual(second["status"], STATUS_DENIED)
        self.assertEqual(second["rule"], "duplicate-approval")
        self.assertFalse(second["provider_called"])
        self.assertEqual(self.provider.calls, [PAYLOAD])
        # Both outcomes are on the file, terminal, in order.
        statuses = [r["status"] for r in self.read_receipts()]
        self.assertEqual(statuses, [STATUS_EXECUTED, STATUS_DENIED])

    def test_duplicate_idempotency_key_never_reaches_the_provider(self):
        first = self.run_gate()
        self.assertEqual(first["status"], STATUS_EXECUTED)
        # A different decision, a different approval — the same key.
        other_payload = "A second, distinct message."
        replayed = make_decision(
            decision_id="D-138-0002",
            exact_payload=other_payload,
            payload_sha=sha(other_payload),
            idempotency_key="idem-1")
        second = self.run_gate(
            decision=replayed, approval=make_approval(replayed,
                                                      approval_id="A-2"))
        self.assertEqual(second["status"], STATUS_DENIED)
        self.assertEqual(second["rule"], "duplicate-idempotency-key")
        self.assertEqual(self.provider.calls, [PAYLOAD])

    def test_payload_mutation_is_denied(self):
        # The payload changed after the decision was assembled, so its own
        # hash no longer describes it.
        mutated = make_decision(exact_payload="Tampered payload.",
                                payload_sha=sha(PAYLOAD))
        receipt = self.run_gate(decision=mutated)
        self.assertEqual(receipt["status"], STATUS_DENIED)
        self.assertEqual(receipt["rule"], "payload-mutated")
        self.assertEqual(self.provider.calls, [])

    def test_approval_bound_to_other_bytes_is_denied(self):
        other = make_approval(make_decision(), payload_sha=sha("other bytes"))
        receipt = self.run_gate(approval=other)
        self.assertEqual(receipt["rule"], "payload-mismatch")
        self.assertEqual(self.provider.calls, [])

    def test_wrong_user_is_denied(self):
        receipt = self.run_gate(
            approval=make_approval(make_decision(),
                                   approver_user_id="partner-7"))
        self.assertEqual(receipt["rule"], "approver-not-owner")
        self.assertEqual(self.provider.calls, [])

    def test_expired_decision_is_denied(self):
        expired = make_decision(expires_at="2026-08-28T12:00:00Z")
        # now == expires_at: the approval's deadline has passed.
        receipt = self.run_gate(decision=expired)
        self.assertEqual(receipt["rule"], "decision-expired")
        later = self.run_gate(decision=expired,
                              now_utc="2026-08-29T00:00:00Z")
        self.assertEqual(later["rule"], "decision-expired")
        self.assertEqual(self.provider.calls, [])

    def test_superseded_approval_is_denied(self):
        receipt = self.run_gate(
            approval=make_approval(make_decision(), superseded=True))
        self.assertEqual(receipt["rule"], "approval-superseded")
        self.assertEqual(self.provider.calls, [])

    def test_approval_for_another_decision_is_denied(self):
        receipt = self.run_gate(
            approval=make_approval(make_decision(),
                                   decision_id="D-somewhere-else"))
        self.assertEqual(receipt["rule"], "approval-unbound")
        self.assertEqual(self.provider.calls, [])

    def test_unavailable_policy_or_witness_is_denied(self):
        for kw, rule in ((dict(policy_available=False),
                          "policy-unavailable"),
                         (dict(witness_available=False),
                          "witness-unavailable")):
            receipt = self.run_gate(**kw)
            self.assertEqual(receipt["status"], STATUS_DENIED, rule)
            self.assertEqual(receipt["rule"], rule, rule)
            self.assertFalse(receipt["provider_called"])
        self.assertEqual(self.provider.calls, [])
        # Nothing executed, so a later healthy run is not blocked by either.
        ok = self.run_gate()
        self.assertEqual(ok["status"], STATUS_EXECUTED)
        self.assertEqual(self.provider.calls, [PAYLOAD])

    def test_invalid_decision_is_denied(self):
        receipt = self.run_gate(decision=make_decision(artifact_sha="short"))
        self.assertEqual(receipt["rule"], "decision-invalid")
        self.assertEqual(self.provider.calls, [])

    def test_provider_timeout_is_recorded_as_failed(self):
        slow = FakeProvider(timeout=True)
        receipt = self.run_gate(provider=slow)
        self.assertEqual(receipt["status"], STATUS_FAILED)
        self.assertEqual(receipt["rule"], "provider-timeout")
        # The attempt was made — that is what makes it a failure, not a deny.
        self.assertTrue(receipt["provider_called"])
        self.assertEqual(slow.calls, [PAYLOAD])
        self.assertEqual(self.read_receipts(), [receipt])

    def test_every_receipt_is_append_only_and_terminal(self):
        def decision_n(n, **over):
            return make_decision(decision_id=f"D-138-000{n}",
                                 idempotency_key=f"idem-{n}", **over)

        def approval_n(decision, n):
            return make_approval(decision, approval_id=f"A-{n}")

        first = decision_n(1)
        self.run_gate(decision=first)                          # EXECUTED
        # A different decision carrying the SAME key: DENIED as a replay.
        replay = make_decision(decision_id="D-138-0002",
                               idempotency_key="idem-1")
        self.run_gate(decision=replay,
                      approval=approval_n(replay, 2))          # DENIED
        self.run_gate(decision=decision_n(3),
                      approval=approval_n(decision_n(3), 3),
                      policy_available=False)                  # DENIED
        self.run_gate(decision=decision_n(4),
                      approval=approval_n(decision_n(4), 4),
                      provider=FakeProvider(timeout=True))     # FAILED
        receipts = self.read_receipts()
        self.assertEqual(len(receipts), 4)
        for receipt in receipts:
            self.assertIn(receipt["status"], TERMINAL_STATUSES)
            self.assertIn(receipt["status"],
                          (STATUS_EXECUTED, STATUS_DENIED, STATUS_FAILED))
            self.assertIn(receipt["rule"], (
                "executed", "duplicate-idempotency-key",
                "policy-unavailable", "provider-timeout"))
        # A denial is terminal for the attempt, not for the lane: nothing
        # above marked a pending state, and the log only ever grew.
        self.assertEqual([r["status"] for r in receipts],
                         [STATUS_EXECUTED, STATUS_DENIED, STATUS_DENIED,
                          STATUS_FAILED])


if __name__ == "__main__":
    unittest.main()
