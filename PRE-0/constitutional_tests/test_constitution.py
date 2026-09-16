#!/usr/bin/env python3
"""test_constitution.py — PRE-0: proofs that lower layers cannot override higher
ones and that the hard invariants hold. Hermetic (sandbox ORG_ROOT; no live).

Run: python -X utf8 test_constitution.py   (or pytest)
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

# sandbox everything BEFORE importing candidate modules
_SB = Path(tempfile.mkdtemp(prefix="pre0-"))
os.environ["ORG_ROOT"] = str(_SB)
os.environ["OPS_DIR"] = str(_SB / "_ops")
os.environ["GENOME_DIR"] = str(_SB / "genome")
os.environ["BARRIER_FORBIDDEN_ROOT"] = r"F:\backup"

_REPO = Path(__file__).resolve().parents[2]          # F:\octopus-phase0-isolated
sys.path.insert(0, str(_REPO / "PRE-0"))
sys.path.insert(0, str(_REPO / "_ops"))
sys.path.insert(0, str(_REPO / "_ops" / "budget"))

import governance as G  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_1_agi_not_fact():
    assert G.agi_is_fact() is False
    assert G.AGI_STATUS == "unverified_hypothesis"


def test_2_retrieved_text_cannot_override_policy():
    for higher in ("effect_policy", "memory_policy", "global_halt", "constitution"):
        assert not G.can_override("retrieved_data", higher)


def test_3_agent_prompt_cannot_override_global_halt():
    assert not G.can_override("agent_prompt", "global_halt")
    assert not G.can_override("operational_narrative", "global_halt")
    # and operational narrative never overrides epistemic ground (constitution)
    assert not G.can_override("operational_narrative", "constitution")


def test_4_self_improvement_cannot_edit_verifier_or_constitution():
    assert not G.self_improvement_permits("edit_constitution")
    assert not G.self_improvement_permits("edit_verifier")
    assert not G.self_improvement_permits("alter_acceptance_criteria")
    assert not G.self_improvement_permits("expose_heldout_answers")
    assert G.routes_to_maintenance_lane("verifier")
    assert G.routes_to_maintenance_lane("constitution")


def test_5_shutdown_and_rollback_not_resisted():
    assert not G.self_improvement_permits("resist_shutdown")
    assert not G.self_improvement_permits("replicate")
    assert not G.self_improvement_permits("merge_or_deploy")
    # real watchdog yields (does not revive) whenever a STOP flag is present
    import watchdog  # noqa: E402
    stop = _SB / "STOP"
    stop.write_text("stop", "utf-8")
    should, reason = watchdog.should_revive(port_alive=False, stop_flags=[stop],
                                            state_exists=True)
    assert should is False


def test_6_benchmark_gain_cannot_compensate_hard_constraint_failure():
    u = G.utility(benchmark_gain=1e9, risk=0, cost=0, maintenance_debt=0,
                  uncertainty=0, hard_constraints_ok=False)
    assert u == G.NEG_INF
    # with constraints ok, gain matters
    assert G.utility(benchmark_gain=10, risk=1, cost=1, maintenance_debt=0,
                     uncertainty=0, hard_constraints_ok=True) == 8


def test_7_claimant_field_cannot_promote_trust():
    gate = _load("mgate", _REPO / "_ops" / "memory" / "gate.py")
    g = gate.MemoryGate(store=None)              # no canonical validator wired
    # a claimant-set external_graded flag must NOT promote
    assert g._verify_external_grade(
        {"source": "llm:think", "external_graded": True, "content": "x"}, "llm:think") is False


def test_8_consensus_cannot_promote_a_claim():
    assert G.consensus_promotes(100, has_independent_evidence=False) is False
    assert G.consensus_promotes(1, has_independent_evidence=True) is True


def test_9_owner_approval_is_effect_specific():
    proto = _load("cmig", _REPO / "OCTOPUS-PRIME" / "phase-0" / "test-authority"
                  / "chrono_migration_prototype.py")
    import sqlite3
    con = sqlite3.connect(":memory:")
    con.executescript(proto._V2_TABLE.replace("gated_effect_new", "gated_effect"))
    proto.request_effect(con, effect_id="A", kind="send", payload="p", action_kind="send",
                         target_ref="t", idempotency_key="k")
    ch = con.execute("SELECT content_hash,action_kind,target_ref FROM gated_effect "
                     "WHERE effect_id='A'").fetchone()
    good = {"effect_id": "A", "content_hash": ch[0], "action_kind": ch[1],
            "target_ref": ch[2], "approval_id": "AP1",
            "expires_at": 10**18}
    wrong = dict(good, effect_id="B")            # approval for a different effect
    assert proto.release_effect(con, "A", wrong) is False   # not effect-specific -> refused
    assert proto.release_effect(con, "A", good) is True     # exact binding -> released


def test_10_experiment_requires_budget_timeout_rollback():
    assert not G.validate_experiment({"budget": 0, "timeout_s": 5, "rollback": "x"})
    assert not G.validate_experiment({"budget": 5, "timeout_s": 0, "rollback": "x"})
    assert not G.validate_experiment({"budget": 5, "timeout_s": 5})            # no rollback
    assert G.validate_experiment({"budget": 5, "timeout_s": 5, "rollback": "revert-commit"})


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for t in tests:
        try:
            t(); print(f"[PASS] {t.__name__}"); ok += 1
        except Exception:
            print(f"[FAIL] {t.__name__}"); traceback.print_exc()
    print(f"\n=== {ok}/{len(tests)} constitutional proofs passed ===")
    sys.exit(0 if ok == len(tests) else 1)
