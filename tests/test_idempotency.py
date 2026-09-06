"""Contract tests for envelope binding hash (create-level dedup witness).

The store collapses a reused idempotency_key. This hash is the independent
record of *what* that key named. Two envelopes with the same key but a
different goal must not bind equally — otherwise a silent collapse is a lie.
"""

from __future__ import annotations

import hashlib
import unittest

from ofn.kernel.envelope import TaskEnvelope, create_envelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.idempotency import (
    envelope_binding_hash, envelope_binding_material, same_contract,
)

_AC = hashlib.sha256(b"binding fixture").hexdigest()
_NOW = 1780000000
_RAND = "a1b2c3d4e5f6a7b8"
_DEADLINE = "2026-09-09T12:00:00Z"


def _env(**overrides):
    kwargs = dict(
        goal="score three leads", risk_tier="GREEN", authority_level="A1",
        idempotency_key="idem-bind-1", acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand=_RAND, deadline_iso=_DEADLINE,
    )
    kwargs.update(overrides)
    return create_envelope(**kwargs)


class BindingIsOfTheContractNotTheRunId(unittest.TestCase):
    def test_same_contract_different_rand_still_binds(self):
        a = _env(rand="aaaaaaaaaa")
        b = _env(rand="bbbbbbbbbb")
        self.assertNotEqual(a.run_id, b.run_id)
        self.assertTrue(same_contract(a, b))
        self.assertEqual(envelope_binding_hash(a), envelope_binding_hash(b))

    def test_hash_is_sha256_hex(self):
        digest = envelope_binding_hash(_env())
        self.assertEqual(len(digest), 64)
        int(digest, 16)  # must be hex


class DifferentContractsDoNotBind(unittest.TestCase):
    def test_different_goal_does_not_bind(self):
        self.assertFalse(same_contract(_env(goal="alpha"), _env(goal="beta")))

    def test_same_key_different_budget_does_not_bind(self):
        # The dangerous case: reuse the key, change the money cap.
        left = _env(idempotency_key="same", budget_aud_cents=0)
        right = _env(idempotency_key="same", budget_aud_cents=2500)
        self.assertEqual(left.idempotency_key, right.idempotency_key)
        self.assertFalse(same_contract(left, right))

    def test_different_deadline_does_not_bind(self):
        self.assertFalse(same_contract(
            _env(deadline_iso="2026-09-09T12:00:00Z"),
            _env(deadline_iso="2026-09-10T12:00:00Z"),
        ))

    def test_allowlist_order_is_significant(self):
        # An allowlist is a closed set with order as written. Swapping
        # names is a different contract until the store says otherwise.
        self.assertFalse(same_contract(
            _env(allowed_tools=("score", "draft")),
            _env(allowed_tools=("draft", "score")),
        ))

    def test_newline_in_goal_cannot_collide_with_separator(self):
        # Length-safe hashing: a goal that contains the join character
        # must not equal a split across two fields.
        sneaky = _env(goal="alpha\nrisk_tier=RED")
        honest = _env(goal="alpha")
        self.assertFalse(same_contract(sneaky, honest))
        self.assertNotEqual(
            envelope_binding_material(sneaky),
            envelope_binding_material(honest),
        )


class ReadyIsNotABindingFact(unittest.TestCase):
    def test_direct_dataclass_with_same_contract_binds(self):
        env = _env()
        twin = TaskEnvelope(
            version=env.version, run_id="run-1780000000-cccccccccc",
            goal=env.goal, risk_tier=env.risk_tier,
            authority_level=env.authority_level,
            idempotency_key=env.idempotency_key,
            acceptance_criteria_hash=env.acceptance_criteria_hash,
            budget_tokens=env.budget_tokens,
            budget_aud_cents=env.budget_aud_cents,
            deadline_iso=env.deadline_iso,
            allowed_tools=env.allowed_tools,
            parent_evidence=env.parent_evidence,
        )
        self.assertTrue(same_contract(env, twin))

    def test_non_envelope_fails_closed(self):
        with self.assertRaises(FailClosedError):
            envelope_binding_material({"goal": "nope"})  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
