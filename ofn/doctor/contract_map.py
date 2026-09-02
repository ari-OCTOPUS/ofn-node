#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_map — LAB-DOCTOR-CONTRACT.yaml → executable behaviour + tests.

Owner directive (Lane B, 2026-09-02): turn the contract into tested code.
Every in-scope contract requirement is mapped here to a code symbol, a test
symbol, its input/output, its failure mode, and where its receipt lands.
Out-of-scope requirements are not silently dropped: the hard-sandbox family
(lane C) is guarded in THIS lane by an unconditional refusal to execute
untrusted mutation code, per the contract's own safety_rule.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .miniyaml import load_file

__all__ = [
    "CONTRACT_SOURCE", "CONTRACT_SOURCE_SHA256", "REQUIREMENTS",
    "RFC_STATES", "SELF_JUDGMENT_BANS", "SandboxNotVerifiedError",
    "execute_mutation", "validate_experiment", "load_contract",
    "extract_gaps", "requirement_stats",
]

CONTRACT_SOURCE = "F:\\backup\\LAB-DOCTOR-CONTRACT.yaml"
CONTRACT_SOURCE_SHA256 = "4b9e1ad325fbba907dd5de43cc060dc39a8d9627cc1de0dc3886b00b5591b9e4"
_CONTRACT_FILE = Path(__file__).with_name("contract") / "LAB-DOCTOR-CONTRACT.yaml"

# doctor.rfc_lifecycle_observed.states — kept verbatim; terminal destiny in destiny.py
RFC_STATES = (
    "draft", "drafted", "sandboxed", "sandbox-skip", "submitted",
    "submitted-no-channel", "submit-failed", "merged", "rejected", "expired",
)

# doctor.self_judgment.forbidden — enforced by assert_no_self_promotion-style tests
SELF_JUDGMENT_BANS = (
    "final judgment of its own RFC",
    "self-issued positive credit",
    "self-promotion to VERIFIED",
    "changing a metric after seeing the result",
)

STATUS_IMPLEMENTED = "IMPLEMENTED"
STATUS_DELEGATED = "DELEGATED_LANE_C"      # guard implemented here; build is lane C
STATUS_BACKLOG = "BACKLOG_ITEM"            # gap registered in the self-backlog


@dataclass(frozen=True)
class Requirement:
    req_id: str
    contract_path: str
    requirement: str
    code_symbol: str
    test_symbol: str
    input: str
    output: str
    failure_mode: str
    receipt: str
    status: str


REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        "R-01", "principle.statement",
        "Organs diagnose and propose; they do not patch or promote themselves.",
        "ofn.doctor.destiny.DestinyEngine.decide",
        "tests.test_doctor_lane_destiny::test_08_sensitive_proposal_escalates_to_owner",
        "proposal whose target is deny-listed or sensitive",
        "Decision(outcome=ESCALATED_TO_OWNER, incident recorded)",
        "allowing a self-patching target through as PR_CREATED",
        "09-LANES/LB/runs/<date>/receipt.jsonl",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-02", "doctor.diagnosis_observed",
        "Offline diagnosis over the vault state with severity-tagged evidence.",
        "ofn.doctor.round.DoctorRound.run",
        "tests.test_doctor_lane_round::test_01_healthy_vault_yields_no_source_findings",
        "vault root path (read-only)",
        "findings.json + integrity manifests + receipt",
        "crash on malformed/missing source instead of a classified finding",
        "09-LANES/LB/runs/<date>/receipt.jsonl",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-03", "doctor.prescription_required.output_shape",
        "Falsifiable prescription with mutation zone, cost, rollback, evidence refs.",
        "ofn.doctor.prescription.validate_prescription",
        "tests.test_doctor_lane_contract_map::test_prescription_shape",
        "prescription mapping",
        "[] when valid; named violations otherwise",
        "accepting a prescription without falsification or rollback",
        "09-LANES/LB/runs/<date>/receipt.jsonl",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-04", "doctor.rfc_lifecycle_observed.states",
        "Proposal lifecycle states; every proposal reaches a terminal destiny.",
        "ofn.doctor.destiny.DestinyEngine.assign/recover",
        "tests.test_doctor_lane_destiny::test_14_crash_mid_proposal_leaves_no_pending",
        "proposal + journal",
        "terminal outcome among the four owner-mandated ones",
        "a proposal left PENDING/orphaned after a crash",
        "journal.jsonl (append-only, per-line sha256)",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-05", "doctor.patch_boundary.scheduled_runs",
        "Scheduled runs are propose_only; the round API has no write path at all.",
        "ofn.doctor.round (module has no mutating function)",
        "tests.test_doctor_lane_round::test_09_10_round_never_touches_source_tree",
        "synthetic vault + full tree hash before/after",
        "changed_sources == [] and tree hash identical",
        "any source file changing during a round",
        "receipt.jsonl integrity manifests (before==after)",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-06", "doctor.patch_boundary.direct_code_merge",
        "Direct code merge forbidden; machine PRs only for reversible lane-owned changes, merge stays human.",
        "ofn.doctor.destiny.DestinyEngine.decide (rule order)",
        "tests.test_doctor_lane_destiny::test_merge_is_never_an_outcome",
        "any proposal",
        "PR_CREATED at most; merging never decided by the engine",
        "engine emitting an auto-merge outcome",
        "PR URL recorded in proposal-outcomes.json",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-07", "doctor.self_judgment.forbidden",
        "No self-final-judgment, no self-promotion to VERIFIED, no post-hoc metric change.",
        "ofn.doctor.contract_map.SELF_JUDGMENT_BANS + tests asserting grades stay E-graded by measurement",
        "tests.test_doctor_lane_contract_map::test_self_promotion_bans_are_enforced",
        "any evidence-grade claim produced by this lane",
        "grades only as measured; promotion attempts raise",
        "self-reported positive grade without a test run",
        "LANE-REPORT.md evidence section",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-08", "experiment_contract.required_before_execution",
        "Experiment must carry the full pre-registration before any execution.",
        "ofn.doctor.contract_map.validate_experiment",
        "tests.test_doctor_lane_contract_map::test_validate_experiment",
        "experiment mapping",
        "[] when fully pre-registered; named violations otherwise",
        "executing an experiment without falsifier/judge/rollback",
        "future experiment receipts (none executed in this lane)",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-09", "experiment_contract.constitutional_validation",
        "budget positive, timeout positive, rollback nonempty, external effects forbidden.",
        "ofn.doctor.contract_map.validate_experiment",
        "tests.test_doctor_lane_contract_map::test_validate_experiment",
        "experiment mapping",
        "violations list including budget/timeout/rollback/external-effects",
        "zero budget or nonzero external_effects passing validation",
        "future experiment receipts",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-10", "lab.hard_sandbox_requirements",
        "Hard sandbox (workspace-only mount, non-root, closed network, cpu/ram/pid limits, OS isolation).",
        "ofn.doctor.contract_map.execute_mutation (unconditional refusal)",
        "tests.test_doctor_lane_contract_map::test_untrusted_execution_is_refused",
        "any request to execute mutation code",
        "SandboxNotVerifiedError citing contract verdict NOT_A_VERIFIED_HARD_SANDBOX",
        "executing untrusted code before sandbox proofs exist",
        "n/a — refusal carries the contract citation",
        STATUS_DELEGATED,
    ),
    Requirement(
        "R-11", "lab.safety_rule",
        "Do not execute untrusted mutation code until all hard-sandbox requirements have negative tests and receipts.",
        "ofn.doctor.contract_map.execute_mutation",
        "tests.test_doctor_lane_contract_map::test_untrusted_execution_is_refused",
        "any request to execute mutation code",
        "immediate raise, no partial run, no auto-retry",
        "silent degradation to a soft sandbox",
        "n/a — no execution occurred",
        STATUS_DELEGATED,
    ),
    Requirement(
        "R-12", "flow.novelty_gate (NOT_IMPLEMENTED)",
        "Independent novelty evaluator: novel AND learnable.",
        "ofn.doctor.backlog.SelfBacklog.upsert_from_gaps",
        "tests.test_doctor_lane_backlog::test_13_backlog_no_duplicates_on_upsert",
        "contract gap extraction",
        "backlog item owner_ruling_required=True",
        "lane B improvising a novelty judge without an owner ruling",
        "self-backlog.json + proposal outcomes",
        STATUS_BACKLOG,
    ),
    Requirement(
        "R-13", "flow.budget_allocation (PARTIAL_ZERO_ALLOCATION)",
        "Governed life-currency allocation with nonnegative balances.",
        "ofn.doctor.backlog.SelfBacklog.upsert_from_gaps",
        "tests.test_doctor_lane_backlog::test_13_backlog_no_duplicates_on_upsert",
        "contract gap extraction",
        "backlog item owner_ruling_required=True",
        "lane B minting budget authority it was not given",
        "self-backlog.json",
        STATUS_BACKLOG,
    ),
    Requirement(
        "R-14", "security_incident_rule",
        "Escape/secret/policy attempt: stop, preserve evidence, quarantine, notify owner, no auto-retry.",
        "ofn.doctor.destiny.DestinyEngine (deny-touch → incident + ESCALATED_TO_OWNER)",
        "tests.test_doctor_lane_destiny::test_incident_rule_on_deny_touch",
        "proposal touching a forbidden target",
        "incident line in journal + owner escalation, zero retries",
        "retrying or logging-and-continuing",
        "journal.jsonl incident line (sha256-signed)",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-15", "forbidden (list)",
        "All thirteen forbidden behaviours are deny-enforced targets.",
        "ofn.doctor.destiny.FORBIDDEN_TARGETS",
        "tests.test_doctor_lane_destiny::test_forbidden_targets_escalate",
        "proposal targeting any forbidden surface",
        "ESCALATED_TO_OWNER / REJECTED_WITH_REASON",
        "any forbidden target flowing into PR_CREATED",
        "proposal-outcomes.json",
        STATUS_IMPLEMENTED,
    ),
    Requirement(
        "R-16", "flow.receipts",
        "Append-only evidence and replay.",
        "ofn.doctor.receipts.ReceiptLog",
        "tests.test_doctor_lane_contract_map::test_12_tampered_line_is_detected",
        "receipt records",
        "self-verifying jsonl lines (per-line sha256)",
        "undetected tampering with a receipt line",
        "09-LANES/LB/runs/<date>/receipt.jsonl",
        STATUS_IMPLEMENTED,
    ),
)


