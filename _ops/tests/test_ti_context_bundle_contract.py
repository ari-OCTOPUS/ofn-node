#!/usr/bin/env python3
"""Grounded contracts for ContextBundle and exact control authorization."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
sys.path.insert(0, str(_OPS))

import harness  # noqa: E402
ENV = harness.setup("ti-context-contract")

import context_bundle as cb  # noqa: E402
import control_contracts as cc  # noqa: E402

NOW = 1_800_000_000.0


def _bundle(**overrides):
    args = {
        "mission_id": "m1", "task_id": "t1", "trace_id": "tr1",
        "tenant_id": "tenant", "project_id": "project",
        "agent_role": "researcher", "phase": "verify",
        "objective": "verify a bounded claim", "ttl_s": 60,
    }
    args.update(overrides)
    original = cb.time.time
    cb.time.time = lambda: NOW
    try:
        return cb.ContextBundle.create(**args)
    finally:
        cb.time.time = original


def _proposal(action_type="http_request", risk="high", confidence=0.9):
    action = cc.ActionSpec(action_type, "fixture", "observe",
                           {"method": "GET"}, reversible=True,
                           sandbox_required=True)
    original_now = cc._now
    original_id = cc._id
    ids = iter(("ap_fixed", "ad_fixed", "er_fixed"))
    cc._now = lambda: NOW
    cc._id = lambda prefix: next(ids)
    try:
        proposal = cc.ActionProposal.create(
            mission_id="m1", task_id="t1", trace_id="tr1",
            tenant_id="tenant", project_id="project", agent_id="agent",
            title="observe", summary="bounded observation", risk=risk,
            confidence=confidence, action=action, ttl_s=600)
    finally:
        cc._now = original_now
        cc._id = original_id
    return proposal


def t_a_valid_bundle_roundtrips_deterministically():
    b = _bundle(evidence=[cb.EvidenceRef("ref:1", "verified", "HIGH", NOW)],
                verified_facts=["fact one"], memory_scopes=["project"])
    assert b.validate(now=NOW + 1) == []
    raw = b.compact_json()
    data = json.loads(raw)
    assert data["schema"] == cb.SCHEMA
    assert data["phase"] == "verify"
    assert raw == b.compact_json()


def t_b_wrong_schema_is_rejected_and_not_relabelled():
    b = replace(_bundle(), schema="invented.v9")
    assert "invalid schema" in b.validate(now=NOW + 1)
    data = json.loads(b.compact_json())
    assert data["schema"] == "invented.v9"
    assert data["schema"] != cb.SCHEMA


def t_c_invalid_phase_fails_validation():
    b = _bundle(phase="dream")
    assert "invalid phase" in b.validate(now=NOW + 1)


def t_d_expiry_is_fail_closed():
    b = _bundle(ttl_s=2)
    assert b.validate(now=NOW + 1) == []
    assert "bundle expired" in b.validate(now=NOW + 2)


def t_e_personal_core_scope_is_role_fenced():
    denied = _bundle(memory_scopes=["personal_core"])
    allowed = _bundle(memory_scopes=["personal_core"], agent_role="owner_interface")
    assert "agent role cannot access personal_core" in denied.validate(now=NOW + 1)
    assert allowed.validate(now=NOW + 1) == []


def t_f_fact_and_reference_limits_are_bounded_at_creation():
    refs = [cb.EvidenceRef(f"r:{n}", "x") for n in range(80)]
    b = _bundle(verified_facts=[f"f{n}" for n in range(80)], evidence=refs)
    assert len(b.verified_facts) == 24
    assert len(b.evidence) == 48
    assert b.validate(now=NOW + 1) == []


def t_g_no_reasoning_or_scratchpad_channel_exists():
    keys = set(json.loads(_bundle().compact_json()))
    forbidden = {"reasoning", "chain_of_thought", "scratchpad", "messages", "conversation"}
    assert not (keys & forbidden), keys & forbidden


def t_h_sensitive_action_requires_exact_human_approval():
    p = _proposal()
    assert cc.authorization(p, None, now=NOW + 1)["reason"] == "approval-required"
    d = cc.ApprovalDecision("ad_fixed", p.proposal_id, p.action_sha256,
                            "approve", "owner", "human", NOW + 1,
                            NOW + 100)
    result = cc.authorization(p, d, now=NOW + 2)
    assert result["allow"] is True
    assert result["action_sha256"] == p.action_sha256


def t_i_non_human_sensitive_approval_is_denied():
    p = _proposal()
    d = cc.ApprovalDecision("ad_fixed", p.proposal_id, p.action_sha256,
                            "approve", "policy-bot", "policy", NOW + 1,
                            NOW + 100)
    assert cc.authorization(p, d, now=NOW + 2)["reason"] == "human-approval-required"


def t_j_mismatched_action_hash_is_denied():
    p = _proposal()
    d = cc.ApprovalDecision("ad_fixed", p.proposal_id, "0" * 64,
                            "approve", "owner", "human", NOW + 1,
                            NOW + 100)
    result = cc.authorization(p, d, now=NOW + 2)
    assert result["allow"] is False
    assert "decision does not bind exact action" in result["errors"]


def t_k_expired_decision_is_denied():
    p = _proposal()
    d = cc.ApprovalDecision("ad_fixed", p.proposal_id, p.action_sha256,
                            "approve", "owner", "human", NOW + 1,
                            NOW + 2)
    result = cc.authorization(p, d, now=NOW + 2)
    assert result["allow"] is False
    assert "decision expired" in result["errors"]


def t_l_missing_execution_receipt_never_matches():
    p = _proposal()
    d = cc.ApprovalDecision("ad_fixed", p.proposal_id, p.action_sha256,
                            "approve", "owner", "human", NOW + 1,
                            NOW + 100)
    assert cc.execution_matches_approval(d, None) == {
        "match": False, "reason": "no-execution-record"}


def t_m_changed_execution_is_detected_as_toctou():
    p = _proposal()
    d = cc.ApprovalDecision("ad_fixed", p.proposal_id, p.action_sha256,
                            "approve", "owner", "human", NOW + 1,
                            NOW + 100)
    r = cc.ExecutionResult("er_fixed", p.proposal_id, d.decision_id,
                           "f" * 64, "success", NOW + 2, NOW + 3)
    verdict = cc.execution_matches_approval(d, r)
    assert verdict["match"] is False
    assert verdict["reason"] == "action-changed-after-approval"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_ti_context_bundle_contract: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
