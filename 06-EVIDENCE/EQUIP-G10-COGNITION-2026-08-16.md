# EQUIP G10 — Cognitive and Self-Model Layer — Evidence Report

**Date:** 2026-08-16
**Wave:** E2 (Group 10 — last implementation group)
**Branch:** `equip/g10-cognition-20260816`
**Base:** `d997f32` (G9 PASS, 176/176)
**Implementer:** 10 (Wave E2)
**Verdict:** PASS

---

## Executive Verdict: PASS

A governed cognitive and self-model layer was implemented with 6 new modules
in `_ops/cognition/`. All 95/95 tests pass with 0 failures, 0 new dependencies,
0 regressions on dependent groups. The implementation enforces:
planner != executor != verifier separation, probe-based self-model updates only,
ADR-013 REJECTED (causal claims are never authority), confidence calibration
with outcome ledger, and fabrication/contamination detection in the verifier.

---

## Discovered Architecture (Pre-G10)

### Existing Cognition Components

| Component | Location | Status | Role |
|-----------|----------|--------|------|
| **model_router.py** | `_ops/cortex/model_router.py` | Live | 3-tier LLM routing (local/secondary/primary) with fallback, quality gates, circuit breaker |
| **route_scorer.py** | `_ops/cortex/route_scorer.py` | Live | 6-signal scoring (complexity/risk/privacy/impact/cost/urgency) -- advisory |
| **provider_adapter.py** | `_ops/cortex/provider_adapter.py` | Live | D5/D6 provider orchestration with ProviderResponse and fallback chain |
| **self_model.py** | `_ops/cortex/self_model.py` | Live | AST-based self-model builder with self-claims |
| **cognitive/** | `_ops/cognitive/` | Live | truth_layer, context_engine, event_stream, run_store, memory_formation |
| **hypothesis_engine/** | `_ops/hypothesis_engine/impl/` | Live | Bayesian hypothesis brain (Pydantic) with evidence grades A-E |
| **memory/gate.py** | `_ops/memory/gate.py` | Live | Graded MemoryGate with trust classification |
| **memory/write_gate_enforcer.py** | `_ops/memory/write_gate_enforcer.py` | Live | Write enforcement bridge |
| **heart/sog_math.py** | `_ops/heart/sog_math.py` | Live | SOG math diagnostics |
| **heart/kalman_shadow_pipeline.py** | `_ops/heart/kalman_shadow_pipeline.py` | Live | Kalman shadow pipeline |

### Identified Gaps (Filled by G10)

1. **No unified task routing policy** -- `route_scorer.py` scores but has no task-class dimension. `model_router.py` has TASK_TIERS but no privacy/cost/risk integration in typed schema.
2. **No formal verifier** -- `truth_layer.py` verifies file existence only; no fabrication detection, no contamination guard (MEA).
3. **No confidence calibration** -- self-claims exist but no outcome feedback loop. Hypothesis engine has Bayesian update but no real outcome ledger.
4. **No structured output schemas** -- No shared schemas for plan/hypothesis/evidence/proposal that all components agree on.
5. **No probe-based self-model** -- `self_model.py` updates from AST only; no probe-result-driven capability claims.
6. **No causal/correlation guard** -- No explicit separation of causal claims from correlations (ADR-013 REJECTED).

---

## Implemented Capabilities

### Module 1: `structured_schemas.py` -- Typed Output Schemas
- `make_plan()`, `make_hypothesis()`, `make_evidence()`, `make_proposal()`, `make_verification_result()`
- All outputs have: schema_version, id, ts, producer, trace_id
- Planner: `may_execute=False` (planner != executor)
- Proposal: `self_approved=False` (executor != authorizer)
- Verification: `authority_level="advisory"` (verifier is advisory only)
- Hypothesis: `is_authority=False` (hypothesis never governs policy)
- `validate_structured_output()` -- validates required fields, confidence range, evidence grade

### Module 2: `task_router.py` -- Unified Task Routing Policy
- Task classification: coding, retrieval, causal_analysis, classification, summarization, research, orchestration, planning
- Privacy detection: PUBLIC, INTERNAL, SENSITIVE, PRIVATE -- sensitive always routes to local
- Cost constraint: budget-limited routing (cost_limit downgrades tier)
- Latency budget per task class
- `route_task()`, `route_batch()`, `fallback_chain()`
- Delegates to existing `model_router.ask()` for actual LLM calls (no duplication)
- $0, stdlib-only, no network calls

### Module 3: `verifier.py` -- Independent Verifier with Contamination Guard
- **MEA contamination guard**: verifier detects if executor context leaked verbatim
- **Schema validation**: type checks, range checks, type-specific rules
- **Consistency check**: planner claiming execution authority, executor self-approving, hypothesis without falsification
- **Fabrication detection**: checks against vault invariants (fugu is paid, local model stays 1.5b, ADR-013 REJECTED, action plane is propose-only)
- 4-stage pipeline: schema -> consistency -> fabrication -> contamination
- Verdicts: VERIFIED, REJECTED, INCONCLUSIVE, CONTAMINATED

### Module 4: `confidence_calibrator.py` -- Confidence Calibration with Outcome Ledger
- Brier score computation
- Calibration bins for reliability diagram
- Confidence inflation detection (systematic over-estimation)
- Outcome ledger: append-only JSONL, sources: probe/test/owner (self-report REJECTED)
- `adjust_confidence()`: scales down if model is overconfident
- $0, stdlib-only

### Module 5: `capability_probe.py` -- Probe-Based Self-Model Updater
- Capability states: CLAIMED -> PROBING -> VERIFIED | FAILED | STALE
- `register_capability()`: initial state CLAIMED, confidence 0.3
- `record_probe_result()`: pass -> VERIFIED (confidence up), fail -> FAILED (confidence down)
- **Invariant**: `grants_authority=False`, `grants_policy_change=False`, `grants_goal_change=False`, `grants_identity_change=False`
- `self_model_summary()`: only verified capabilities contribute
- **No capability claim can grant policy/goal/identity authority**

### Module 6: `causal_guard.py` -- Causal Claim Guard
- Claim classification: causal, correlation, prediction, speculative
- **ADR-013 REJECTED**: causal claims are NEVER authority
- Spurious causal reasoning detection (patterns like "this obviously means", "this clearly proves")
- `guard_output()`: marks causal claims as non-authoritative
- Synthetic acceptance fixture: perfect correlation (r=1.0) but NOT causal, demonstrating correlation != causation

---

## Changed Files

| File | Lines | Description |
|------|-------|-------------|
| `_ops/cognition/structured_schemas.py` | 263 | Typed schemas for all cognition outputs |
| `_ops/cognition/task_router.py` | 242 | Unified task routing with privacy/cost/risk |
| `_ops/cognition/verifier.py` | 278 | Independent verifier with MEA contamination guard |
| `_ops/cognition/confidence_calibrator.py` | 234 | Brier score, inflation detection, outcome ledger |
| `_ops/cognition/capability_probe.py` | 260 | Probe-based self-model with authority invariant |
| `_ops/cognition/causal_guard.py` | 244 | Causal claim guard, ADR-013 enforcement |
| `_ops/cognition/tests/__init__.py` | 1 | Test package marker |
| `_ops/cognition/tests/test_g10_cognition.py` | 785 | Comprehensive test suite (95 tests) |

**Total:** 2307 lines added, 0 modified, 0 deleted, 8 files created

---

## Dependencies

**New dependencies: 0.** All modules use stdlib only (json, re, os, sys, time, pathlib, uuid, hashlib, enum, tempfile, shutil).

---

## Tests + Exact Results

### G10 Tests: 95/95 PASS

```
--- Structured Schemas (16 tests) ---
  ok S1_make_plan_valid
  ok S2_hypothesis_has_falsification
  ok S3_evidence_has_grade
  ok S4_proposal_not_self_approved
  ok S5_verification_advisory
  ok S6_validate_accepts_valid
  ok S7_validate_rejects_invalid
  ok S8_confidence_out_of_range
  ok S9_invalid_evidence_grade
  ok S10_schema_version_plan
  ok S10_schema_version_hypothesis
  ok S10_schema_version_evidence
  ok S10_schema_version_proposal
  ok S10_schema_version_verification_result
  ok S11_unique_ids
  ok S12_unique_traces
  ok S13_causal_claim_preserved
  ok S14_planner_no_execute_authority

--- Task Router (12 tests) ---
  ok R1_coding_to_local
  ok R2_retrieval_to_local
  ok R3_causal_to_local
  ok R4_privacy_forces_local
  ok R5_cost_constraint_downgrade
  ok R6_fallback_primary
  ok R7_fallback_local
  ok R8_batch_routing
  ok R9_explicit_class_override
  ok R10_sensitive_metadata
  ok R11_unknown_to_local
  ok R12_output_valid_schema

--- Verifier (12 tests) ---
  ok V1_valid_plan_passes
  ok V2_execution_claim_inconclusive
  ok V3_contamination_detected
  ok V4_fugu_free_fabrication
  ok V5_7b_upgrade_fabrication
  ok V6_adr013_accepted_fabrication
  ok V7_hypothesis_without_falsification
  ok V8_schema_rejects_missing
  ok V9_consistency_planner_authority
  ok V10_proposal_self_approval
  ok V11_verifier_advisory
  ok V12_verify_output_valid

--- Confidence Calibrator (12 tests) ---
  ok C1_brier_perfect
  ok C2_brier_worst
  ok C3_brier_empty
  ok C4_calibration_bins
  ok C5_inflation_detected
  ok C6_no_inflation_well_calibrated
  ok C7_self_report_rejected
  ok C8_probe_outcome_accepted
  ok C9_test_outcome_accepted
  ok C10_owner_outcome_accepted
  ok C11_adjust_no_data
  ok C12_compute_calibration

--- Capability Probe (12 tests) ---
  ok P1_register_claimed
  ok P2_unknown_capability
  ok P3_probe_pass_verifies
  ok P4_probe_fail_fails
  ok P5_confidence_increases
  ok P6_confidence_decreases
  ok P7_no_authority_grant
  ok P8_no_policy_change_grant
  ok P9_no_goal_change_grant
  ok P10_no_identity_change_grant
  ok P11_probe_count
  ok P12_self_model_summary

--- Causal Guard (10 tests) ---
  ok G1_causal_detected
  ok G2_correlation_detected
  ok G3_prediction_detected
  ok G4_speculative_default
  ok G5_adr013_rejected
  ok G6_causal_advisory_note
  ok G7_spurious_detected
  ok G8_no_spurious_normal
  ok G9_synthetic_not_causation
  ok G10_guard_removes_authority

--- Acceptance Scenario (9 tests) ---
  ok A1_coding_routed_local
  ok A1_coding_plan_verified
  ok A1_coding_fabrication_caught
  ok A2_retrieval_routed_local
  ok A2_executor_self_approval_caught
  ok A3_causal_routed_local
  ok A3_causal_correctly_classified
  ok A3_synthetic_correlation_not_causation
  ok A3_self_model_probe_based

--- Security / Negative Tests (10 tests) ---
  ok N1_empty_task_no_crash
  ok N2_long_input_no_crash
  ok N3_none_input_no_crash
  ok N4_verify_none_no_crash
  ok N5_confidence_2_rejected
  ok N6_confidence_negative_rejected
  ok N7_capability_no_policy
  ok N8_kill_switch_compatible
  ok N9_all_schema_versioned
  ok N10_no_secrets_in_clean_output

RESULTS: 95/95 passed, 0 failed
```

### Regression Tests: All Pass

| Group | Tests | Result |
|-------|-------|--------|
| Heart Cognition | 7/7 | PASS |
| Heart Cognition Wiring | 5/5 | PASS |
| SOG Floor Guards | 5/5 | PASS |
| SOG Provenance | 16/16 | PASS |
| Kalman Shadow Pipeline | 3/3 | PASS |

---

## Scan Findings by Severity

### Security Scan

| Severity | Finding | Status |
|----------|---------|--------|
| INFO | Test fixture uses fake API key `sk-1234567890abcdef` in N10 test | Not a real secret -- clearly a test fixture with comment explaining it |
| NONE | No network calls in production code | Clean |
| NONE | No sensitive file writes | Clean |
| NONE | No unsafe deserialization (pickle/shelve/marshal) | Clean |
| NONE | No path traversal vectors | Clean |
| NONE | No eval/exec/subprocess in production code | Clean |
| NONE | No authority leakage -- all modules enforce `is_authority=False` | Clean |

### G10 Specialized Scan

| Check | Result |
|-------|--------|
| Model-routing loop | No loop -- router delegates to model_router.ask(), no recursive call |
| Unverifiable self-claims | capability_probe requires probe pass for VERIFIED |
| Confidence inflation | detect_inflation() catches systematic over-estimation |
| Evaluator contamination | verifier.py contamination guard detects verbatim context leak |
| Reward hacking | No reward signal in any module |
| Authority leakage from diagnostics | All diagnostic outputs marked `authority_level="advisory"` |
| Goal drift | No module can set/change goals -- grants_goal_change=False |
| Unsafe fallback | fallback_chain() is explicit, ordered, observable |
| Malformed structured output | validate_structured_output() catches missing/invalid fields |
| Hidden activation of disabled components | No activation flag manipulation in any module |

---

## Invariants Verified

1. CORTEX_HYPOTHESIS: Not changed, not referenced.
2. p_base: Not changed, not referenced.
3. SOG/Kalman: Diagnostic only, untouched.
4. ADR-013 (causal-selfmodel): REJECTED -- causal_guard.py enforces `is_authority=False` on all causal claims.
5. Planner != Executor != Verifier: Separation enforced in structured schemas.
6. Self-model updates from probe results only: capability_probe.py rejects self-report.
7. Model cannot change policy/goal/identity: All modules enforce grants_policy_change=False.
8. No paid model probed: All acceptance scenarios use fixtures/local models.
9. Fugu not probed: No Fugu API calls in any module.

---

## Unresolved Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| route_scorer.py context-rich signals unused (ctx=None in live path) | LOW | Existing behavior preserved; G10 does not change model_router |
| Confidence calibrator ledger in state dir (disk I/O on every record) | LOW | Fail-soft; ledger corruption = empty ledger |
| Causal guard regex-based (not NLP) | LOW | Sufficient for current vault text patterns; can upgrade later |
| No real-world calibration data yet | LOW | Infrastructure ready; needs probes + owner outcomes |

---

## Rollback Plan

1. `git checkout equip/g9-connectors-20260816 -- _ops/cognition/` (removes G10 files)
2. Or: delete the 8 files listed in "Changed Files" above
3. No migrations, no database changes, no dependency changes to revert
4. Zero impact on existing modules -- all new files are additive

---

## Reproduce Commands

```bash
cd F:\backup
git checkout equip/g10-cognition-20260816

# Run G10 tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/cognition/tests/test_g10_cognition.py

# Run regression tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_heart_cognition.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_heart_cognition_wiring.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_sog_floor_guards.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_sog_provenance.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_kalman_shadow_pipeline.py

# Security scan
PYTHONIOENCODING=utf-8 python -X utf8 -c "..." # See Phase 5 scan script
```

---

## Evidence Paths

- Test file: `_ops/cognition/tests/test_g10_cognition.py`
- Evidence report: `06-EVIDENCE/EQUIP-G10-COGNITION-2026-08-16.md`
- Branch: `equip/g10-cognition-20260816`
- Commit: `c576861`

---

## Recommended Next Step

Wave E FINAL: independent scan by separate agent using `MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md`.
All 10 implementation groups complete. Chain ready for final scan.
