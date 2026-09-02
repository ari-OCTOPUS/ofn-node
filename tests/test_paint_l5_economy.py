"""PAINT-L5-001 episode school — D-27.

One shared episode, five roles, no second Envelope, no WIRE, no
revenue without a receipt. Owner-approved and tests-green are not rewards.
"""

from __future__ import annotations

import ast
import os
import tempfile
import unittest

from octopus_survival.economy import (
    CLEAN_TO_PROPOSE_PROMOTION,
    EPISODE_FIELDS,
    FAKE_REWARDS,
    INDEPENDENT_REWARDS,
    MISSION,
    Economy,
    EconomyError,
    answers_lead_to_revenue,
)
from octopus_survival.loop import Envelope as SurvivalEnvelope


def school(tmp: str, *, level: str = "A1", wire: bool = False) -> Economy:
    return Economy(tmp, clock=lambda: 1_800_000_000, granted_level=level, wire_open=wire)


class TestContract(unittest.TestCase):
    def test_mission_and_exact_fields(self):
        self.assertEqual(MISSION, "PAINT-L5-001")
        self.assertEqual(EPISODE_FIELDS, (
            "episode_id", "lead_evidence", "decision", "proposed_action",
            "approval", "execution_receipt", "cost", "revenue", "outcome",
            "teacher_correction", "lesson",
        ))

    def test_module_does_not_define_a_second_envelope(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "octopus_survival", "economy.py")
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        self.assertNotIn("Envelope", names)
        self.assertTrue(issubclass(SurvivalEnvelope, object))


