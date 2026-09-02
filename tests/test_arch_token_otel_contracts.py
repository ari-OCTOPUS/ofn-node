"""Docs-vs-code for token budgets, agent contracts, and the OTel map.

Numbers in the architecture files are tests, not sentences (CLAUDE.md
§8-الف). This module reads the documents that exist on main and asserts
they still match the code. It does not create ``otel_map.py`` or
``revenue_states.py`` — those files belong to open PR #77.
"""

from __future__ import annotations

import os
import re
import unittest

from ofn.kernel.callbudget import DEFAULT_CAPS
from ofn.kernel.domain import Decision, RiskTier
from ofn.kernel.envelope import create_envelope
from ofn.kernel import events as ev
from ofn.kernel.errors import FailClosedError
from ofn.kernel.routing import Rung
from ofn.kernel.token_ceiling import SEND_STATES, grants_send

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUDGETS = os.path.join(ROOT, "docs", "octopus-os", "06-TOKEN-BUDGETS.yaml")
CONTRACTS = os.path.join(ROOT, "docs", "octopus-os", "02-AGENT-CONTRACTS.yaml")
OTEL = os.path.join(ROOT, "docs", "octopus-os", "OTEL-EVENT-MAPPING.md")

_CAP_LINE = re.compile(
    r"^\s+(RULES|LOCAL|REMOTE|REMOTE_DEEP):\s+(\d+)\b", re.M)
_FACTORY = re.compile(r'factory:\s*"([^"]+)"')
_HALT_IMPL = re.compile(r'halt:\s*\{[^}]*impl:\s*"([^"]+)"')
_HALT_GATE = re.compile(r'halt:\s*\{[^}]*gate:\s*"([^"]+)"')
_OTEL_KIND = re.compile(r"^\|\s+([A-Z_]+)\s+\|", re.M)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class TokenBudgetDocMatchesCode(unittest.TestCase):
    def test_daily_call_caps_mirror_default_caps(self):
        text = _read(BUDGETS)
        documented = {name: int(value) for name, value in _CAP_LINE.findall(text)}
        self.assertEqual(
            documented,
            {
                "RULES": DEFAULT_CAPS[Rung.RULES],
                "LOCAL": DEFAULT_CAPS[Rung.LOCAL],
                "REMOTE": DEFAULT_CAPS[Rung.REMOTE],
                "REMOTE_DEEP": DEFAULT_CAPS[Rung.REMOTE_DEEP],
            },
        )

    def test_doc_names_the_two_envelope_budget_fields(self):
        text = _read(BUDGETS)
        self.assertIn("budget_tokens", text)
        self.assertIn("budget_aud_cents", text)
        env = create_envelope(
            goal="doc fixture", risk_tier="GREEN", authority_level="A1",
            idempotency_key="idem-doc", 
            acceptance_criteria_hash="a" * 64,
            now_epoch_s=1780000000, rand="a1b2c3d4e5f6a7b8",
            deadline_iso="2026-09-09T12:00:00Z",
        )
        self.assertTrue(hasattr(env, "budget_tokens"))
        self.assertTrue(hasattr(env, "budget_aud_cents"))


class AgentContractDocPointsAtRealModules(unittest.TestCase):
    def test_factory_and_halt_paths_import(self):
        text = _read(CONTRACTS)
        factory = _FACTORY.search(text)
        halt_impl = _HALT_IMPL.search(text)
        halt_gate = _HALT_GATE.search(text)
        self.assertIsNotNone(factory)
        self.assertIsNotNone(halt_impl)
        self.assertIsNotNone(halt_gate)
        self.assertEqual(factory.group(1), "ofn.kernel.envelope.create_envelope")
        self.assertEqual(halt_impl.group(1), "ofn.adapters.halt_flag")
        self.assertEqual(halt_gate.group(1), "ofn.adapters.run_gate.RunGate")
        from ofn.kernel.envelope import create_envelope as factory_fn
        from ofn.adapters import halt_flag
        from ofn.adapters.run_gate import RunGate
        self.assertTrue(callable(factory_fn))
        self.assertTrue(callable(halt_flag.halt_flag_active))
        self.assertTrue(callable(RunGate))


class OtelMapNamesSpineEvents(unittest.TestCase):
    def test_mapped_kinds_are_real_event_kinds(self):
        text = _read(OTEL)
        kinds = _OTEL_KIND.findall(text)
        self.assertTrue(kinds, "OTel table has no event kinds")
        unknown = [k for k in kinds if k not in ev.EVENT_KINDS]
        self.assertEqual(unknown, [], f"OTel map names unknown kinds: {unknown}")
        sealed = [k for k in kinds if k in ev.FORBIDDEN_EFFECT_KINDS]
        self.assertEqual(sealed, [], "OTel map must not project send/ready")

    def test_doc_says_otel_is_a_projection_not_the_ledger(self):
        text = _read(OTEL)
        self.assertIn("projection", text.lower())
        self.assertIn("never the ledger", text.lower())


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_token_admit_never_grants_send(self):
        decision = Decision(
            True, RiskTier.GREEN, "within ceilings", rule="token:both-ceilings")
        self.assertFalse(grants_send(decision))
        self.assertNotIn("campaign_envelope_ready", SEND_STATES)
        self.assertIn("send_authorized", SEND_STATES)
        self.assertIn("quote_sent", SEND_STATES)

    def test_send_name_in_decision_fails_closed(self):
        with self.assertRaises(FailClosedError):
            grants_send(Decision(
                True, RiskTier.GREEN, "oops send_authorized",
                rule="token:forged"))


if __name__ == "__main__":
    unittest.main()
