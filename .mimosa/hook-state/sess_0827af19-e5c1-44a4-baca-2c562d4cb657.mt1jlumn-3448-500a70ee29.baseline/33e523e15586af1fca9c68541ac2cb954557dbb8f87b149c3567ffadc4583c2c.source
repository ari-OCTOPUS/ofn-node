# tests/test_hypothesis_brain.py — ۸ تستِ اجباریِ spec §5 + پوششِ فرمول/گذار/purity
#
# اجرا:  py -m pytest _ops/hypothesis_engine/tests/test_hypothesis_brain.py -q
import asyncio
import math
import sys
from pathlib import Path

import pytest

# (در کنار conftest.py) برای اجرایِ مستقل هم مسیر را تضمین کن:
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "impl"))

from base_brain import BrainError  # noqa: E402
from hypothesis_brain import (  # noqa: E402
    ALLOWED_TRANSITIONS,
    HypothesisBrain,
    PURSUE_THRESHOLD,
    pursue_score,
)
from schemas import (  # noqa: E402
    GRADE_WEIGHTS,
    EvidenceGrade,
    HypothesisRecord,
    HypothesisStatus,
    logit,
    sigmoid,
)


def run(coro):
    return asyncio.run(coro)


def _drive(coro):
    """کوروتین را بدون event loop پیش ببر (برای تستِ purity).
    execute هرگز await نمی‌کند ⇒ باید همگام تمام شود. این از ساختِ
    event loop (که روی ویندوز socket می‌زند) جلوگیری می‌کند تا بتوانیم
    socket را واقعاً مسدود کنیم و فقط مغز را بیازماییم."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value
    raise AssertionError("execute همگام تمام نشد — چیزی را await کرده است")


def _propose(b: HypothesisBrain, **kw) -> dict:
    payload = {"statement": "x"}
    payload.update(kw)
    return run(b.execute({"op": "propose", **payload}))


# ---------------------------------------------------------------------------
# تست ۱ — فرضیهٔ آزمون‌ناپذیر با usefulness بالا («X is AGI») باید reject شود
# ---------------------------------------------------------------------------
def test_1_untestable_high_usefulness_rejected():
    b = HypothesisBrain()
    out = _propose(b, statement="Octopus is AGI",
                   p_existence=0.5, p_usefulness=0.95,
                   testability=0.0, eig=0.0, cost_hours=None)
    assert out["verdict"] == "reject"
    assert out["reject_reason"] is not None
    assert "testability" in out["reject_reason"]


# ---------------------------------------------------------------------------
# تست ۲ — فرضیهٔ کم‌احتمال ولی پرارزش باید pursue شود
# ---------------------------------------------------------------------------
def test_2_low_probability_high_value_pursued():
    b = HypothesisBrain()
    out = _propose(b, statement="الگوی (2E,1N)x3 راهروی پنهان باز می‌کند",
                   p_existence=0.08, p_usefulness=0.82,
                   testability=0.9, eig=0.7, cost_hours=0.5,
                   value_if_true=2.0)
    assert out["verdict"] == "pursue"
    assert out["proposal"]["priority_score"] >= PURSUE_THRESHOLD


# ---------------------------------------------------------------------------
# تست ۳ — update بدون evidence_id باید BrainError recoverable=False بدهد
# ---------------------------------------------------------------------------
def test_3_update_without_evidence_id_raises_hard():
    b = HypothesisBrain()
    rec = _propose(b, testability=0.5)["proposal"]["record"]
    with pytest.raises(BrainError) as ei:
        run(b.execute({"op": "update", "hypothesis": rec,
                       "grade": "C", "direction": "support"}))
    assert ei.value.recoverable is False


# ---------------------------------------------------------------------------
# تست ۴ — ۲ شاهد A موافق + ۱ D مخالف ⇒ p_e صعودیِ خالص
# ---------------------------------------------------------------------------
def test_4_belief_update_net_upward_after_2A_1D():
    b = HypothesisBrain()
    rec = _propose(b, p_existence=0.2, testability=0.8, eig=0.4)["proposal"]["record"]
    p0 = rec["existence_probability"]
    for i in range(2):
        rec = run(b.execute({"op": "update", "hypothesis": rec, "grade": "A",
                             "direction": "support", "evidence_id": f"a{i}"}))["hypothesis"]
    rec = run(b.execute({"op": "update", "hypothesis": rec, "grade": "D",
                         "direction": "contradict", "evidence_id": "d0"}))["hypothesis"]
    p1 = rec["existence_probability"]
    assert p1 > p0
    # بررسیِ ریاضی: log-odds خطی است ⇒ net = sigmoid(logit(p0) + 2·w_A − w_D)
    expected = sigmoid(logit(p0) + 2 * GRADE_WEIGHTS[EvidenceGrade.A]
                       - GRADE_WEIGHTS[EvidenceGrade.D])
    assert abs(p1 - expected) < 1e-9


# ---------------------------------------------------------------------------
# تست ۵ (§5 spec) — در commit ۲ (test_validate_registry.py) покрыт می‌شود
# (kill_condition ناقص در TESTING ⇒ validator exit=1)
# ---------------------------------------------------------------------------
# → این‌جا مستثنی؛ فایلِ جداگانه.


# ---------------------------------------------------------------------------
# تست ۶ — فرمولِ pursue_score دقیقاً
# ---------------------------------------------------------------------------
def test_6_pursue_score_formula_exact():
    h = HypothesisRecord(id="H", statement="s", existence_probability=0.2,
                         usefulness_probability=0.8, testability=0.75,
                         cost_of_testing_hours=2.0, expected_information_gain=0.5)
    # p_e·V + EIG + u·0.5 + u_o − c/4 − (1−testability)
    expected = (0.2 * 3.0) + 0.5 + (0.8 * 0.5) + 0.1 - (2.0 / 4.0) - (1.0 - 0.75)
    assert abs(pursue_score(h, value_if_true=3.0, option_value=0.1) - expected) < 1e-12


# ---------------------------------------------------------------------------
# تست ۷ — قاعدهٔ سخت testability==0 حتی با score بالا reject می‌کند
# ---------------------------------------------------------------------------
def test_7_testability_hard_floor_overrides_score():
    b = HypothesisBrain()
    # یک فرضیهٔ کاملاً مفید ولی آزمون‌ناپذیر
    out = _propose(b, statement="everything is consciousness",
                   p_existence=0.99, p_usefulness=0.99,
                   testability=0.0, eig=0.99, cost_hours=0.1,
                   value_if_true=5.0)
    assert out["verdict"] == "reject"
    assert "testability" in (out["reject_reason"] or "")


# ---------------------------------------------------------------------------
# تست ۸ — prioritize با سقفِ MAX_ACTIVE (=20)
# ---------------------------------------------------------------------------
def test_8_prioritize_caps_at_max_active():
    b = HypothesisBrain()
    hyps = [{
        "id": f"HYP-{i:02d}", "statement": f"stmt {i}", "status": "SPECULATIVE",
        "existence_probability": round(i / 30.0, 3),  # امتیاز صعودی
        "usefulness_probability": 0.5, "testability": 0.8,
        "expected_information_gain": 0.4,
    } for i in range(25)]
    out = run(b.execute({"op": "prioritize", "hypotheses": hyps}))
    assert out["status"] == "completed"
    assert len(out["ranked"]) == 20
    assert out["overflow_count"] == 5
    prios = [r["priority"] for r in out["ranked"]]
    assert prios == sorted(prios, reverse=True)
    assert out["ranked"][0]["id"] == "HYP-24"   # بالاترین p_e


# ---------------------------------------------------------------------------
# تست ۹ — op ناشناخته ⇒ BrainError recoverable=False
# ---------------------------------------------------------------------------
def test_9_unknown_op_raises_hard():
    b = HypothesisBrain()
    with pytest.raises(BrainError) as ei:
        run(b.execute({"op": "frobnicate"}))
    assert ei.value.recoverable is False


# ---------------------------------------------------------------------------
# تست ۱۰ — direction نامعتبر ⇒ BrainError recoverable=False
# ---------------------------------------------------------------------------
def test_10_invalid_direction_raises_hard():
    b = HypothesisBrain()
    rec = _propose(b, testability=0.5)["proposal"]["record"]
    with pytest.raises(BrainError) as ei:
        run(b.execute({"op": "update", "hypothesis": rec, "grade": "C",
                       "direction": "sideways", "evidence_id": "e1"}))
    assert ei.value.recoverable is False


# ---------------------------------------------------------------------------
# تست ۱۱ — گذار خودکار TESTING → EVIDENCED وقتی p_e ≥ 0.7
# ---------------------------------------------------------------------------
def test_11_auto_transition_to_evidenced():
    b = HypothesisBrain()
    base = _propose(b, p_existence=0.6, testability=0.9, eig=0.5,
                    cost_hours=1.0)["proposal"]["record"]
    base["status"] = "TESTING"   # شبیه‌سازیِ تأییدِ مالک برای ورود به TESTING
    out = run(b.execute({"op": "update", "hypothesis": base, "grade": "A",
                         "direction": "support", "evidence_id": "strong-1"}))
    assert out["hypothesis"]["status"] == "EVIDENCED"
    assert out["update"]["transitioned"] is True


# ---------------------------------------------------------------------------
# تست ۱۲ — گذار خودکار TESTING → FALSIFIED وقتی p_e ≤ 0.15
# ---------------------------------------------------------------------------
def test_12_auto_transition_to_falsified():
    b = HypothesisBrain()
    base = _propose(b, p_existence=0.2, testability=0.9, eig=0.5,
                    cost_hours=1.0)["proposal"]["record"]
    base["status"] = "TESTING"
    out = run(b.execute({"op": "update", "hypothesis": base, "grade": "A",
                         "direction": "contradict", "evidence_id": "killer-1"}))
    assert out["hypothesis"]["status"] == "FALSIFIED"
    assert out["update"]["transitioned"] is True


# ---------------------------------------------------------------------------
# تست ۱۳ — purity: execute بدون IO/شبکه (monkeypatch)
# ---------------------------------------------------------------------------
def test_13_purity_no_io_no_network(monkeypatch):
    import socket as _sock
    import urllib.request as _url

    def _no_net(*a, **k):
        raise AssertionError("HypothesisBrain نباید شبکه را لمس کند")
    monkeypatch.setattr(_sock, "socket", _no_net)
    monkeypatch.setattr(_url, "urlopen", _no_net)

    b = HypothesisBrain()
    out = _drive(b.execute({"op": "propose", "statement": "x", "testability": 0.5}))
    assert out["status"] == "completed"
    rec = out["proposal"]["record"]
    out2 = _drive(b.execute({"op": "update", "hypothesis": rec, "grade": "B",
                             "direction": "support", "evidence_id": "e1"}))
    assert out2["status"] == "completed"
    out3 = _drive(b.execute({"op": "prioritize", "hypotheses": [rec]}))
    assert out3["status"] == "completed"


# ---------------------------------------------------------------------------
# تست ۱۴ — evidence_id به evidence_ids افزوده و شمارش می‌شود (بدون تکرار)
# ---------------------------------------------------------------------------
def test_14_evidence_id_appended_and_counted():
    b = HypothesisBrain()
    rec = _propose(b, p_existence=0.3, testability=0.7, eig=0.3)["proposal"]["record"]
    out = run(b.execute({"op": "update", "hypothesis": rec, "grade": "B",
                         "direction": "support", "evidence_id": "ev-001"}))
    h = out["hypothesis"]
    assert "ev-001" in h["evidence_ids"]
    assert h["supporting_evidence_count"] == 1
    # دوباره با همان id → بدون تکرار
    out2 = run(b.execute({"op": "update", "hypothesis": h, "grade": "B",
                          "direction": "support", "evidence_id": "ev-001"}))
    h2 = out2["hypothesis"]
    assert h2["evidence_ids"].count("ev-001") == 1
    assert h2["supporting_evidence_count"] == 2


# ---------------------------------------------------------------------------
# تست ۱۵ — rationale برای هر دو verdict غیرتهی است
# ---------------------------------------------------------------------------
def test_15_rationale_nonempty_for_both_verdicts():
    b = HypothesisBrain()
    rej = _propose(b, statement="AGI", testability=0.0)["proposal"]
    pur = _propose(b, statement="corridor", p_existence=0.1, testability=0.9,
                   eig=0.7, value_if_true=2.0)["proposal"]
    assert rej["verdict"] == "reject" and rej["rationale"]
    assert pur["verdict"] == "pursue" and pur["rationale"]


# ---------------------------------------------------------------------------
# تست ۱۶ — can_transition / چرخهٔ عمر: حالت‌های نهایی بی‌خروج‌اند
# ---------------------------------------------------------------------------
def test_16_terminal_states_have_no_exits():
    assert ALLOWED_TRANSITIONS[HypothesisStatus.FALSIFIED] == set()
    assert ALLOWED_TRANSITIONS[HypothesisStatus.ARCHIVED] == set()
    assert HypothesisBrain.can_transition(HypothesisStatus.TESTING,
                                          HypothesisStatus.EVIDENCED) is True
    assert HypothesisBrain.can_transition(HypothesisStatus.FALSIFIED,
                                          HypothesisStatus.TESTING) is False
