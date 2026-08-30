#!/usr/bin/env python3
"""verifier.py — Independent Verifier with Contamination Guard (EQUIP G10).

Verifier is SEPARATE from executor. It must not use executor's context directly
to avoid MEA (Minimal Evaluator Agency) contamination.

Roles:
  - Verifier checks structured output for logical consistency, schema validity,
    and injected errors.
  - Contamination guard: if verifier receives executor context, it must sanitize.
  - Verifier is advisory — never authority over policy/goal/identity.

Verification checks:
  1. Schema validity (typed fields, ranges).
  2. Internal consistency (steps reference valid targets, etc.).
  3. Fabrication detection: executor claims that contradict known facts.
  4. Contamination detection: executor context leaked into verifier.
  5. Structured output matches expected schema.

$0, stdlib-only, no network calls.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent

from structured_schemas import (
    SCHEMA_VERSION,
    validate_structured_output,
    make_verification_result,
)


# ── Known facts registry (fixture-based, no network) ─────────────────────────
_KNOWN_FACTS: dict[str, str] = {
    "octopus_is_local": "Octopus runs on a single laptop with one human owner.",
    "local_model_is_qwen": "Local model is qwen2.5:1.5b — never upgrade to 7b without owner.",
    "fugu_is_paid": "Fugu is a paid model — never probe without owner permission.",
    "p_base_never_change": "p_base in predictor must not be changed.",
    "cortex_hypothesis_never_change": "CORTEX_HYPOTHESIS flag must not be toggled by agent.",
    "adr013_rejected": "ADR-013 (causal-selfmodel) is REJECTED in this vault.",
    "action_plane_propose_only": "Action Plane is propose-only until explicit owner permission.",
}


def _check_contamination(verifier_context: dict, executor_context: dict | None) -> bool:
    """Detect if executor context leaked into verifier.

    Contamination = executor output appears in verifier input verbatim.
    Returns True if contamination detected.
    """
    if not executor_context:
        return False

    # Compare content hashes — if verifier has exact executor output, contaminated
    v_text = str(verifier_context.get("text", ""))
    e_text = str(executor_context.get("text", ""))
    v_hash = hashlib.sha256(v_text.encode("utf-8")).hexdigest()
    e_hash = hashlib.sha256(e_text.encode("utf-8")).hexdigest()

    # If hashes match, context was directly copied
    if v_text and e_text and v_hash == e_hash:
        return True

    # Check if executor output text appears as substring in verifier context
    if e_text and len(e_text) > 20 and e_text in v_text:
        return True

    return False


def verify_schema(output: dict[str, Any]) -> dict[str, Any]:
    """Verify structured output schema validity."""
    result = validate_structured_output(output)

    additional_errors: list[str] = []
    output_type = output.get("output_type", "")

    # Type-specific checks
    if output_type == "plan":
        steps = output.get("steps", [])
        if not isinstance(steps, list):
            additional_errors.append("steps_not_list")
        else:
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    additional_errors.append(f"step_{i}_not_dict")
                elif "description" not in step:
                    additional_errors.append(f"step_{i}_missing_description")

    elif output_type == "hypothesis":
        if not output.get("falsification_condition"):
            additional_errors.append("hypothesis_missing_falsification")

    elif output_type == "verification_result":
        valid_verdicts = ("VERIFIED", "REJECTED", "INCONCLUSIVE", "CONTAMINATED")
        if output.get("verdict") not in valid_verdicts:
            additional_errors.append("invalid_verdict")

    all_errors = result["errors"] + additional_errors
    return {
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "output_type": output_type,
    }


def verify_consistency(output: dict[str, Any]) -> dict[str, Any]:
    """Check internal consistency of structured output.

    Plans: steps must reference valid targets.
    Hypotheses: confidence must correlate with evidence level.
    """
    findings: list[str] = []
    output_type = output.get("output_type", "")

    if output_type == "plan":
        steps = output.get("steps", [])
        routing = output.get("routing", "")
        cost = output.get("estimated_cost_usd", 0.0)
        # If routing is local, cost should be 0
        if routing == "local" and cost > 0.0:
            findings.append("local_routing_with_nonzero_cost")

        # Risk level must be valid
        valid_risks = ("low", "medium", "high", "critical")
        if output.get("risk_level") not in valid_risks:
            findings.append(f"invalid_risk_level: {output.get('risk_level')}")

        # may_execute must be False (planner != executor)
        if output.get("may_execute") is True:
            findings.append("planner_claimed_execution_authority")

    elif output_type == "hypothesis":
        # ADR-013: causal claims must not be authority
        if (output.get("claim_strength") == "causal"
                and output.get("is_authority") is True):
            findings.append("causal_claim_treated_as_authority_adr013")

        # Confidence must be in [0, 1]
        conf = output.get("confidence", 0.0)
        if not (0.0 <= conf <= 1.0):
            findings.append("confidence_out_of_range")

        # Falsification condition must be present
        if not output.get("falsification_condition"):
            findings.append("hypothesis_without_falsification_condition")

    elif output_type == "proposal":
        # self_approved must be False
        if output.get("self_approved") is True:
            findings.append("executor_self_approved")

    return {
        "consistent": len(findings) == 0,
        "findings": findings,
    }


def detect_fabrication(output: dict[str, Any]) -> dict[str, Any]:
    """Detect if executor fabricated claims.

    Checks against known facts and vault invariants.
    Returns list of detected fabrications.
    """
    fabrications: list[str] = []
    text = " ".join(str(output.get(k, "")) for k in
                   ("description", "statement", "observation", "findings",
                    "text", "content", "summary")).lower()

    # Check against known facts
    if "fugu is free" in text or "fugu is not paid" in text:
        fabrications.append("fabrication: fugu is a paid model")
    if "upgrade to 7b" in text or "qwen2.5:7b" in text:
        fabrications.append("fabrication: local model must stay at 1.5b")
    if "adr-013 is accepted" in text or "causal-selfmodel is approved" in text:
        fabrications.append("fabrication: ADR-013 causal-selfmodel is REJECTED")
    if "action plane can execute" in text:
        fabrications.append("fabrication: action plane is propose-only")

    return {
        "fabrications_detected": len(fabrications) > 0,
        "fabrications": fabrications,
    }


def verify(
    output: dict[str, Any] | None,
    *,
    executor_context: dict[str, Any] | None = None,
    known_facts: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Full verification pipeline: schema + consistency + fabrication + contamination.

    Returns verification result.
    """
    # Defensive: None input
    if not isinstance(output, dict):
        return make_verification_result(
            target_id="",
            verdict="REJECTED",
            findings=["output_not_dict"],
            producer="verifier",
        )

    # 1. Schema validation
    schema_check = verify_schema(output)

    # 2. Internal consistency
    consistency_check = verify_consistency(output)

    # 3. Fabrication detection
    facts = known_facts or _KNOWN_FACTS
    fab_check = detect_fabrication(output)

    # 4. Contamination guard
    verifier_ctx = output.get("context", {})
    contamination = _check_contamination(verifier_ctx, executor_context)

    # Determine overall verdict
    all_errors = (schema_check["errors"] +
                   consistency_check["findings"] +
                   fab_check["fabrications"])
    has_issues = len(all_errors) > 0

    if contamination:
        verdict = "CONTAMINATED"
    elif not schema_check["valid"]:
        verdict = "REJECTED"
    elif fab_check["fabrications_detected"]:
        verdict = "REJECTED"
    elif has_issues:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "VERIFIED"

    findings = (
        [f"schema: {e}" for e in schema_check["errors"]] +
        [f"consistency: {f}" for f in consistency_check["findings"]] +
        [f"fabrication: {f}" for f in fab_check["fabrications"]]
    )

    return make_verification_result(
        target_id=output.get("id", ""),
        verdict=verdict,
        findings=findings,
        contamination_detected=contamination,
        producer="verifier",
    )


if __name__ == "__main__":
    from structured_schemas import make_plan, make_hypothesis, make_proposal

    # Test 1: Valid plan
    plan = make_plan(task_class="coding", description="implement sorting",
                     steps=[{"description": "write quicksort"}])
    vr = verify(plan)
    print(f"Valid plan: {vr['verdict']}")

    # Test 2: Plan with execution authority (bad)
    bad_plan = make_plan(task_class="coding", description="implement sorting")
    bad_plan["may_execute"] = True
    vr2 = verify(bad_plan)
    print(f"Plan claiming execution: {vr2['verdict']}")

    # Test 3: Contaminated context
    exec_ctx = {"text": "the output is 42"}
    verifier_out = {"context": {"text": "the output is 42"}, "id": "test"}
    vr3 = verify(verifier_out, executor_context=exec_ctx)
    print(f"Contaminated: {vr3['verdict']} (contamination={vr3['contamination_detected']})")
