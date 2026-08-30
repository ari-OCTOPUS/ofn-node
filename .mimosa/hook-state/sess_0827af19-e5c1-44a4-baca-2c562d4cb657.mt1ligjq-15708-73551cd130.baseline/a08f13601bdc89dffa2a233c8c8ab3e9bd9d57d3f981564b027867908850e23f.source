#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contracts + scoped-memory regression tests for the 2030 control-plane update."""
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for p in (_HERE.parent, _HERE.parent / "memory", _HERE.parent / "outcomes"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import harness
harness.setup("control-contracts-v2")

import control_contracts as cc
import context_bundle as cb
import memory_store as ms
import gate as mg


def t_a_exact_authorization_and_toctou():
    a = cc.ActionSpec("code_patch", "_ops/x.py", "apply", {"patch_sha": "abc"})
    p = cc.ActionProposal.create(mission_id="m1", task_id="t1", trace_id="tr1",
        tenant_id="personal", project_id="octopus", agent_id="coder", title="fix",
        summary="safe patch", risk="high", confidence=.9, action=a)
    assert cc.authorization(p, None)["reason"] == "approval-required"
    d = cc.ApprovalDecision.create(p, decision="approve", reviewer_id="owner")
    assert cc.authorization(p, d)["allow"] is True
    a2 = cc.ActionSpec("code_patch", "_ops/y.py", "apply", {"patch_sha": "evil"})
    p2 = cc.ActionProposal(**{**p.__dict__, "action": a2})
    assert cc.authorization(p2, d)["allow"] is False


def t_b_nonhuman_cannot_authorize_sensitive_action():
    a = cc.ActionSpec("external_message", "telegram", "send", {"ref": "draft-1"})
    p = cc.ActionProposal.create(mission_id="m", task_id="t", trace_id="tr",
        tenant_id="personal", project_id="p", agent_id="ops", title="send",
        summary="message", risk="medium", confidence=.99, action=a)
    d = cc.ApprovalDecision.create(p, decision="approve", reviewer_id="policy",
                                   reviewer_type="policy_engine")
    assert cc.authorization(p, d)["reason"] == "human-approval-required"


def t_c_context_bundle_is_scoped_and_has_no_reasoning_channel():
    b = cb.ContextBundle.create(mission_id="m", task_id="t", trace_id="tr",
        tenant_id="personal", project_id="paint", agent_role="coder", phase="verify",
        objective="verify patch", verified_facts=["suite baseline green"],
        tool_allowlist=["pytest"], memory_scopes=["project", "verified_shared"])
    assert b.validate() == []
    blob = b.compact_json()
    assert "scratchpad" not in blob and "chain_of_thought" not in blob
    bad = cb.ContextBundle.create(mission_id="m", task_id="t", trace_id="tr",
        tenant_id="personal", project_id="paint", agent_role="coder", phase="act",
        objective="x", memory_scopes=["personal_core"])
    assert "agent role cannot access personal_core" in bad.validate()


def t_d_memory_scope_fence_and_owner_promotion():
    old = os.environ.get(mg.FLAG)
    os.environ[mg.FLAG] = "1"
    try:
        with tempfile.TemporaryDirectory() as td:
            st = ms.MemoryStore(Path(td) / "m.db")
            g = mg.MemoryGate(st, Path(td) / "proposals.jsonl")
            common = {"namespace": "semantic", "source": "deterministic", "producer": "sensor",
                      "content": "painting workflow evidence", "salience": .9,
                      "tenant_id": "personal", "agent_id": "research"}
            a = g.submit({**common, "project_id": "paint", "scope": "project"})
            b = g.submit({**common, "content": "mining workflow evidence", "project_id": "mining",
                          "scope": "project"})
            assert a["verb"] == b["verb"] == "commit"
            hits = st.search("workflow", tenant_id="personal", project_id="paint",
                             scopes=["project"])
            assert len(hits) == 1 and hits[0]["project_id"] == "paint"
            prop = g.submit({**common, "content": "unverified global claim",
                             "project_id": "paint", "scope": "verified_shared"})
            assert prop["verb"] == "propose"
            assert st.metrics()["active"] == 2
            st.close()
    finally:
        if old is None:
            os.environ.pop(mg.FLAG, None)
        else:
            os.environ[mg.FLAG] = old


# ─── ExecutionResult (2026-07-28, step 5) ────────────────────────────────
# approval_state_machine already had an `execution_result` field, but it lived
# ON the approval object and was mutated in place. That conflates a decision
# (immutable) with an event (append-only), and makes the one question that
# matters unanswerable: was what executed the same thing that was approved?

def _proposal_and_decision():
    spec = cc.ActionSpec(action_type="code_patch", target="_ops/x.py",
                         operation="apply_patch", args={"content_sha256": "aaa"},
                         reversible=True, sandbox_required=True)
    p = cc.ActionProposal.create(
        mission_id="m", task_id="t", trace_id="tr", tenant_id="personal",
        project_id="octopus-core", agent_id="self_patch", title="p",
        summary="s", risk="high", confidence=1.0, action=spec)
    d = cc.ApprovalDecision.create(p, decision="approve", reviewer_id="owner",
                                   reviewer_type="human")
    return p, d


def t_e_execution_matching_the_approval_is_verified():
    import time
    p, d = _proposal_and_decision()
    r = cc.ExecutionResult.create(proposal_id=p.proposal_id, decision_id=d.decision_id,
                                  action_sha256=p.action_sha256, outcome="success",
                                  started_at=time.time())
    v = cc.execution_matches_approval(d, r)
    assert v["match"] is True and v["reason"] == "approved-action-executed", v


def t_f_an_action_changed_after_approval_is_caught():
    """The whole point: approving payload A must not authorise payload B."""
    import time
    p, d = _proposal_and_decision()
    r = cc.ExecutionResult.create(proposal_id=p.proposal_id, decision_id=d.decision_id,
                                  action_sha256="deadbeef", outcome="success",
                                  started_at=time.time())
    v = cc.execution_matches_approval(d, r)
    assert v["match"] is False and v["reason"] == "action-changed-after-approval", v


def t_g_missing_records_fail_closed():
    """An unverifiable execution is not 'probably fine' - for an audit trail
    it is the same as a mismatch."""
    import time
    p, d = _proposal_and_decision()
    ok = cc.ExecutionResult.create(proposal_id=p.proposal_id, decision_id=d.decision_id,
                                   action_sha256=p.action_sha256, outcome="success",
                                   started_at=time.time())
    assert cc.execution_matches_approval(d, None)["match"] is False
    assert cc.execution_matches_approval(None, ok)["match"] is False
    assert cc.execution_matches_approval(None, None)["match"] is False


def t_h_a_result_from_another_decision_is_rejected():
    import time
    p, d = _proposal_and_decision()
    _, d2 = _proposal_and_decision()
    r = cc.ExecutionResult.create(proposal_id=p.proposal_id, decision_id=d2.decision_id,
                                  action_sha256=p.action_sha256, outcome="success",
                                  started_at=time.time())
    assert cc.execution_matches_approval(d, r)["reason"] == "different-decision"


def t_i_an_invalid_result_never_counts_as_a_match():
    import time
    p, d = _proposal_and_decision()
    now = time.time()
    bad_outcome = cc.ExecutionResult.create(
        proposal_id=p.proposal_id, decision_id=d.decision_id,
        action_sha256=p.action_sha256, outcome="totally-made-up", started_at=now)
    assert cc.execution_matches_approval(d, bad_outcome)["match"] is False
    backwards = cc.ExecutionResult.create(
        proposal_id=p.proposal_id, decision_id=d.decision_id,
        action_sha256=p.action_sha256, outcome="success",
        started_at=now, finished_at=now - 10)
    assert cc.execution_matches_approval(d, backwards)["match"] is False


def t_j_the_module_still_executes_nothing():
    """It describes and compares. If it ever runs anything, every gate is moot."""
    import ast
    from pathlib import Path as _P
    tree = ast.parse(_P(cc.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"subprocess", "requests", "urllib", "socket", "os"}), imported


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_control_contracts_v2: "
          f"{len(checks)-failed}/{len(checks)}")
    raise SystemExit(1 if failed else 0)
