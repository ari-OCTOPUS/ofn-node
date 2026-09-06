"""Both token ceilings must pass; neither grants a send."""

from __future__ import annotations

import hashlib
import unittest

from ofn.kernel.domain import Decision, RiskTier
from ofn.kernel.envelope import create_envelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.quota import NodeQuota
from ofn.kernel.token_ceiling import (
    SEND_STATES, admit_token_spend, aud_cents_from_payload, grants_send,
    per_run_fits, tokens_from_payload,
)

_AC = hashlib.sha256(b"acceptance: token-ceiling").hexdigest()
_NOW = 1780000000


def _env(*, budget_tokens: int = 0):
    return create_envelope(
        goal="token ceiling fixture", risk_tier="GREEN", authority_level="A1",
        idempotency_key="tok-ceil-1", acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand="c1c2c3d4e5f6a7b8",
        deadline_iso="2026-09-09T12:00:00Z", budget_tokens=budget_tokens)


def _quota() -> NodeQuota:
    return NodeQuota(
        estimated_capacity_tokens=100_000,
        utilisation=0.40,
        shares={"alpha": 0.50, "bravo": 0.50},
    )


class PerRunFits(unittest.TestCase):
    def test_zero_budget_only_allows_zero_request(self):
        self.assertTrue(per_run_fits(0, 0, 0))
        self.assertFalse(per_run_fits(0, 0, 1))

    def test_ceiling_is_inclusive_at_the_edge(self):
        self.assertTrue(per_run_fits(10, 8, 2))
        self.assertFalse(per_run_fits(10, 8, 3))

    def test_negative_fails_closed(self):
        with self.assertRaises(FailClosedError):
            per_run_fits(10, 0, -1)
        with self.assertRaises(FailClosedError):
            per_run_fits(-1, 0, 0)


class TokensFromPayload(unittest.TestCase):
    def test_missing_is_zero(self):
        self.assertEqual(tokens_from_payload({}), 0)
        self.assertEqual(tokens_from_payload(None), 0)

    def test_non_int_fails_closed(self):
        with self.assertRaises(FailClosedError):
            tokens_from_payload({"tokens": "8"})
        with self.assertRaises(FailClosedError):
            tokens_from_payload({"tokens": True})


class AudCentsFromPayload(unittest.TestCase):
    def test_missing_is_zero(self):
        self.assertEqual(aud_cents_from_payload({}), 0)
        self.assertEqual(aud_cents_from_payload(None), 0)

    def test_non_int_fails_closed(self):
        with self.assertRaises(FailClosedError):
            aud_cents_from_payload({"aud_cents": "50"})
        with self.assertRaises(FailClosedError):
            aud_cents_from_payload({"aud_cents": True})

    def test_value_is_returned(self):
        self.assertEqual(aud_cents_from_payload({"aud_cents": 250}), 250)


class BothCeilings(unittest.TestCase):
    def test_per_run_refusal_does_not_touch_node_ledger(self):
        q = _quota()
        env = _env(budget_tokens=0)
        d = admit_token_spend(
            env, q, "alpha", already_consumed=0, request=5, now_epoch_s=_NOW)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "token:per-run-ceiling")
        self.assertEqual(q.spent(_NOW, "alpha"), 0)

    def test_node_refusal_after_per_run_pass(self):
        q = _quota()  # node ceiling 40_000; alpha share 20_000
        env = _env(budget_tokens=50_000)
        # visible 10_000 * 2.6 multiplier = 26_000 > alpha 20_000
        d = admit_token_spend(
            env, q, "alpha", already_consumed=0, request=10_000,
            now_epoch_s=_NOW)
        self.assertFalse(d.allowed)
        self.assertTrue(d.rule.startswith("quota:"))

    def test_both_pass(self):
        q = _quota()
        env = _env(budget_tokens=100)
        d = admit_token_spend(
            env, q, "alpha", already_consumed=0, request=10, now_epoch_s=_NOW)
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule, "token:both-ceilings")
        self.assertIn("per-run-ceiling", d.checks)

    def test_admit_never_grants_send(self):
        q = _quota()
        env = _env(budget_tokens=100)
        d = admit_token_spend(
            env, q, "alpha", already_consumed=0, request=1, now_epoch_s=_NOW)
        self.assertTrue(d.allowed)
        self.assertFalse(grants_send(d))
        self.assertNotIn(d.rule, SEND_STATES)

    def test_grants_send_fails_closed_if_a_decision_names_a_send_state(self):
        poisoned = Decision(
            True, RiskTier.GREEN, "oops send_authorized",
            rule="token:forged")
        with self.assertRaises(FailClosedError):
            grants_send(poisoned)

    def test_ready_is_listed_and_is_not_a_send_grant(self):
        # campaign_envelope_ready is a draft name. Mentioning it in a
        # token Decision is a defect, not authorization.
        self.assertIn("campaign_envelope_ready", SEND_STATES)
        self.assertIn("send_authorized", SEND_STATES)
        self.assertIn("quote_sent", SEND_STATES)
        poisoned = Decision(
            True, RiskTier.GREEN, "promote campaign_envelope_ready",
            rule="token:forged")
        with self.assertRaises(FailClosedError):
            grants_send(poisoned)