class SandboxNotVerifiedError(RuntimeError):
    """Raised for ANY request to execute untrusted mutation code.

    Contract citation: lab.verdict = NOT_A_VERIFIED_HARD_SANDBOX and
    lab.safety_rule. Lifted only when lane C lands negative tests and
    receipts for every hard-sandbox requirement AND the owner rules the
    gate open. This lane does not get to lift its own guard (R-07).
    """


def execute_mutation(*_args, **_kwargs):
    raise SandboxNotVerifiedError(
        "refused: lab.verdict=NOT_A_VERIFIED_HARD_SANDBOX (LAB-DOCTOR-CONTRACT.yaml); "
        "untrusted mutation code may not execute until lane C lands negative tests "
        "+ receipts for every hard-sandbox requirement and the owner opens the gate"
    )


_EXPERIMENT_REQUIRED = (
    "experiment_id", "hypothesis", "frozen_metric", "baseline_ref", "candidate_ref",
    "control_or_placebo", "target_zone", "risk_budget", "timeout_s", "stop_condition",
    "rollback", "replay_recipe", "falsifier", "independent_judge", "expected_receipts",
)


def validate_experiment(exp: dict) -> list[str]:
    """experiment_contract.required_before_execution + constitutional_validation."""
    v: list[str] = []
    if not isinstance(exp, dict):
        return ["experiment: must be a mapping"]
    for key in _EXPERIMENT_REQUIRED:
        val = exp.get(key)
        if val is None or (isinstance(val, (str, list, dict)) and not val):
            v.append(f"{key}: required before execution")

    def _num(key, *, positive: bool):
        val = exp.get(key)
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            v.append(f"{key}: must be a number")
        elif positive and val <= 0:
            v.append(f"{key}: constitutional_validation requires positive")

    _num("timeout_s", positive=True)
    if exp.get("target_zone") not in ("B1", "B2"):
        v.append("target_zone: must be B1 or B2")
    budget = exp.get("risk_budget")
    if not isinstance(budget, dict):
        if "risk_budget" not in v:
            v.append("risk_budget: must be a mapping")
    else:
        for k in ("tokens", "risk_weight"):
            b = budget.get(k)
            if not isinstance(b, (int, float)) or isinstance(b, bool) or b <= 0:
                v.append(f"risk_budget.{k}: budget_positive requires a positive number")
        if not isinstance(budget.get("calls"), int) or isinstance(budget.get("calls"), bool):
            v.append("risk_budget.calls: must be an integer")
        if budget.get("max_external_effects") != 0:
            v.append("risk_budget.max_external_effects: external effects are forbidden (must be 0)")
    if not str(exp.get("rollback", "")).strip():
        v.append("rollback: constitutional_validation requires nonempty")
    return v


def load_contract() -> dict:
    return load_file(_CONTRACT_FILE)


def extract_gaps(contract: dict | None = None) -> list[dict]:
    """Deterministic gap extraction → feeds the self-backlog (missing organs)."""
    c = contract or load_contract()
    gaps: list[dict] = []

    def _add(area: str, item: str, status: str):
        gaps.append({"area": area, "item": item, "status": status})

    for step in c.get("flow", []):
        st = step.get("current_status")
        if st and st not in ("COMPLETE",):
            _add("flow", f"{step.get('step')}::{step.get('actor')}", st)
    for gate_id, gate in (c.get("gates") or {}).items():
        st = gate.get("status", "")
        if any(k in st for k in ("NOT_STARTED", "BLOCKED", "INCONCLUSIVE")):
            _add("gate", f"{gate_id}:{gate.get('name')}", st)
    lab = c.get("lab", {}).get("hard_sandbox_requirements", {})
    for req, spec in lab.items():
        cur = spec.get("current_status", "")
        if "NOT_VERIFIED" in cur or "PARTIAL" in cur or "NOT_PROVEN" in cur:
            _add("lab", f"hard_sandbox.{req}", cur)
    if c.get("doctor", {}).get("prescription_required", {}).get("status") == "PROPOSED_EXTENSION":
        _add("doctor", "prescription engine beyond validation (generation needs the brain)", "PROPOSED_EXTENSION")
    return gaps


def requirement_stats() -> dict:
    by: dict[str, int] = {}
    for r in REQUIREMENTS:
        by[r.status] = by.get(r.status, 0) + 1
    return {"total": len(REQUIREMENTS), **by}
