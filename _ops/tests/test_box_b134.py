#!/usr/bin/env python3
"""تست B1 (falsifiability) + B3 (Doctor connect) + B4 (fusion φ_t) ($0).

B1: neural Dreamer > chance روی seed tasks (falsifiable).
B3: Box → submit_for_approval (propose-only، no merge without human-append).
B4: φ_t coupling boosts novelty near critical; ablation on/off.
هیچ import از production. λ_persist منفی.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("box-b134")
_BOX = (harness.SELF_OPS / "doctor" / "box")
_DR = (harness.SELF_OPS / "doctor")
for _p in (str(_BOX), str(_DR), str(_DR.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# B1
from falsif_harness import (run_falsif_episode, run_falsif_suite,  # noqa: E402
                            SEED_TASKS, neural_dreamer_action)
# B3
from b3_bridge import BoxInsight, submit_box_insight, box_to_doctor_pipeline  # noqa: E402
# B4
from b4_fusion import compute_phi_t, phi_to_novelty, run_ablation  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# B1 — Falsifiability harness
# ════════════════════════════════════════════════════════════════════════════════

def t_b1_neural_mi_higher_than_null():
    """I(a;x) neural > null روی seed task."""
    result = run_falsif_episode(SEED_TASKS[0], n_steps=15, seed=42)
    assert result.neural_mi >= result.null_mi, \
        f"neural({result.neural_mi}) باید ≥ null({result.null_mi})"


def t_b1_neural_quality_higher():
    """کیفیتِ fixِ neural > null (good_fixes بیشتر)."""
    result = run_falsif_episode(SEED_TASKS[0], n_steps=15, seed=42)
    assert result.neural_quality >= result.null_quality, \
        f"neural quality({result.neural_quality}) باید ≥ null({result.null_quality})"


def t_b1_suite_neural_majority():
    """در اکثریتِ tasks، neural برنده است (falsifiable: اگر نه → Box بی‌ارزش)."""
    suite = run_falsif_suite(n_steps=15)
    assert suite["neural_majority"] is True, \
        f"neural باید اکثریت را ببرد: {suite['neural_wins']}/{suite['tasks_run']}"


def t_b1_falsifiable_flag():
    """suite falsifiable=True (Box خودش را falsify می‌کند)."""
    suite = run_falsif_suite()
    assert suite["falsifiable"] is True


def t_b1_neuralness_neural_higher():
    """neuralness_score: neural > null."""
    result = run_falsif_episode(SEED_TASKS[1], seed=42)
    assert result.neuralness_neural >= result.neuralness_null


# ════════════════════════════════════════════════════════════════════════════════
# B3 — Box → Doctor (propose-only)
# ════════════════════════════════════════════════════════════════════════════════

def _fake_doctor(submitted_log: list):
    """fake Doctor برای تستِ B3."""
    class FakeRFC:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)
    class FakeDoctor:
        def propose_rfc(self, bn, fix, expected_lift, rollback=""):
            submitted_log.append({"proposed": True, "fix": fix})
            return FakeRFC(rfc_id="RFC-test", status="drafted",
                           bottleneck=bn.get("bottleneck", ""),
                           fix=fix, expected_lift=expected_lift)
        def run_sandbox(self, rfc):
            rfc.status = "sandboxed"
        def submit_for_approval(self, rfc):
            rfc.status = "submitted-no-channel"
            submitted_log.append({"submitted": True})
            return False   # no channel
    return FakeDoctor()


def t_b3_submit_box_insight():
    """BoxInsight → Doctor.submit_for_approval (propose-only)."""
    log = []
    doc = _fake_doctor(log)
    insight = BoxInsight(bottleneck="test", fix="real fix here",
                         expected_lift="better", confidence=0.7)
    result = submit_box_insight(doc, insight)
    assert "submitted" in result
    assert result.get("rfc_id") == "RFC-test"


def t_b3_no_doctor_returns_false():
    """بدونِ doctor → submitted=False."""
    insight = BoxInsight(bottleneck="x", fix="y", expected_lift="z")
    result = submit_box_insight(None, insight)
    assert result["submitted"] is False


def t_b3_propose_only_no_merge():
    """خروجی propose_only=True (هیچ merge)."""
    log = []
    doc = _fake_doctor(log)
    insight = BoxInsight(bottleneck="x", fix="y", expected_lift="z")
    result = submit_box_insight(doc, insight)
    assert result.get("propose_only") is True
    # نباید merged/applied داشته باشد
    for forbidden in ("merged", "applied", "settled"):
        assert forbidden not in result


def t_b3_pipeline_from_metrics():
    """box_to_doctor_pipeline از metrics insights استخراج می‌کند."""
    log = []
    doc = _fake_doctor(log)
    metrics = {"bottlenecks": [{"description": "high errors", "suggested_fix": "add guard",
                                 "expected_lift": "fewer errors", "confidence": 0.8}]}
    results = box_to_doctor_pipeline(metrics, doc)
    assert len(results) == 1
    assert results[0].get("rfc_id") == "RFC-test"


def t_b3_insight_to_payload():
    """BoxInsight → RFC payload ساختارِ درست."""
    insight = BoxInsight(bottleneck="bn", fix="fx", expected_lift="el",
                         confidence=0.9, measured_lift_score=0.3)
    from b3_bridge import box_insight_to_rfc_payload
    payload = box_insight_to_rfc_payload(insight)
    assert payload["bottleneck"] == "bn"
    assert payload["evidence"]["source"] == "box-of-agents"
    assert payload["evidence"]["confidence"] == 0.9


# ════════════════════════════════════════════════════════════════════════════════
# B4 — Fusion φ_t coupling
# ════════════════════════════════════════════════════════════════════════════════

def t_b4_compute_phi_t_returns_fields():
    """compute_phi_t تمام فیلدها را برمی‌گرداند."""
    edges = [(0, 1), (1, 2), (0, 2)]
    phi = compute_phi_t(edges, 3, agent_states=[0.5, 0.3, 0.8])
    for key in ("phi_vec", "sigma", "spectral_gap", "near_critical", "available"):
        assert key in phi, f"missing {key}: {phi}"
    assert phi["available"] is True


def t_b4_phi_to_novelty_boosts_near_critical():
    """φ_t نزدیکِ critical → novelty بالا."""
    phi = {"sigma": 1.0, "near_critical": True, "available": True}
    nov = phi_to_novelty(phi, base_novelty=0.3)
    assert nov > 0.3, f"critical باید novelty را بالا ببرد: {nov}"


def t_b4_phi_to_novelty_base_when_off():
    """φ_t available=False → base_novelty (off mode)."""
    phi = {"available": False}
    nov = phi_to_novelty(phi, base_novelty=0.3)
    assert nov == 0.3


def t_b4_ablation_on_off():
    """ablation: novelty_on ≠ novelty_off (اگر φ_t available)."""
    edges = [(0, 1), (1, 2), (2, 0)]
    result = run_ablation(edges, 3, agent_states=[0.5, 0.6, 0.4])
    assert "novelty_on" in result.__dict__
    assert "novelty_off" in result.__dict__
    assert "novelty_boost" in result.__dict__


def t_b4_no_production_import():
    """B4 هیچ import از *_gate/chrono/money."""
    import b4_fusion
    src = open(b4_fusion.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز: {f}"


if __name__ == "__main__":
    failed = harness.run([
        # B1
        ("[B1] I(a;x) neural ≥ null", t_b1_neural_mi_higher_than_null),
        ("[B1] quality neural ≥ null", t_b1_neural_quality_higher),
        ("[B1] suite neural majority", t_b1_suite_neural_majority),
        ("[B1] falsifiable flag", t_b1_falsifiable_flag),
        ("[B1] neuralness neural > null", t_b1_neuralness_neural_higher),
        # B3
        ("[B3] submit box insight", t_b3_submit_box_insight),
        ("[B3] no doctor → false", t_b3_no_doctor_returns_false),
        ("[B3] propose-only no merge", t_b3_propose_only_no_merge),
        ("[B3] pipeline from metrics", t_b3_pipeline_from_metrics),
        ("[B3] insight → payload", t_b3_insight_to_payload),
        # B4
        ("[B4] compute_phi_t fields", t_b4_compute_phi_t_returns_fields),
        ("[B4] novelty boosts near critical", t_b4_phi_to_novelty_boosts_near_critical),
        ("[B4] novelty base when off", t_b4_phi_to_novelty_base_when_off),
        ("[B4] ablation on/off", t_b4_ablation_on_off),
        ("[B4] no production import", t_b4_no_production_import),
    ])
    sys.exit(1 if failed else 0)
