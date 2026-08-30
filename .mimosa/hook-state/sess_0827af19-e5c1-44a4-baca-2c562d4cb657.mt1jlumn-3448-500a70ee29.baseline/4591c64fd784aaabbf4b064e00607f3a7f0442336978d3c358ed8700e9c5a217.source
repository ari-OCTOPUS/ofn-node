#!/usr/bin/env python3
"""test_phase_jn.py — فاز J→N: advice-only · shadow influence · evaluation · limited effect.

هر چهار ماژول با harness ایزوله تست می‌شوند (state موقت، صفر لمس state زنده).
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("phase-jn")
_OPS = harness.SELF_OPS

for _p in (str(_OPS), str(_OPS / "memory"), str(_OPS / "owner_console")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import equation_advice as ea  # noqa: E402
import shadow_influence as si  # noqa: E402
import shadow_evaluation as se  # noqa: E402
import limited_effect as le  # noqa: E402


# ════════════════════════════════════════════════════════════════════
# فاز J — equation_advice
# ════════════════════════════════════════════════════════════════════

def _write_org_state():
    st = Path(ENV["ops"]) / "state"
    st.mkdir(parents=True, exist_ok=True)
    (st / "ORGANISM-STATE.json").write_text(json.dumps({
        "beat": 100,
        "halted": False,
        "protective_skip": False,
        "pain_assessment": {"pain": 0.8},
        "math_control": {"period_s": 700.0, "effects": [], "rank_bias": None},
    }), encoding="utf-8")


def t_j_advice_labels_are_always_false():
    ea.STATE_DIR = Path(ENV["ops"]) / "state"
    _write_org_state()
    snap = ea.equation_advice_snapshot()
    assert snap["equation_advice_only"] is True
    assert snap["decision_effect"] is False
    assert snap["apply_effect"] is False
    assert snap["may_authorize"] is False


def t_j_pain_above_threshold_advises_slow_down():
    ea.STATE_DIR = Path(ENV["ops"]) / "state"
    _write_org_state()
    snap = ea.equation_advice_snapshot()
    pain = next((s for s in snap["advice"] if s["eq"] == ea.EQ_PAIN), None)
    assert pain is not None and pain["advice"] == "slow_down"
    assert "nociceptor-pain" in snap["equations_consulted"]


def t_j_missing_state_is_failsoft_empty():
    empty = Path(tempfile.mkdtemp(prefix="ea-")) / "state"
    empty.mkdir()
    ea.STATE_DIR = empty
    snap = ea.equation_advice_snapshot()
    assert snap["equation_advice_only"] is True
    assert isinstance(snap["advice"], list)


# ════════════════════════════════════════════════════════════════════
# فاز K — shadow_influence
# ════════════════════════════════════════════════════════════════════

def t_k_probe_never_applies():
    si.STATE_DIR = Path(ENV["ops"]) / "state"
    _write_org_state()
    rec = si.evaluate_shadow()
    assert rec["applied"] is False
    assert rec["may_authorize"] is False
    assert rec["real_decision"] in ("continue", "halt", "protective_skip")
    assert rec["shadow_decision"] in ("continue", "slow_down", "unknown")


def t_k_record_writes_jsonl_under_state():
    tmp = Path(tempfile.mkdtemp(prefix="si-"))
    si.STATE_DIR = tmp
    si.OUT_DIR = tmp / "shadow-influence"
    si.DIVERGENCE = si.OUT_DIR / "divergence.jsonl"
    rec = si.record_divergence({"tick": 1, "divergence": False, "applied": False})
    assert rec["recorded"] is True
    assert si.count_records() == 1
    body = si.DIVERGENCE.read_text("utf-8")
    assert '"applied": false' in body


# ════════════════════════════════════════════════════════════════════
# فاز L — shadow_evaluation
# ════════════════════════════════════════════════════════════════════

def _seed_divergence(tmp: Path, n: int, applied_ok: bool = True):
    se.STATE_DIR = tmp
    se.DIVERGENCE = tmp / "shadow-influence" / "divergence.jsonl"
    se.DIVERGENCE.parent.mkdir(parents=True)
    rows = []
    for i in range(n):
        r = {"schema": "shadow-influence.v1",
             "ts": "2026-08-12T%02d:00:00Z" % (i % 24),
             "tick": 1000 + i,
             "real_decision": "continue",
             "shadow_decision": "slow_down" if i % 3 == 0 else "continue",
             "divergence": i % 3 == 0,
             "applied": False,
             "may_authorize": False}
        rows.append(json.dumps(r))
    se.DIVERGENCE.write_text("\n".join(rows) + "\n", encoding="utf-8")


def t_l_insufficient_data_keeps_advisory():
    tmp = Path(tempfile.mkdtemp(prefix="se-"))
    _seed_divergence(tmp, 10)
    res = se.evaluate(window_days=7, min_samples=100)
    assert res["verdict"] == "KEEP_ADVISORY"
    assert "insufficient" in res["reason"]


def t_l_ready_when_window_complete_and_clean():
    tmp = Path(tempfile.mkdtemp(prefix="se-"))
    _seed_divergence(tmp, 120)
    res = se.evaluate(window_days=7, min_samples=100)
    assert res["verdict"] in ("READY_FOR_VOTE", "REVIEW_REQUIRED")
    assert res["integrity_violations"] == []


def t_l_integrity_violation_forces_review():
    tmp = Path(tempfile.mkdtemp(prefix="se-"))
    _seed_divergence(tmp, 120)
    # تزریق نقض
    rows = se.DIVERGENCE.read_text("utf-8").splitlines()
    bad = json.loads(rows[0])
    bad["applied"] = True
    rows.insert(0, json.dumps(bad))
    se.DIVERGENCE.write_text("\n".join(rows), encoding="utf-8")
    res = se.evaluate(window_days=7, min_samples=100)
    assert res["verdict"] == "REVIEW_REQUIRED"
    assert "applied_true" in res["integrity_violations"]


# ════════════════════════════════════════════════════════════════════
# فاز N — limited_effect (رأی مالک: انتخاب ۳ — با رأی فعال، fail-closed)
# ════════════════════════════════════════════════════════════════════

def _vote(choice: str = "0"):
    """تزریق رأی موقت برای تست (بدون لمس فایل واقعی)."""
    os.environ["OCTOPUS_OWNER_VERDICTS"] = "__isolated_no_owner_verdicts__.yaml"
    os.environ["OCTOPUS_LIMITED_EFFECT_PHASE_N"] = choice


def t_n_no_vote_denies_everything():
    _vote("0")
    try:
        assert le.enabled() is False
        r = le.evaluate({})
        assert r["decision"] == "DENY" and r["applied"] is False
    finally:
        os.environ.pop("OCTOPUS_LIMITED_EFFECT_PHASE_N", None)


def t_n_vote_3_missing_fields_deny():
    _vote("3")
    try:
        assert le.enabled() is True
        r = le.evaluate({"action": "throttle"})
        assert r["decision"] == "DENY"
        assert "missing required fields" in r["reason"]
        assert "proposal_hash" in r["reason"]
    finally:
        os.environ.pop("OCTOPUS_LIMITED_EFFECT_PHASE_N", None)


def t_n_vote_3_full_request_is_proposal_only_never_applied():
    _vote("3")
    try:
        future = "2999-01-01T00:00:00Z"
        r = le.evaluate({
            "action": "throttle",
            "proposal_hash": "sha256:x",
            "policy_version": "ADR-033-v1",
            "state_version": 0,
            "expiry_at": future,
            "idempotency_key": "k-1",
            "owner_verdict": "owner:phase-m-choice3",
        })
        assert r["allowed"] is True
        assert r["decision"] == "ALLOWED_AS_PROPOSAL"
        assert r["applied"] is False
    finally:
        os.environ.pop("OCTOPUS_LIMITED_EFFECT_PHASE_N", None)


def t_n_record_effect_writes_audit_line():
    _vote("3")
    tmp = Path(tempfile.mkdtemp(prefix="le-"))
    le.STATE_DIR = tmp
    le.ACTIVE_EFFECTS = tmp / "limited-effects" / "active.jsonl"
    try:
        future = "2999-01-01T00:00:00Z"
        rec = le.record_effect({
            "action": "throttle",
            "proposal_hash": "sha256:y",
            "policy_version": "ADR-033-v1",
            "state_version": 0,
            "expiry_at": future,
            "idempotency_key": "k-2",
            "owner_verdict": "owner:phase-m-choice3",
        })
        assert rec["allowed"] is True and rec["recorded"] is True
        body = le.ACTIVE_EFFECTS.read_text("utf-8")
        assert '"applied": false' in body and '"may_authorize": false' in body
    finally:
        os.environ.pop("OCTOPUS_LIMITED_EFFECT_PHASE_N", None)


def t_n_disallowed_action_denied_even_with_vote():
    _vote("3")
    try:
        future = "2999-01-01T00:00:00Z"
        r = le.evaluate({
            "action": "send_email",   # خارج از لیست مجاز
            "proposal_hash": "sha256:z",
            "policy_version": "ADR-033-v1",
            "state_version": 0,
            "expiry_at": future,
            "idempotency_key": "k-3",
            "owner_verdict": "owner:phase-m-choice3",
        })
        assert r["decision"] == "DENY"
    finally:
        os.environ.pop("OCTOPUS_LIMITED_EFFECT_PHASE_N", None)


if __name__ == "__main__":
    failed = harness.run([
        ("[J] advice labels always false", t_j_advice_labels_are_always_false),
        ("[J] pain>0.7 → slow_down advice", t_j_pain_above_threshold_advises_slow_down),
        ("[J] missing state fail-soft", t_j_missing_state_is_failsoft_empty),
        ("[K] probe never applies", t_k_probe_never_applies),
        ("[K] record writes jsonl under state", t_k_record_writes_jsonl_under_state),
        ("[L] insufficient → KEEP_ADVISORY", t_l_insufficient_data_keeps_advisory),
        ("[L] window complete → ready/review", t_l_ready_when_window_complete_and_clean),
        ("[L] integrity violation → review", t_l_integrity_violation_forces_review),
        ("[N] no vote deny", t_n_no_vote_denies_everything),
        ("[N] vote3 missing fields deny", t_n_vote_3_missing_fields_deny),
        ("[N] vote3 full request proposal-only", t_n_vote_3_full_request_is_proposal_only_never_applied),
        ("[N] record effect audit line", t_n_record_effect_writes_audit_line),
        ("[N] disallowed action denied", t_n_disallowed_action_denied_even_with_vote),
    ])
    sys.exit(1 if failed else 0)
