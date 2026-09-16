# -*- coding: utf-8 -*-
"""تستِ chord — پرتابل (بدونِ مسیرِ ویندوزی/REAL_VAULT؛ سندباکس py3.10 و ویندوز py3.13).
اجرا:  python -X utf8 _ops/tests/test_chord.py
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # _ops/

from chord.schemas import (DIMENSIONS, DEFAULT_TARGETS, DEFAULT_WEIGHTS,
                           Observation, StateVector, Verdict, clamp01)
from chord.metrics import weighted_distance, component_gaps, top_gaps
from chord.state_vector import build_state_vector, NEUTRAL_VALUE
from chord.uncertainty_gate import gate
from chord.repair_policy import assess, FORBIDDEN_ACTIONS
from chord.observation import (from_test_result, from_log, mark_contradiction,
                               count_contradictions, scrub_summary)
from chord.adapters.llm_adapter import extract_observation, LLM_STRENGTH_CAP
from chord.adapters.doctor_adapter import shadow_assess
from chord.adapters.telegram_cards import render_assessment_card, render_health_summary
from chord import ledger


def _vec(coverage=0.9, uncertainty=0.1, **overrides) -> StateVector:
    vals = {d: DEFAULT_TARGETS[d] for d in DIMENSIONS}
    vals.update(overrides)
    return StateVector(values=vals, evidence_coverage=coverage,
                       uncertainty=uncertainty, generated_from=["OBS-x"])


class TestMath(unittest.TestCase):
    def test_zero_distance_at_target(self):
        self.assertAlmostEqual(weighted_distance(_vec()), 0.0, places=9)

    def test_known_value(self):
        # فقط evidence_quality=0.5 → d = sqrt(1.5*0.25/10.5) ≈ 0.18898
        v = _vec(evidence_quality=0.5)
        self.assertAlmostEqual(weighted_distance(v), 0.18898, places=4)

    def test_clamp_and_nan(self):
        self.assertEqual(clamp01(5), 1.0)
        self.assertEqual(clamp01(-3), 0.0)
        self.assertEqual(clamp01("junk", 0.2), 0.2)
        self.assertEqual(clamp01(float("nan"), 0.3), 0.3)

    def test_negative_weight_rejected(self):
        v = _vec()
        v.weights["operational_risk"] = -1
        with self.assertRaises(ValueError):
            weighted_distance(v)

    def test_component_and_top_gaps(self):
        v = _vec(test_health=0.2, evidence_quality=0.7)
        gaps = component_gaps(v)
        self.assertAlmostEqual(gaps["test_health"]["gap"], -0.8, places=6)
        self.assertEqual(top_gaps(v, 1)[0][0], "test_health")


class TestVectorBuild(unittest.TestCase):
    def test_no_observations_is_unknown_not_healthy(self):
        v = build_state_vector([], [])
        self.assertEqual(v.evidence_coverage, 0.0)
        self.assertGreaterEqual(v.uncertainty, 0.8)
        self.assertEqual(v.values["test_health"], NEUTRAL_VALUE)
        a = assess("MIS-t", v)
        self.assertEqual(a.verdict, Verdict.UNKNOWN)
        self.assertFalse(a.approval_required)
        self.assertEqual(a.allowed_actions, ["observe.collect"])

    def test_claims_flow_into_dims(self):
        ob = from_test_result("test_x", True, "ok", mission_id="MIS-t")
        v = build_state_vector([ob], [{"test_health": 1.0}])
        self.assertAlmostEqual(v.values["test_health"], 1.0, places=6)
        self.assertIn(ob.observation_id, v.generated_from)

    def test_invalid_observation_excluded(self):
        bad = Observation(source_type="log", source_ref="", payload_summary="x")
        v = build_state_vector([bad], [{"test_health": 1.0}])
        self.assertEqual(v.generated_from, [])


class TestGateAndPolicy(unittest.TestCase):
    def test_low_coverage_unknown(self):
        g = gate(_vec(coverage=0.2))
        self.assertFalse(g["open"])
        self.assertEqual(g["verdict_hint"], Verdict.UNKNOWN)

    def test_mid_coverage_observe_more(self):
        a = assess("MIS-t", _vec(coverage=0.5))
        self.assertEqual(a.verdict, Verdict.OBSERVE_MORE)

    def test_contradiction_blocks_auto(self):
        a = assess("MIS-t", _vec(), contradiction_count=1)
        self.assertEqual(a.verdict, Verdict.OBSERVE_MORE)
        self.assertNotIn("code.diff", a.allowed_actions)

    def test_high_uncertainty_closes_patch(self):
        a = assess("MIS-t", _vec(uncertainty=0.7))
        self.assertEqual(a.verdict, Verdict.OBSERVE_MORE)

    def test_healthy(self):
        a = assess("MIS-t", _vec())
        self.assertEqual(a.verdict, Verdict.HEALTHY)
        self.assertFalse(a.approval_required)

    def test_propose_patch_never_allows_apply(self):
        a = assess("MIS-t", _vec(test_health=0.4, evidence_quality=0.8,
                                 operational_risk=0.2, reversibility=0.9))
        self.assertEqual(a.verdict, Verdict.PROPOSE_PATCH)
        self.assertFalse(a.approval_required)
        for bad in FORBIDDEN_ACTIONS:
            self.assertNotIn(bad, a.allowed_actions)
        self.assertIn("code.test", a.allowed_actions)

    def test_high_risk_needs_approval(self):
        a = assess("MIS-t", _vec(operational_risk=0.7))
        self.assertEqual(a.verdict, Verdict.REQUEST_APPROVAL)
        self.assertTrue(a.approval_required)

    def test_low_reversibility_needs_approval(self):
        a = assess("MIS-t", _vec(reversibility=0.2))
        self.assertEqual(a.verdict, Verdict.REQUEST_APPROVAL)

    def test_money_context_forces_approval_even_if_calm(self):
        a = assess("MIS-t", _vec(), context={"touches_money": True})
        self.assertEqual(a.verdict, Verdict.REQUEST_APPROVAL)
        self.assertTrue(a.approval_required)

    def test_kill_switch_blocks(self):
        a = assess("MIS-t", _vec(), context={"stop_organism": True})
        self.assertEqual(a.verdict, Verdict.BLOCK)

    def test_secret_taint_blocks(self):
        a = assess("MIS-t", _vec(), context={"secret_observation": True})
        self.assertEqual(a.verdict, Verdict.BLOCK)
        self.assertTrue(a.approval_required)


class TestObservationTools(unittest.TestCase):
    def test_scrub_redacts_secret_patterns(self):
        s = scrub_summary("failed: api_key=abc123 token xyz")
        self.assertNotIn("api_key", s)
        self.assertIn("[REDACTED]", s)

    def test_contradiction_marking_and_count(self):
        a = from_log("log.txt", "service UP")
        b = from_log("probe", "service DOWN")
        mark_contradiction(a, b)
        mark_contradiction(a, b)  # idempotent
        self.assertEqual(count_contradictions([a, b]), 1)


class TestLLMAdapter(unittest.TestCase):
    def test_malformed_json_rejected(self):
        ob, claims, reason = extract_observation("some log", "ref", ask_fn=lambda p: "not json")
        self.assertIsNone(ob)
        self.assertTrue(reason.startswith("malformed-llm-output"))

    def test_offline_is_honest_none(self):
        ob, claims, reason = extract_observation("x", "ref", ask_fn=lambda p: None)
        self.assertIsNone(ob)
        self.assertIn("llm-unavailable", reason)

    def test_missing_source_ref_rejected(self):
        ob, _, reason = extract_observation("x", "", ask_fn=lambda p: "{}")
        self.assertIsNone(ob)
        self.assertIn("source_ref", reason)

    def test_valid_json_capped_strength_and_filtered_dims(self):
        payload = json.dumps({"payload_summary": "sync worker stale error",
                              "evidence_strength": 0.99,
                              "dim_claims": {"dependency_health": 0.3,
                                             "not_a_dim": 1.0}})
        ob, claims, reason = extract_observation("raw", "telegram:msg1",
                                                 ask_fn=lambda p: f"noise {payload} noise")
        self.assertEqual(reason, "ok")
        self.assertLessEqual(ob.evidence_strength, LLM_STRENGTH_CAP)
        self.assertEqual(list(claims), ["dependency_health"])

    def test_llm_exception_contained(self):
        def boom(p):
            raise RuntimeError("x")
        ob, _, reason = extract_observation("x", "ref", ask_fn=boom)
        self.assertIsNone(ob)
        self.assertIn("llm-error", reason)


class TestLedgerAndDoctor(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["CHORD_STATE_DIR"] = self._tmp.name

    def tearDown(self):
        os.environ.pop("CHORD_STATE_DIR", None)
        self._tmp.cleanup()

    def test_hash_chain_and_dedup(self):
        r1 = ledger.append({"a": 1}, dedup_key="k1")
        r2 = ledger.append({"a": 2}, dedup_key="k2")
        self.assertTrue(r1["ok"] and r2["ok"])
        lines = [json.loads(x) for x in
                 Path(ledger.ledger_path()).read_text("utf-8").splitlines()]
        self.assertEqual(lines[1]["prev_sha256"], lines[0]["sha256"])
        r3 = ledger.append({"a": 2}, dedup_key="k2")
        self.assertEqual(r3.get("skipped"), "dedup")
        self.assertTrue(ledger.verify_chain()["ok"])

    def test_shadow_assess_logs_and_never_executes(self):
        ob = from_test_result("test_sync", False, "stale API error", "MIS-42")
        rec = shadow_assess("MIS-42", [ob], [{"test_health": 0.0,
                                              "dependency_health": 0.4}])
        self.assertIn(rec["verdict"], Verdict.ALL)
        self.assertTrue(rec.get("shadow"))
        for bad in FORBIDDEN_ACTIONS:
            self.assertNotIn(bad, rec["allowed_actions"])
        self.assertTrue(Path(ledger.ledger_path()).exists())
        n1 = len(Path(ledger.ledger_path()).read_text("utf-8").splitlines())
        shadow_assess("MIS-42", [ob], [{"test_health": 0.0,
                                        "dependency_health": 0.4}])  # dedup
        n2 = len(Path(ledger.ledger_path()).read_text("utf-8").splitlines())
        self.assertEqual(n1, n2)


class TestCards(unittest.TestCase):
    def test_assessment_card(self):
        a = assess("MIS-77", _vec(test_health=0.3)).to_dict()
        card = render_assessment_card(a)
        self.assertIn("MIS-77", card)
        self.assertIn(a["verdict"], card)
        self.assertIn("shadow", card)
        self.assertNotIn("Traceback", card)

    def test_health_summary_orders_worst_first(self):
        items = [{"mission_id": "M1", "verdict": "HEALTHY", "weighted_distance": 0.1},
                 {"mission_id": "M2", "verdict": "BLOCK", "weighted_distance": 0.9}]
        out = render_health_summary(items)
        self.assertLess(out.index("M2"), out.index("M1"))
        self.assertIn("CHORD", render_health_summary([]))


if __name__ == "__main__":
    print(f"[test_chord] py={sys.version.split()[0]}")
    unittest.main(verbosity=1)
