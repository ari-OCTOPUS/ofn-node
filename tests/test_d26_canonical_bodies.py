"""D-26 is a recorded owner package, not an implementation green-light.

The owner accepted the STAGE-01 senior package and later attested that
all three partners signed. These tests keep two records apart: the
attestation is true, independent observation by this vantage is still
false. Wave 1 did not start.
"""

from __future__ import annotations

import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATIFICATION = os.path.join(
    ROOT,
    "docs",
    "octopus-surgery",
    "stage-01-lineage-scan",
    "2026-09-01",
    "OWNER-RATIFICATION.json",
)
DECISIONS = os.path.join(ROOT, "DECISIONS.md")
RECORD = os.path.join(
    ROOT, "docs", "architecture", "DECISION-canonical-bodies-2026-09-01.md"
)

FORBIDDEN_NEW_MODULES = (
    "ofn/adapters/mcp_server.py",
    "ofn/agents/mcp_server.py",
    "ofn/kernel/capability_token.py",
    "ofn/adapters/capability_token.py",
    "ofn/adapters/memory_chain.py",
    "octopus_observation/memory_chain.py",
    "ofn/adapters/model_cost_pool.py",
    "spec/octopus.tla",
    "vbaa",
    "VBAA",
    "octopus-unified-chat/TYPED-EVENTS-RUN-ID-EXECUTION-PLAN-2026-08-12.md",
)


def _load() -> dict:
    with open(RATIFICATION, encoding="utf-8") as fh:
        return json.load(fh)


class TestRatificationIsARecordNotASignatureForge(unittest.TestCase):
    def setUp(self):
        self.data = _load()

    def test_schema_and_ids(self):
        self.assertEqual(self.data["schema"], "octopus.owner_ratification.v1")
        self.assertEqual(self.data["decision_id"], "D-26")
        self.assertEqual(self.data["speaker_role"], "owner")

    def test_owner_attests_signatures_and_this_vantage_did_not_hear_them(self):
        self.assertTrue(self.data["binds_partnership"])
        self.assertTrue(self.data["owner_attests_all_signed"])
        self.assertEqual(self.data["partner_countersign_status"], "owner_attested")
        self.assertEqual(self.data["partners"], ["maliheh", "abbas", "saba"])
        self.assertFalse(self.data["partner_voices_independently_observed"])
        texts = [row["text"] for row in self.data["utterances"]]
        self.assertIn("همشون امضا کردن", texts)

    def test_registration_does_not_authorize_build_or_egress(self):
        for key in (
            "implementation_authorized",
            "merge_authorized",
            "deploy_authorized",
            "wire_authorized",
        ):
            self.assertFalse(self.data[key], key)
        self.assertFalse(self.data["waves"]["wave_1_started"])
        self.assertFalse(self.data["waves"]["auto_advance"])
        self.assertFalse(self.data["business_parallel"]["writes_revenue_sent_booking"])


class TestCanonicalSplit(unittest.TestCase):
    def setUp(self):
        self.data = _load()

    def test_bodies(self):
        bodies = self.data["canonical_bodies"]
        self.assertEqual(bodies["business"], "ofn-node")
        self.assertEqual(bodies["architecture"], "vault")
        self.assertEqual(bodies["mesh"], "after_edge_contract")
        self.assertEqual(bodies["vault_to_public_ofn_node"], "forbidden")

    def test_real_means_has_three_independent_parts(self):
        self.assertEqual(
            self.data["real_means"],
            [
                "code_on_canonical_body",
                "failing_test_if_claim_false",
                "independent_receipt",
            ],
        )

    def test_wave_1_is_vault_only(self):
        self.assertEqual(self.data["waves"]["wave_1_body"], "vault")
        self.assertEqual(
            self.data["waves"]["wave_1_items"],
            ["typed_envelope", "append_only_run_store", "h1_financial_idempotency"],
        )

    def test_existing_edge_contract_is_board_events(self):
        rel = self.data["ofn_node_edge_contract"]
        self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)))
        self.assertEqual(self.data["h1_on_ofn_node"], "harvest-not-financial-idempotency")


class TestForbidsStillHoldOnThisTree(unittest.TestCase):
    def test_forbidden_modules_absent(self):
        for rel in FORBIDDEN_NEW_MODULES:
            self.assertFalse(
                os.path.exists(os.path.join(ROOT, rel)),
                f"D-26 forbid broken: {rel} now exists",
            )

    def test_wire_drift_guard_still_present(self):
        self.assertTrue(
            os.path.isfile(os.path.join(ROOT, "tests", "test_octopus_wire_drift.py"))
        )

    def test_secret_rotation_still_a_deliberate_shut_gate(self):
        from tools.repo_baseline import DELIBERATELY_SHUT
        self.assertIn("secret_rotation", DELIBERATELY_SHUT)

    def test_prose_files_carry_d26_and_the_honesty_clause(self):
        for path in (DECISIONS, RECORD):
            with open(path, encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn("D-26", body)
            self.assertIn("partner_voices_independently_observed", body)
        with open(DECISIONS, encoding="utf-8") as fh:
            decisions = fh.read()
        self.assertIn("خانوادهٔ envelope دوم", decisions)
        self.assertIn("partner_voices_independently_observed = false", decisions)
        self.assertIn("owner_attests_all_signed = true", decisions)
        data = _load()
        self.assertIn("second-envelope-family-on-ofn-node", data["forbid"])
