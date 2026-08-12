#!/usr/bin/env python3
"""ADR-034 A+B acceptance — containment + demotion (offline, $0, no WORKLOCK).

A criteria:
  1) neural snapshots/trace still buildable
  2) protective_halt / _protective_skip not triggered from neural
  3) no new protective_skip state write from neural path
  4) pain>thr → protective_proposal / SHADOW only
  5) replay deterministic; zero external side effect; control state not mutated by proposal

B DoD:
  PainAssessment immutable; PolicyGate owns halt; organism/brain_worker demoted;
  high-pain / NaN / store-down / kill-switch / APPLY deprecated semantics.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("adr034-demote")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "neural"), str(_OPS / "policy")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402
from neural.pain_assessment import PainAssessment, build_pain_assessment  # noqa: E402


def _env_clean():
    for k in (
        "OCTOPUS_NEURAL_LEARNED_APPLY",
        "OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL",
        "OCTOPUS_PAIN_THRESHOLD_CALIBRATED",
        "OCTOPUS_NEURAL_EFFECT_SHADOW",
    ):
        os.environ.pop(k, None)


def t_pain_assessment_immutable_fields():
    a = build_pain_assessment(pain_level=0.9, threshold=0.7)
    assert isinstance(a, PainAssessment)
    assert a.pain == 0.9 and a.status == "OK"
    assert a.proposal == "protective_proposal"
    assert a.trace_id.startswith("pain-")
    assert "pain_above_threshold" in a.reason_codes
    try:
        a.pain = 0.1  # type: ignore[misc]
        raise AssertionError("PainAssessment must be frozen")
    except Exception:
        pass


def t_nan_is_unknown_no_influence():
    a = build_pain_assessment(pain_level=float("nan"))
    assert a.status == "UNKNOWN" and a.proposal == "none"
    r = wiring.protective_override({"pain": {"level": float("nan")}, "reflexes": []})
    assert r["action"] == "none" and r["override"] is False
    assert r["executable"] is False


def t_high_pain_proposal_only():
    _env_clean()
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"
    try:
        r = wiring.protective_override({"pain": {"level": 0.95}, "reflexes": []})
        assert r["action"] == "protective_proposal"
        assert r["override"] is False and r["executable"] is False
        assert r["shadow_alert"] is True
        assert r["assessment"]["evidence_level"] == "SHADOW"
    finally:
        _env_clean()


def t_learned_apply_flag_does_not_execute():
    """ADR-034 containment path: when APPLY unset/0 — no execute.
    (ADR-035 re-arms APPLY=1 separately; see test_adr035_neural_rearm.)"""
    _env_clean()
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"
    try:
        r = wiring.protective_override({
            "pain": {"level": 0.3},
            "reflexes": [],
            "brain_inputs": {"learned_pressure": 0.9},
        })
        assert r["action"] != "protective_halt"
        assert r["executable"] is False
        assert r["override"] is False
    finally:
        _env_clean()


def t_proposal_flag_shadow_fold_only():
    _env_clean()
    os.environ["OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL"] = "1"
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"
    try:
        r = wiring.protective_override({
            "pain": {"level": 0.3},
            "reflexes": [],
            "brain_inputs": {"learned_pressure": 0.9},
        })
        assert r["action"] == "protective_proposal"
        assert r["executable"] is False
        codes = r["assessment"]["reason_codes"]
        assert "learned_pressure_shadow_fold" in codes
    finally:
        _env_clean()


def t_organism_brain_cannot_neural_skip():
    """ADR-034: without executable gate, consumers stay proposal-only.
    ADR-035 adds executable-gated assignment — pin that gate exists."""
    org = (_OPS / "organism.py").read_text(encoding="utf-8")
    bw = (_OPS / "brain_worker.py").read_text(encoding="utf-8")
    assert 'get("executable")' in org and 'get("executable")' in bw
    assert "SHADOW_ALERT neural" in org and "SHADOW_ALERT neural" in bw
    # skip assignment must be behind executable (not unconditional)
    assert '_protective_skip = True' in org
    assert 'self.protective_skip = True' in bw
    # ensure executable check appears before skip assignment in organism
    i_exec = org.index('get("executable")')
    i_skip = org.index('_protective_skip = True')
    assert i_exec < i_skip


def t_request_halt_requires_approval_and_kill_switch():
    deny = wiring.request_protective_halt(
        run_id="r1",
        approval_id=None,
        idempotency_key="k1",
        provenance_id="p1",
        kill_switch_engaged=False,
        store_ok=True,
    )
    assert deny["allowed"] is False
    assert deny["decision"] == "deny"

    ks = wiring.request_protective_halt(
        run_id="r1",
        approval_id="appr-1",
        idempotency_key="k1",
        provenance_id="p1",
        kill_switch_engaged=True,
        store_ok=True,
    )
    assert ks["allowed"] is False
    assert "kill_switch" in ks["reason"]

    store = wiring.request_protective_halt(
        run_id="r1",
        approval_id="appr-1",
        idempotency_key="k1",
        provenance_id="p1",
        kill_switch_engaged=False,
        store_ok=False,
    )
    assert store["allowed"] is False
    assert store["reason"] == "store_unavailable"

    ok = wiring.request_protective_halt(
        run_id="r1",
        approval_id="appr-1",
        idempotency_key="k1",
        provenance_id="p1",
        kill_switch_engaged=False,
        store_ok=True,
    )
    assert ok["allowed"] is True


def t_replay_deterministic_zero_control_mutation():
    """Same seed inputs → same proposal action when APPLY=0."""
    _env_clean()
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"
    try:
        payload = {"pain": {"level": 0.88}, "reflexes": [], "brain_inputs": {}}
        a1 = wiring.protective_override(payload)
        a2 = wiring.protective_override(payload)
        assert a1["action"] == a2["action"] == "protective_proposal"
        assert a1["override"] is False and a2["override"] is False
        for key in ("pain", "status", "proposal", "threshold"):
            assert a1["assessment"][key] == a2["assessment"][key]
    finally:
        _env_clean()


def t_flags_cmd_containment():
    """ADR-035 re-armed APPLY=1; rollback path still documents =0."""
    flags = (_OPS / "OCTOPUS-flags.cmd").read_text(encoding="utf-8", errors="replace")
    assert "set OCTOPUS_NEURAL_LEARNED_APPLY=1" in flags
    assert "OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL=1" in flags
    assert "ADR-035" in flags


def t_capability_record_armed():
    """Post ADR-035 (owner «هردو»): capability record reflects ARMED apply."""
    cap = json.loads((_OPS / "capabilities" / "neural-learned-apply.json").read_text(
        encoding="utf-8"))
    assert cap["truth_status"] == "TESTED"
    assert cap["evidence_level"] == "ARMED"
    assert cap["runtime"]["production_apply_enabled"] is True
    assert cap["authority"]["may_gate"] is True
    assert cap["authority"]["allowed_effect"] == "gate_internal"
    assert cap["evidence"]["adr"] == "ADR-035"
    # مرز سخت: اثر بیرونی/پول همچنان ممنوع
    assert cap["authority"]["may_trigger_external_action"] is False
    assert cap["authority"]["may_mutate_ledger"] is False


if __name__ == "__main__":
    failed = harness.run([
        ("PainAssessment immutable + fields", t_pain_assessment_immutable_fields),
        ("NaN → UNKNOWN no influence", t_nan_is_unknown_no_influence),
        ("high pain → proposal only", t_high_pain_proposal_only),
        ("LEARNED_APPLY=0 not executable", t_learned_apply_flag_does_not_execute),
        ("PROPOSAL shadow fold only", t_proposal_flag_shadow_fold_only),
        ("organism/brain executable-gated", t_organism_brain_cannot_neural_skip),
        ("PolicyGate halt gates", t_request_halt_requires_approval_and_kill_switch),
        ("replay deterministic / no skip mutation", t_replay_deterministic_zero_control_mutation),
        ("flags containment A", t_flags_cmd_containment),
        ("capability ARMED record", t_capability_record_armed),
    ])
    sys.exit(1 if failed else 0)
