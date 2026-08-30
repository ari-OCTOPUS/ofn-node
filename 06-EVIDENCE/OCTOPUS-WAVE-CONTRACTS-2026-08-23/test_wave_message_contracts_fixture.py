# -*- coding: utf-8 -*-
"""Schema-only fixture for OCTOPUS-WAVE-CONTRACTS-2026-08-23 (no live TG)."""
from __future__ import annotations
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACTS = HERE / "CONTRACTS.json"
SCHEMA = HERE / "message-path-contract.schema.json"


class WaveMessageContractsFixture(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(CONTRACTS.read_text(encoding="utf-8"))
        self.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_schema_const(self):
        self.assertEqual(self.doc["schema"], "octopus-wave-message-contracts/1")
        self.assertEqual(self.schema.get("$id"), "octopus.wave-message-contracts.v1")

    def test_required_waves_present(self):
        for k in ("Wave-1", "Wave-B", "A13", "A18"):
            self.assertIn(k, self.doc["waves"])

    def test_a13_is_pass_historical(self):
        self.assertEqual(self.doc["waves"]["A13"]["status"], "PASS")
        paths = self.doc["waves"]["A13"]["evidence_paths_only"]
        self.assertTrue(any("A13-TRACE" in p for p in paths))

    def test_a18_never_pass(self):
        a18 = self.doc["waves"]["A18"]
        self.assertTrue(a18["pass_claim_forbidden"])
        self.assertEqual(a18["do_not_claim"], "PASS")
        self.assertNotEqual(a18["status"], "PASS")
        self.assertIn(a18["status"], {"PARTIAL_BLOCKED", "BLOCKED", "PARTIAL"})
        self.assertGreaterEqual(len(a18["blockers"]), 1)

    def test_wave_b_pollkinds_nonempty(self):
        kinds = self.doc["waves"]["Wave-B"]["message_paths"]["PollKind"]
        self.assertIn("OK", kinds)
        self.assertIn("LEASE_DENIED", kinds)

    def test_minimal_schema_shape(self):
        # Lightweight draft-agnostic checks (no jsonschema dependency required).
        req = self.schema["required"]
        for k in req:
            self.assertIn(k, self.doc)
        for k in self.schema["properties"]["waves"]["required"]:
            self.assertIn(k, self.doc["waves"])


if __name__ == "__main__":
    unittest.main()
