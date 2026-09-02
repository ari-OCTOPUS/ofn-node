"""D-27 unlocks authorization. It does not flip real flags or forge facts.

D-26 remains the historical record (authorization false at that time).
D-27 supersedes those fields only. Four facts stay outside decree.
"""

from __future__ import annotations

import ast
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRECTIVE = os.path.join(
    ROOT,
    "docs",
    "octopus-surgery",
    "stage-01-lineage-scan",
    "2026-09-01",
    "D-27-OWNER-DIRECTIVE.json",
)
D26 = os.path.join(
    ROOT,
    "docs",
    "octopus-surgery",
    "stage-01-lineage-scan",
    "2026-09-01",
    "OWNER-RATIFICATION.json",
)
CONTRADICTIONS = os.path.join(
    ROOT,
    "docs",
    "octopus-surgery",
    "stage-01-lineage-scan",
    "2026-09-01",
    "CONTRADICTIONS.md",
)
DECISIONS = os.path.join(ROOT, "DECISIONS.md")
RECORD = os.path.join(
    ROOT, "docs", "architecture", "DECISION-d27-unlock-2026-09-02.md"
)
CONFIG = os.path.join(ROOT, "ofn", "config.py")


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class TestD27AuthorizationBlock(unittest.TestCase):
    def setUp(self):
        self.data = _load(DIRECTIVE)

    def test_schema_and_supersede_scope(self):
        self.assertEqual(self.data["schema"], "octopus.owner_directive.v1")
        self.assertEqual(self.data["decision_id"], "D-27")
        self.assertEqual(self.data["supersedes"], "D-26 authorization fields only")
        self.assertEqual(self.data["speaker_role"], "owner")
        self.assertFalse(self.data["propose_only_mode"])
        self.assertTrue(self.data["parallel_execution"])
        self.assertTrue(self.data["auto_advance_waves"])

    def test_authorization_fields_are_true(self):
        for key in (
            "implementation_authorized",
            "merge_authorized",
            "deploy_authorized",
            "wire_authorized",
            "external_effect_authorized",
            "board_access_authorized",
            "money_authorized",
        ):
            self.assertTrue(self.data[key], key)

    def test_partner_voices_still_not_independently_observed(self):
        self.assertTrue(self.data["owner_attests_all_signed"])
        self.assertFalse(self.data["partner_voices_independently_observed"])

    def test_hard_limits_match_code_constants(self):
        from ofn.config import (
            D27_DAILY_SEND_CAP,
            D27_DAILY_SPEND_CAP_AUD,
            D27_KILL_SWITCH,
            D27_PER_BOARD_BUDGET_DEFAULT,
            D27_ROLLBACK_WINDOW_HOURS,
        )
        limits = self.data["hard_limits"]
        self.assertEqual(limits["daily_send_cap"], 25)
        self.assertEqual(limits["daily_spend_cap_aud"], 50)
        self.assertEqual(limits["per_board_budget_default"], 0)
        self.assertEqual(limits["kill_switch"], "OFN_EXTRA_CLOSED_GATES")
        self.assertEqual(limits["rollback_window_hours"], 24)
        self.assertEqual(D27_DAILY_SEND_CAP, 25)
        self.assertEqual(D27_DAILY_SPEND_CAP_AUD, 50)
        self.assertEqual(D27_PER_BOARD_BUDGET_DEFAULT, 0)
        self.assertEqual(D27_KILL_SWITCH, "OFN_EXTRA_CLOSED_GATES")
        self.assertEqual(D27_ROLLBACK_WINDOW_HOURS, 24)

    def test_cannot_be_decreed_list(self):
        self.assertEqual(
            self.data["cannot_be_decreed"],
            [
                "partner_voices_independently_observed",
                "saba_publish_consent_record",
                "real_secret_rotation",
                "shopify_telegram_payment_tos",
            ],
        )

    def test_flags_not_flipped_correct_the_unlock_prose(self):
        flags = self.data["flags_not_flipped"]
        self.assertIn("already 7000", flags["OFN_CONTROL_QUOTA_TOKENS"])
        self.assertIn("not set", flags["OFN_KEEP_GATES_OPEN"])
        self.assertIn("not defaulted", flags["OFN_WIRE_OUTBOUND"])
        self.assertEqual(
            self.data["writes_revenue_sent_booking"],
            "authorized_to_record_independent_receipts_only",
        )
        self.assertIsInstance(self.data["writes_revenue_sent_booking"], str)
        self.assertEqual(
            self.data["error_policy"],
            "demote_one_path_one_rung_not_lock_all_five",
        )
        from ofn.config import load
        self.assertEqual(load().control_quota_tokens, 7000)
        prose = os.path.join(
            ROOT,
            "docs",
            "octopus-surgery",
            "stage-01-lineage-scan",
            "2026-09-01",
            "sources",
            "D-27-UNLOCK-DIRECTIVE.md",
        )
        with open(prose, encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("پیش‌فرض ۰", body)

    def test_merge_authorized_is_not_github_self_merge(self):
        self.assertTrue(self.data["merge_authorized"])
        self.assertTrue(self.data["merge_authorized_is_not_self_merge"])
        self.assertFalse(self.data["github_self_merge"])
        self.assertEqual(self.data["pr65_merge"]["push_to_main"], "rejected")
        self.assertEqual(self.data["recommended_merge_order"], ["68", "67"])
        overlay = self.data["lanes_overlay"]
        self.assertFalse(overlay["lanes_csv_on_this_host"])
        self.assertEqual(overlay["L13"]["pr"], 68)
        self.assertFalse(
            os.path.isfile(os.path.join(ROOT, "LANES.csv")),
        )
        self.assertFalse(
            os.path.isfile(
                os.path.join(ROOT, "docs", "octopus-surgery", "LANES.csv")
            ),
        )

    def test_c009_is_on_the_closed_list(self):
        self.assertEqual(self.data["contradictions_closed_by_this"], ["C-009"])
        with open(CONTRADICTIONS, encoding="utf-8") as fh:
            body = fh.read()
        section = body.split("## C-009", 1)[1].split("## C-", 1)[0]
        self.assertIn("status | closed", section)
        self.assertIn("closed_by | D-27", section)

    def test_o3_and_s04_moved_to_open(self):
        self.assertEqual(self.data["opened_from_later"], ["O-3", "S-04"])


class TestD26StaysAHistoricalRecord(unittest.TestCase):
    def test_d26_authorization_fields_remain_false(self):
        data = _load(D26)
        self.assertEqual(data["decision_id"], "D-26")
        self.assertEqual(data["authorization_superseded_by"], "D-27")
        for key in (
            "implementation_authorized",
            "merge_authorized",
            "deploy_authorized",
            "wire_authorized",
        ):
            self.assertFalse(data[key], key)
        self.assertFalse(data["partner_voices_independently_observed"])


class TestRealFlagsStayEnvGated(unittest.TestCase):
    def test_flag_helper_only_accepts_one(self):
        with open(CONFIG, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src, filename=CONFIG)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_flag":
                segment = ast.get_source_segment(src, node)
                self.assertIsNotNone(segment)
                self.assertIn('== "1"', segment)
                found = True
        self.assertTrue(found)

    def test_load_config_defaults_do_not_arm_wire_or_silence_gate_expiry(self):
        keys = (
            "OFN_WIRE_OUTBOUND",
            "OFN_KEEP_GATES_OPEN",
            "OFN_PUBLIC_CATALOG",
            "OFN_COMMERCE_ROUTES",
            "OFN_EXTRA_CLOSED_GATES",
        )
        saved = {key: os.environ.pop(key, None) for key in keys}
        try:
            from ofn.config import load
            cfg = load()
            self.assertFalse(cfg.wire_outbound)
            self.assertFalse(cfg.public_catalog_enabled)
            self.assertFalse(cfg.commerce_routes_enabled)
            self.assertGreaterEqual(cfg.control_quota_tokens, 1)
            self.assertIn("miner_isolation", cfg.base_closed_gates)
            # D-28 moved GATE_OPEN_UNTIL_UTC forward. Live load() before
            # that date leaves secret_rotation open via the official
            # window, not via OFN_KEEP_GATES_OPEN. Re-close is proven
            # by freezing at the constant in test_gate_enforcement.
        finally:
            for key, value in saved.items():
                if value is not None:
                    os.environ[key] = value

    def test_prose_carries_d27_and_the_honesty_clause(self):
        for path in (DECISIONS, RECORD):
            with open(path, encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn("D-27", body)
            self.assertIn("partner_voices_independently_observed", body)
            self.assertIn("OFN_EXTRA_CLOSED_GATES", body)
            self.assertIn("PAINT-L5-001", body)