class TestFiveRolesOneEpisode(unittest.TestCase):
    def test_roles_cannot_write_each_others_slots(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            with self.assertRaisesRegex(EconomyError, "cannot-write"):
                eco.apply("E1", "sensing", {"decision": "accept"})
            with self.assertRaisesRegex(EconomyError, "cannot-write"):
                eco.apply("E1", "selling", {"revenue": {"receipt_id": "x"}})

    def test_full_draft_loop_without_send(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            eco.apply("E1", "sensing", {"lead_evidence": {
                "title": "Interior repaint Cheltenham", "suburb": "Cheltenham",
            }})
            eco.apply("E1", "selling", {
                "decision": "accept_lead",
                "proposed_action": "draft_quote",
            })
            ep = eco.get("E1")
            self.assertEqual(ep.decision, "accept_lead")
            self.assertIsNone(ep.execution_receipt)
            self.assertIsNone(ep.revenue)


class TestGates(unittest.TestCase):
    def test_supply_side_is_wrong_recipient(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            with self.assertRaisesRegex(EconomyError, "wrong_recipient"):
                eco.apply("E1", "sensing", {"lead_evidence": {
                    "title": "We are hiring a painter",
                    "employmentType": "full_time",
                    "salary": "40 per hour",
                }})

    def test_a1_cannot_execute(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp, level="A1")
            eco.open("E1")
            with self.assertRaisesRegex(EconomyError, "draft-only"):
                eco.apply("E1", "execution", {
                    "approval": "owner-1",
                    "execution_receipt": {"kind": "local"},
                })

    def test_a2_needs_approval(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp, level="A2")
            eco.open("E1")
            with self.assertRaisesRegex(EconomyError, "approval"):
                eco.apply("E1", "execution", {
                    "execution_receipt": {"kind": "local"},
                })

    def test_send_refused_while_wire_closed(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp, level="A2", wire=False)
            eco.open("E1")
            with self.assertRaisesRegex(EconomyError, "WIRE"):
                eco.apply("E1", "execution", {
                    "approval": "owner-1",
                    "execution_receipt": {"kind": "send"},
                })

    def test_revenue_without_receipt_refused(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            with self.assertRaisesRegex(EconomyError, "revenue_without_receipt"):
                eco.apply("E1", "finance", {"revenue": {"amount_cents": 25000}})

    def test_receipt_moves_verified_income(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            eco.apply("E1", "finance", {
                "cost": {"amount_cents": 5000},
                "revenue": {"amount_cents": 25000, "receipt_id": "pay-1"},
            })
            self.assertEqual(eco.metrics()["verified_net_income_cents"], 20000)


class TestTeacher(unittest.TestCase):
    def test_correction_becomes_a_lesson_not_a_silent_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            eco.apply("E1", "selling", {
                "decision": "reject_lead",
                "proposed_action": "drop",
            })
            ep = eco.teach(
                "E1",
                agent_decision="reject_lead",
                teacher_decision="accept_lead",
                reason_code="SERVICE_AREA_MISCLASSIFIED",
                real_outcome="booked",
                lesson="Cheltenham تا محدوده تعیین‌شده قابل قبول است",
            )
            self.assertEqual(ep.teacher_correction["reason_code"],
                             "SERVICE_AREA_MISCLASSIFIED")
            self.assertEqual(ep.lesson, "Cheltenham تا محدوده تعیین‌شده قابل قبول است")
            self.assertEqual(ep.outcome, "booked")
            self.assertIsNone(ep.revenue)

    def test_owner_approved_is_not_a_reward(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            for fake in FAKE_REWARDS:
                with self.assertRaisesRegex(EconomyError, "not independent"):
                    eco.reward("E1", fake)
            eco.reward("E1", "qualified_lead")
            self.assertIn("qualified_lead", eco.get("E1").rewards)
            self.assertTrue(INDEPENDENT_REWARDS)


class TestPromotionAndDemotion(unittest.TestCase):
    def test_three_clean_episodes_propose_a2_but_not_a3_while_wire_closed(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp, level="A1", wire=False)
            for i in range(CLEAN_TO_PROPOSE_PROMOTION):
                eid = f"E{i}"
                eco.open(eid)
                eco.apply(eid, "selling", {
                    "decision": "accept_lead",
                    "proposed_action": "draft_quote",
                })
            self.assertEqual(eco.propose_promotion(), "A2")
            eco.grant("A2")
            self.assertEqual(eco.granted_level, "A2")
            for i in range(CLEAN_TO_PROPOSE_PROMOTION, CLEAN_TO_PROPOSE_PROMOTION * 2):
                eid = f"E{i}"
                eco.open(eid)
                eco.apply(eid, "selling", {
                    "decision": "accept_lead",
                    "proposed_action": "draft_quote",
                })
            self.assertIsNone(eco.propose_promotion())
            with self.assertRaisesRegex(EconomyError, "WIRE"):
                eco.grant("A3")

    def test_dangerous_error_steps_back_one_rung(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp, level="A2")
            eco.open("E1")
            self.assertEqual(eco.mark_dangerous("E1", "wrong_recipient"), "A1")
            self.assertEqual(eco.granted_level, "A1")


class TestMetricsAndPriority(unittest.TestCase):
    def test_autonomous_rate_ignores_owner_agreement_as_success_signal(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            eco.apply("E1", "selling", {
                "decision": "accept_lead", "proposed_action": "draft",
            })
            eco.open("E2")
            eco.apply("E2", "selling", {
                "decision": "reject_lead", "proposed_action": "drop",
            })
            eco.teach(
                "E2",
                agent_decision="reject_lead",
                teacher_decision="accept_lead",
                reason_code="SERVICE_AREA_MISCLASSIFIED",
                real_outcome="booked",
                lesson="Cheltenham ok",
            )
            rate = eco.metrics()["autonomous_correct_rate"]
            self.assertEqual(rate, 0.5)

    def test_pr_filter_rejects_architecture_without_the_loop(self):
        self.assertTrue(answers_lead_to_revenue("bind harvest lead_evidence to episode"))
        self.assertFalse(answers_lead_to_revenue("add another dashboard panel"))
        self.assertFalse(answers_lead_to_revenue("formal TLA+ model for coordination"))


class TestD27Caps(unittest.TestCase):
    def test_metrics_expose_the_hard_limits(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            metrics = eco.metrics()
            self.assertEqual(metrics["daily_send_cap"], 25)
            self.assertEqual(metrics["daily_spend_cap_aud"], 50)
            self.assertEqual(metrics["per_board_budget_default"], 0)

    def test_spend_over_cap_refuses_only_finance(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            eco.open("E1")
            eco.apply("E1", "sensing", {"lead_evidence": {"title": "Interior"}})
            with self.assertRaisesRegex(EconomyError, "spend-cap"):
                eco.apply("E1", "finance", {"cost": {"amount_cents": 5001}})
            eco.apply("E1", "selling", {
                "decision": "accept_lead",
                "proposed_action": "draft_quote",
            })
            self.assertEqual(eco.get("E1").decision, "accept_lead")
            self.assertIsNone(eco.get("E1").revenue)

    def test_send_cap_refuses_the_26th_send(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp, level="A2", wire=True)
            eco.daily_send_cap = 1
            eco.open("E1")
            eco.apply("E1", "execution", {
                "approval": "owner-1",
                "execution_receipt": {"kind": "send"},
            })
            eco.open("E2")
            with self.assertRaisesRegex(EconomyError, "send-cap"):
                eco.apply("E2", "execution", {
                    "approval": "owner-1",
                    "execution_receipt": {"kind": "send"},
                })
            eco.apply("E2", "sensing", {"lead_evidence": {"title": "still open"}})
            self.assertEqual(eco.get("E2").lead_evidence["title"], "still open")

    def test_board_budget_default_is_zero(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp)
            with self.assertRaisesRegex(EconomyError, "board-budget-zero"):
                eco.board_may_spend("board-180", 1)

    def test_dangerous_error_does_not_lock_the_school(self):
        with tempfile.TemporaryDirectory(prefix="econ-") as tmp:
            eco = school(tmp, level="A2")
            eco.open("E1")
            eco.mark_dangerous("E1", "wrong_recipient")
            eco.open("E2")
            eco.apply("E2", "selling", {
                "decision": "accept_lead",
                "proposed_action": "draft",
            })
            self.assertEqual(eco.granted_level, "A1")
            self.assertEqual(eco.get("E2").decision, "accept_lead")


if __name__ == "__main__":
    unittest.main()
