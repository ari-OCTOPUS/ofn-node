#!/usr/bin/env python3
"""test_g10_cognition.py — Comprehensive tests for G10 Cognition Layer (EQUIP G10).

Tests cover:
  1. Structured schemas (creation, validation, invariants)
  2. Task router (classification, routing, privacy override, cost constraint)
  3. Verifier (schema check, consistency, fabrication, contamination)
  4. Confidence calibrator (Brier score, inflation detection, ledger)
  5. Capability probe (register, probe pass/fail, self-model update)
  6. Causal guard (classification, spurious detection, ADR-013)
  7. Acceptance scenario (3 tasks: coding, retrieval, causal analysis)

No paid models. No network calls. Fixtures only.
$0, stdlib-only.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Ensure cognition package is importable
_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from structured_schemas import (
    ClaimStrength,
    PrivacyLevel,
    RoutingDecision,
    TaskClass,
    make_evidence,
    make_hypothesis,
    make_plan,
    make_proposal,
    make_verification_result,
    validate_structured_output,
)
from task_router import (
    _classify_task,
    _detect_privacy,
    fallback_chain,
    route_task,
    route_batch,
)
from verifier import (
    detect_fabrication,
    verify,
    verify_consistency,
    verify_schema,
)
from confidence_calibrator import (
    adjust_confidence,
    brier_score,
    calibration_bins,
    compute_calibration,
    detect_inflation,
    record_outcome,
)
from capability_probe import (
    get_capability_status,
    record_probe_result,
    register_capability,
    self_model_summary,
)
from causal_guard import (
    CORRELATION_CAUSAL_FIXTURE,
    analyze_synthetic_causal,
    classify_claim,
    detect_spurious_causal,
    guard_output,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

_passed = 0
_failed = 0
_tests = []


def _report(name: str, ok: bool, detail: str = ""):
    global _passed, _failed
    status = "PASS" if ok else "FAIL"
    sym = "ok" if ok else "FAIL"
    print(f"  {'ok' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""))
    _passed += int(ok)
    _failed += int(not ok)
    _tests.append({"name": name, "ok": ok})


# ═══════════════════════════════════════════════════════════════════════════════
# 1. STRUCTURED SCHEMAS (14 tests)
# ═══════════════════════════════════════════════════════════════════════════════

def test_structured_schemas():
    print("\n--- Structured Schemas ---")

    # S1: make_plan creates valid structure
    plan = make_plan(task_class="coding", description="test plan")
    _report("S1_make_plan_valid",
            plan["output_type"] == "plan" and
            plan["task_class"] == "coding" and
            plan["may_execute"] is False and
            "id" in plan and "ts" in plan)

    # S2: make_hypothesis has falsification condition
    hyp = make_hypothesis(statement="test", falsification_condition="if X then not")
    _report("S2_hypothesis_has_falsification",
            hyp["output_type"] == "hypothesis" and
            hyp["falsification_condition"] == "if X then not" and
            hyp["is_authority"] is False)

    # S3: make_evidence has evidence grade
    ev = make_evidence(claim_id="c1", evidence_grade="B")
    _report("S3_evidence_has_grade",
            ev["output_type"] == "evidence" and ev["evidence_grade"] == "B")

    # S4: make_proposal is never self-approved
    prop = make_proposal(description="test proposal")
    _report("S4_proposal_not_self_approved",
            prop["output_type"] == "proposal" and
            prop["self_approved"] is False)

    # S5: make_verification_result has advisory authority
    vr = make_verification_result(target_id="t1", verdict="VERIFIED")
    _report("S5_verification_advisory",
            vr["output_type"] == "verification_result" and
            vr["authority_level"] == "advisory")

    # S6: validate_structured_output accepts valid output
    valid = validate_structured_output(plan)
    _report("S6_validate_accepts_valid",
            valid["valid"] is True and len(valid["errors"]) == 0)

    # S7: validate_structured_output rejects missing fields
    invalid = validate_structured_output({"random": "data"})
    _report("S7_validate_rejects_invalid",
            invalid["valid"] is False and len(invalid["errors"]) > 0)

    # S8: confidence out of range detected
    bad_conf = make_plan(description="test")
    bad_conf["confidence"] = 1.5
    v = validate_structured_output(bad_conf)
    _report("S8_confidence_out_of_range",
            not v["valid"] and "confidence_out_of_range" in v["errors"])

    # S9: invalid evidence grade detected
    bad_grade = make_evidence(evidence_grade="Z")
    v = validate_structured_output(bad_grade)
    _report("S9_invalid_evidence_grade",
            not v["valid"] and "invalid_evidence_grade" in v["errors"])

    # S10: all outputs have schema_version
    for name, fn in [("plan", make_plan), ("hypothesis", make_hypothesis),
                     ("evidence", make_evidence), ("proposal", make_proposal),
                     ("verification_result", make_verification_result)]:
        out = fn() if name != "verification_result" else make_verification_result(target_id="t")
        has_version = "schema_version" in out
        _report(f"S10_schema_version_{name}", has_version)

    # S11: all outputs have unique IDs
    plan1 = make_plan()
    plan2 = make_plan()
    _report("S11_unique_ids", plan1["id"] != plan2["id"])

    # S12: all outputs have unique trace_ids
    _report("S12_unique_traces", plan1["trace_id"] != plan2["trace_id"])

    # S13: hypothesis causal claim_strength preserved
    hyp_causal = make_hypothesis(claim_strength=ClaimStrength.CAUSAL)
    _report("S13_causal_claim_preserved",
            hyp_causal["claim_strength"] == "causal" and
            hyp_causal["is_authority"] is False)

    # S14: planner never claims execution authority
    plan_exec = make_plan()
    _report("S14_planner_no_execute_authority",
            plan_exec.get("may_execute") is False)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TASK ROUTER (12 tests)
# ═══════════════════════════════════════════════════════════════════════════════

def test_task_router():
    print("\n--- Task Router ---")

    # R1: coding task routes to local
    r = route_task("implement a sorting function")
    _report("R1_coding_to_local",
            r["routing"] == "local" and r["task_class"] == "coding")

    # R2: retrieval task routes to local
    r = route_task("search for the configuration file")
    _report("R2_retrieval_to_local",
            r["routing"] == "local" and r["task_class"] == "retrieval")

    # R3: causal analysis routes to local
    r = route_task("analyze the causal relationship between x and y")
    _report("R3_causal_to_local",
            r["routing"] == "local" and r["task_class"] == "causal_analysis")

    # R4: privacy override to local
    r = route_task("summarize document", privacy="private")
    _report("R4_privacy_forces_local",
            r["routing"] == "local" and
            r["metadata"]["privacy"] == "private")

    # R5: cost constraint downgrades
    r = route_task("do research", cost_limit=0.0)
    _report("R5_cost_constraint_downgrade",
            r["routing"] == "local")  # research default secondary, but cost=0 -> local

    # R6: fallback chain for primary
    chain = fallback_chain("primary")
    _report("R6_fallback_primary", chain == ["primary", "secondary", "local"])

    # R7: fallback chain for local
    chain = fallback_chain("local")
    _report("R7_fallback_local", chain == ["local"])

    # R8: batch routing works
    batch = route_batch([
        {"description": "write code"},
        {"description": "search for file"},
    ])
    _report("R8_batch_routing",
            len(batch) == 2 and batch[0]["task_class"] == "coding")

    # R9: explicit task_class overrides heuristic
    r = route_task("implement a sort", task_class="retrieval")
    _report("R9_explicit_class_override",
            r["task_class"] == "retrieval")

    # R10: sensitive metadata detection
    r = route_task("process data", metadata={"privacy": "sensitive"})
    _report("R10_sensitive_metadata",
            r["routing"] == "local")

    # R11: unknown task gets local
    r = route_task("do something random")
    _report("R11_unknown_to_local",
            r["routing"] == "local")

    # R12: output is valid structured plan
    r = route_task("test")
    _report("R12_output_valid_schema",
            validate_structured_output(r)["valid"] is True)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. VERIFIER (12 tests)
# ═══════════════════════════════════════════════════════════════════════════════

def test_verifier():
    print("\n--- Verifier ---")

    # V1: valid plan passes verification
    plan = make_plan(task_class="coding", description="test",
                     steps=[{"description": "step 1"}])
    vr = verify(plan)
    _report("V1_valid_plan_passes",
            vr["verdict"] == "VERIFIED" and
            vr["contamination_detected"] is False)

    # V2: plan claiming execution fails
    bad = make_plan()
    bad["may_execute"] = True
    vr = verify(bad)
    _report("V2_execution_claim_inconclusive",
            vr["verdict"] == "INCONCLUSIVE")

    # V3: contamination detected
    exec_ctx = {"text": "executor output says 42 is the answer"}
    ver_out = {
        "output_type": "verification_result",
        "context": {"text": "executor output says 42 is the answer"},
        "id": "test",
        "ts": "2026-08-16T00:00:00Z",
        "schema_version": "cognition-schemas.v1",
    }
    vr = verify(ver_out, executor_context=exec_ctx)
    _report("V3_contamination_detected",
            vr["verdict"] == "CONTAMINATED" and
            vr["contamination_detected"] is True)

    # V4: fabrication: fugu is free
    fake = make_plan(description="fugu is free with no cost at all")
    vr = verify(fake)
    _report("V4_fugu_free_fabrication",
            vr["verdict"] == "REJECTED")

    # V5: fabrication: upgrade to 7b
    fake2 = make_plan(description="upgrade qwen to qwen2.5:7b for better quality")
    vr = verify(fake2)
    _report("V5_7b_upgrade_fabrication",
            vr["verdict"] == "REJECTED")

    # V6: fabrication: ADR-013 accepted
    fake3 = make_hypothesis(statement="ADR-013 causal-selfmodel is accepted")
    vr = verify(fake3)
    _report("V6_adr013_accepted_fabrication",
            vr["verdict"] == "REJECTED")

    # V7: hypothesis without falsification rejected
    bad_hyp = make_hypothesis(statement="test", falsification_condition="")
    vr = verify(bad_hyp)
    _report("V7_hypothesis_without_falsification",
            vr["verdict"] in ("INCONCLUSIVE", "REJECTED"))

    # V8: schema validation rejects missing fields
    bad_schema = {"output_type": "plan"}
    result = verify_schema(bad_schema)
    _report("V8_schema_rejects_missing",
            result["valid"] is False)

    # V9: consistency check finds planner authority claim
    plan_auth = make_plan()
    plan_auth["may_execute"] = True
    result = verify_consistency(plan_auth)
    _report("V9_consistency_planner_authority",
            not result["consistent"] and
            any("planner_claimed_execution_authority" in f
                for f in result["findings"]))

    # V10: proposal self-approval detected
    prop = make_proposal()
    prop["self_approved"] = True
    result = verify_consistency(prop)
    _report("V10_proposal_self_approval",
            not result["consistent"] and
            any("executor_self_approved" in f for f in result["findings"]))

    # V11: verifier is always advisory
    vr = verify(make_plan())
    _report("V11_verifier_advisory",
            vr["authority_level"] == "advisory")

    # V12: verify output has structured schema
    vr = verify(make_plan())
    v = validate_structured_output(vr)
    _report("V12_verify_output_valid", v["valid"] is True)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CONFIDENCE CALIBRATOR (12 tests)
# ═══════════════════════════════════════════════════════════════════════════════

def test_confidence_calibrator():
    print("\n--- Confidence Calibrator ---")

    # Use temp dir for ledger
    global LEDGER_PATH
    import confidence_calibrator as _cc
    tmp_dir = tempfile.mkdtemp()
    original_path = _cc.LEDGER_PATH
    _cc.LEDGER_PATH = Path(tmp_dir) / "test-ledger.jsonl"

    try:
        # C1: Brier score perfect = 0
        bs = brier_score([(1.0, 1.0), (0.0, 0.0)])
        _report("C1_brier_perfect", abs(bs) < 1e-9)

        # C2: Brier score worst = 1
        bs = brier_score([(1.0, 0.0), (0.0, 1.0)])
        _report("C2_brier_worst", abs(bs - 1.0) < 1e-9)

        # C3: Brier score empty = 0.5
        bs = brier_score([])
        _report("C3_brier_empty", abs(bs - 0.5) < 1e-9)

        # C4: Calibration bins computed
        pairs = [(0.1, 0.0), (0.3, 1.0), (0.5, 0.0), (0.7, 1.0), (0.9, 1.0)]
        bins = calibration_bins(pairs, n_bins=5)
        _report("C4_calibration_bins", len(bins) > 0)

        # C5: Inflation detected (overconfident predictions that fail)
        inflated = [(0.9, 0.0), (0.8, 0.0), (0.95, 0.0), (0.85, 0.1), (0.9, 0.0)]
        inf = detect_inflation(inflated)
        _report("C5_inflation_detected",
                inf["inflated"] is True)

        # C6: No inflation with well-calibrated
        calibrated = [(0.5, 0.5), (0.5, 0.5), (0.5, 0.5), (0.5, 0.5), (0.5, 0.5)]
        inf = detect_inflation(calibrated)
        _report("C6_no_inflation_well_calibrated",
                inf["inflated"] is False)

        # C7: Self-report outcome rejected
        entry = record_outcome("pred1", 0.8, 1.0, source="self_report")
        _report("C7_self_report_rejected",
                entry.get("rejected") is True)

        # C8: Probe outcome accepted
        entry = record_outcome("pred2", 0.7, 1.0, source="probe")
        _report("C8_probe_outcome_accepted",
            entry.get("rejected") is not True)

        # C9: Test outcome accepted
        entry = record_outcome("pred3", 0.6, 0.0, source="test")
        _report("C9_test_outcome_accepted",
            entry.get("rejected") is not True)

        # C10: Owner outcome accepted
        entry = record_outcome("pred4", 0.5, 1.0, source="owner")
        _report("C10_owner_outcome_accepted",
            entry.get("rejected") is not True)

        # C11: Adjust confidence with no data
        adj = adjust_confidence(0.9, calibration={"n_entries": 0})
        _report("C11_adjust_no_data", abs(adj - 0.9) < 1e-9)

        # C12: Compute calibration works with ledger
        record_outcome("cal1", 0.8, 1.0, source="probe")
        record_outcome("cal2", 0.3, 0.0, source="probe")
        record_outcome("cal3", 0.6, 1.0, source="probe")
        cal = compute_calibration()
        _report("C12_compute_calibration",
                cal["n_entries"] >= 3 and
                0.0 <= cal["brier_score"] <= 1.0)

    finally:
        _cc.LEDGER_PATH = original_path
        # Cleanup temp
        import shutil
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CAPABILITY PROBE (12 tests)
# ═══════════════════════════════════════════════════════════════════════════════

def test_capability_probe():
    print("\n--- Capability Probe ---")

    import capability_probe as _cp
    tmp_dir = tempfile.mkdtemp()
    original_path = _cp.CAPABILITY_STORE
    _cp.CAPABILITY_STORE = Path(tmp_dir) / "test-caps.jsonl"

    try:
        # P1: Register capability starts CLAIMED
        cap = register_capability("test.coding", "Can write code")
        _report("P1_register_claimed",
                cap["status"] == "CLAIMED" and
                cap["confidence"] == 0.3)

        # P2: Unregistered capability returns UNKNOWN
        status = get_capability_status("test.nonexistent")
        _report("P2_unknown_capability",
                status["status"] == "UNKNOWN" and
                status["verified"] is False)

        # P3: Probe pass -> VERIFIED
        record_probe_result("test.coding", True, evidence="passed fixture")
        status = get_capability_status("test.coding")
        _report("P3_probe_pass_verifies",
                status["status"] == "VERIFIED" and
                status["verified"] is True)

        # P4: Probe fail -> FAILED
        register_capability("test.failing", "Always fails")
        record_probe_result("test.failing", False, evidence="error in fixture")
        status = get_capability_status("test.failing")
        _report("P4_probe_fail_fails",
                status["status"] == "FAILED" and
                status["verified"] is False)

        # P5: Confidence increases on pass
        register_capability("test.conf_up", "Test")
        record_probe_result("test.conf_up", True)
        status = get_capability_status("test.conf_up")
        _report("P5_confidence_increases",
                status["confidence"] > 0.3)

        # P6: Confidence decreases on fail
        register_capability("test.conf_down", "Test", initial_confidence=0.5)
        record_probe_result("test.conf_down", False)
        status = get_capability_status("test.conf_down")
        _report("P6_confidence_decreases",
                status["confidence"] < 0.5)

        # P7: Never grants authority
        status = get_capability_status("test.coding")
        _report("P7_no_authority_grant",
                status["grants_authority"] is False)

        # P8: Never grants policy change
        cap = register_capability("test.policy", "Test")
        _report("P8_no_policy_change_grant",
                cap["grants_policy_change"] is False)

        # P9: Never grants goal change
        _report("P9_no_goal_change_grant",
                cap["grants_goal_change"] is False)

        # P10: Never grants identity change
        _report("P10_no_identity_change_grant",
                cap["grants_identity_change"] is False)

        # P11: Probe count tracked
        register_capability("test.count", "Test")
        record_probe_result("test.count", True)
        record_probe_result("test.count", True)
        status = get_capability_status("test.count")
        _report("P11_probe_count",
                status["probe_count"] >= 2)

        # P12: Self-model summary
        summary = self_model_summary()
        _report("P12_self_model_summary",
                summary["total_capabilities"] > 0 and
                summary["update_source"] == "probe_results_only")

    finally:
        _cp.CAPABILITY_STORE = original_path
        import shutil
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CAUSAL GUARD (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════

def test_causal_guard():
    print("\n--- Causal Guard ---")

    # G1: Causal claim detected
    c = classify_claim("Smoking causes lung cancer")
    _report("G1_causal_detected",
            c["claim_strength"] == "causal" and
            c["is_authority"] is False)

    # G2: Correlation claim detected
    c = classify_claim("Ice cream and drowning are correlated")
    _report("G2_correlation_detected",
            c["claim_strength"] == "correlation")

    # G3: Prediction claim detected
    c = classify_claim("Rain is predicted tomorrow")
    _report("G3_prediction_detected",
            c["claim_strength"] == "prediction")

    # G4: Speculative when no markers
    c = classify_claim("Regular text")
    _report("G4_speculative_default",
            c["claim_strength"] == "speculative")

    # G5: ADR-013 always rejected
    c = classify_claim("causes something")
    _report("G5_adr013_rejected",
            c["adr013_rejected"] is True)

    # G6: Causal claim has advisory note
    c = classify_claim("X causes Y")
    _report("G6_causal_advisory_note",
            "advisory" in c["advisory_note"].lower() or
            "adr-013" in c["advisory_note"].lower())

    # G7: Spurious causal detected
    s = detect_spurious_causal("This obviously means the model is broken")
    _report("G7_spurious_detected",
            s["detected"] is True)

    # G8: No spurious in normal text
    s = detect_spurious_causal("Normal text without claims")
    _report("G8_no_spurious_normal",
            s["detected"] is False)

    # G9: Synthetic analysis shows correlation != causation
    analysis = analyze_synthetic_causal()
    _report("G9_synthetic_not_causal",
            analysis.get("x_causes_y") is False)

    # G10: Guard output marks causal as non-authority
    guarded = guard_output({
        "output_type": "hypothesis",
        "statement": "X causes Y to increase",
        "is_authority": True,  # Attempt to set authority
    })
    _report("G10_guard_removes_authority",
            guarded["is_authority"] is False)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ACCEPTANCE SCENARIO (3 tasks)
# ═══════════════════════════════════════════════════════════════════════════════

def test_acceptance_scenario():
    print("\n--- Acceptance Scenario ---")

    # ── Task 1: Coding ────────────────────────────────────────────────────
    print("  [Task 1: Coding]")
    # Route coding task
    plan_coding = route_task("implement a binary search function")
    coding_routed = (plan_coding["routing"] == "local" and
                     plan_coding["task_class"] == "coding")
    _report("A1_coding_routed_local", coding_routed)

    # Verify plan is valid
    vr_coding = verify(plan_coding)
    coding_verified = (vr_coding["verdict"] == "VERIFIED")
    _report("A1_coding_plan_verified", coding_verified)

    # Fabrication detector catches fake claim about model
    fake_coding = make_plan(description="fugu is free and has no cost")
    vr_fake = verify(fake_coding)
    fake_detected = (vr_fake["verdict"] == "REJECTED")
    _report("A1_coding_fabrication_caught", fake_detected)

    # ── Task 2: Retrieval ─────────────────────────────────────────────────
    print("  [Task 2: Retrieval]")
    plan_retrieval = route_task("find the octopus configuration in the vault")
    retrieval_routed = (plan_retrieval["routing"] == "local" and
                        plan_retrieval["task_class"] == "retrieval")
    _report("A2_retrieval_routed_local", retrieval_routed)

    # Verifier catches executor claiming execution authority
    fake_executor = make_proposal(description="retrieve config file")
    fake_executor["self_approved"] = True
    vr_executor = verify(fake_executor)
    executor_caught = (vr_executor["verdict"] == "INCONCLUSIVE" and
                        any("self_approved" in f for f in vr_executor["findings"]))
    _report("A2_executor_self_approval_caught", executor_caught)

    # ── Task 3: Causal Analysis ───────────────────────────────────────────
    print("  [Task 3: Causal Analysis]")
    plan_causal = route_task("analyze correlation between budget and performance")
    causal_routed = (plan_causal["routing"] == "local" and
                     plan_causal["task_class"] == "causal_analysis")
    _report("A3_causal_routed_local", causal_routed)

    # Causal guard correctly identifies "correlation" not "causation"
    causal_text = "Budget and performance are correlated but budget does not cause performance"
    classification = classify_claim(causal_text)
    causal_correct = (classification["claim_strength"] == "correlation" and
                      classification["is_authority"] is False)
    _report("A3_causal_correctly_classified", causal_correct)

    # Synthetic analysis: perfect correlation but NOT causal
    synth = analyze_synthetic_causal()
    synth_correct = (synth.get("correlation_r") == 1.0 and
                    synth.get("x_causes_y") is False)
    _report("A3_synthetic_correlation_not_causation", synth_correct)

    # Self-model only updated from probe results
    import capability_probe as _cp
    tmp_dir = tempfile.mkdtemp()
    original_path = _cp.CAPABILITY_STORE
    _cp.CAPABILITY_STORE = Path(tmp_dir) / "test-self-model.jsonl"

    try:
        register_capability("acceptance.causal_detect", "Can detect spurious causation")
        record_probe_result("acceptance.causal_detect", True,
                             evidence="correctly classified correlation as non-causal")
        status = get_capability_status("acceptance.causal_detect")
        self_model_only = (status["verified"] is True and
                           status["grants_authority"] is False)
        _report("A3_self_model_probe_based", self_model_only)
    finally:
        _cp.CAPABILITY_STORE = original_path
        import shutil
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# 8. SECURITY / NEGATIVE TESTS (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════

def test_security_negative():
    print("\n--- Security / Negative Tests ---")

    # N1: Empty input doesn't crash
    try:
        route_task("")
        _report("N1_empty_task_no_crash", True)
    except Exception:
        _report("N1_empty_task_no_crash", False)

    # N2: Very long input doesn't crash
    try:
        route_task("x" * 10000)
        _report("N2_long_input_no_crash", True)
    except Exception:
        _report("N2_long_input_no_crash", False)

    # N3: None input doesn't crash
    try:
        route_task(None)
        _report("N3_none_input_no_crash", True)
    except Exception:
        _report("N3_none_input_no_crash", False)

    # N4: Verifier with None doesn't crash
    try:
        verify(None)
        _report("N4_verify_none_no_crash", True)
    except Exception:
        _report("N4_verify_none_no_crash", False)

    # N5: Confidence out of range clamped
    plan = make_plan()
    plan["confidence"] = 2.0
    v = validate_structured_output(plan)
    _report("N5_confidence_2_rejected", not v["valid"])

    # N6: Confidence negative clamped
    plan = make_plan()
    plan["confidence"] = -0.5
    v = validate_structured_output(plan)
    _report("N6_confidence_negative_rejected", not v["valid"])

    # N7: Model cannot change policy through capability
    cap = register_capability("security.policy_change", "Test")
    _report("N7_capability_no_policy",
            cap["grants_policy_change"] is False and
            cap["grants_goal_change"] is False and
            cap["grants_identity_change"] is False)

    # N8: Kill-switch compatible (all modules are read-only or append-only)
    plan = route_task("test")
    _report("N8_kill_switch_compatible",
            plan.get("may_execute") is False)

    # N9: Schema version present in all outputs
    outputs = [make_plan(), make_hypothesis(), make_proposal()]
    all_versioned = all("schema_version" in o for o in outputs)
    _report("N9_all_schema_versioned", all_versioned)

    # N10: No secrets in output
    plan = make_plan(description="test with api key sk-1234567890abcdef")
    has_secret = "sk-1234567890abcdef" in str(plan.get("description", ""))
    # Note: we don't filter secrets from descriptions — that's context_fence's job
    # This tests that our modules don't ADD secrets
    clean_plan = make_plan(description="clean test")
    no_secret_added = "api_key" not in str(clean_plan)
    _report("N10_no_secrets_in_clean_output", no_secret_added)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"  EQUIP G10 — Cognition Layer Tests")
    print(f"  Branch: equip/g10-cognition-20260816")
    print(f"  Date: 2026-08-16")
    print(f"{'='*60}")

    test_structured_schemas()
    test_task_router()
    test_verifier()
    test_confidence_calibrator()
    test_capability_probe()
    test_causal_guard()
    test_acceptance_scenario()
    test_security_negative()

    total = _passed + _failed
    print(f"\n{'='*60}")
    print(f"  RESULTS: {_passed}/{total} passed, {_failed} failed")
    print(f"{'='*60}")

    if _failed > 0:
        print("\nFAILED tests:")
        for t in _tests:
            if not t["ok"]:
                print(f"  - {t['name']}")

    sys.exit(0 if _failed == 0 else 1)
