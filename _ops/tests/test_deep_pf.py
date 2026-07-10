#!/usr/bin/env python3
"""تست عمیق: DualBrain v3 + Studio Telegram v3 + Neural Driver ($0)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("deep-pf")
_PF = (harness.REAL_VAULT / r"03 - Projects\اونلی فنز")
_NEURAL = (harness.REAL_VAULT / r"_ops\neural")
for _p in (str(_PF / "brain"), str(_PF / "studio"), str(_NEURAL)):
    if _p not in sys.path: sys.path.insert(0, _p)

from dual_brain_v3 import (DualBrainV3, ThinkingBrain, CommBrain, Thought,  # noqa: E402
                            LAMBDA_PERSIST, COMPLIANCE_RULES, ETHICS_RULES, _guard_text)
from studio_telegram_v3 import StudioTelegramV3, MAIN_MENU, BACK_KB  # noqa: E402
from neural_driver import NeuralDriver  # noqa: E402
from content_studio import ContentStudio, COMPLIANCE_CHECKS  # noqa: E402


def _checks():
    return {**{r: True for r in COMPLIANCE_RULES}, **{r: True for r in ETHICS_RULES}}


# ════════════════════════════════════════════════════════════════════════════════
# ThinkingBrain — ۱۰ agents
# ════════════════════════════════════════════════════════════════════════════════

def t_10_agents_all_present():
    tb = ThinkingBrain()
    thoughts = tb.process_all(checks=_checks())
    agents = [t.source_agent for t in thoughts]
    expected = ["Strategist","Pricer","Scheduler","RiskAnalyzer","Segmenter",
                "CompetitorIntel","TrendForecaster","RetentionStrategist",
                "ContentOptimizer","FunnelAnalyst"]
    for a in expected:
        assert a in agents, f"missing agent: {a}. got: {agents}"


def t_pricer_learns_from_history():
    tb = ThinkingBrain(historical=[{"type":"price","outcome":"approved","price":25}])
    t = tb.pricer()
    assert t.data["base"] >= 15  # moved toward 25


def test_competitor_intel_with_data():
    tb = ThinkingBrain()
    t = tb.competitor_intel([{"tag":"asmr","avg_upvotes":80},{"tag":"nylon","avg_upvotes":30}])
    hot = t.data.get("hot_tags",{})
    assert "asmr" in hot and hot["asmr"] > hot["nylon"]


def test_trend_forecaster_seasonal():
    tb = ThinkingBrain()
    t = tb.trend_forecaster("winter")
    assert "fuzzy-socks" in t.data["predicted_trends"]


def test_funnel_analyst_bottleneck():
    tb = ThinkingBrain()
    t = tb.funnel_analyst(visitors=200, subscribers=3, ppv_buyers=0)
    assert len(t.data["bottlenecks"]) >= 1


def test_content_optimizer_with_history():
    tb = ThinkingBrain(historical=[
        {"type":"post","tag":"good","upvotes":80,"comments":10},
        {"type":"post","tag":"bad","upvotes":5,"comments":0}])
    t = tb.content_optimizer()
    assert t.data["best_tag"] == "good" and t.data["worst_tag"] == "bad"


def test_retention_strategist_high_churn():
    tb = ThinkingBrain()
    t = tb.retention_strategist(churn_rate=0.4)
    assert any("increase wall" in a["action"] for a in t.data["actions"])


# ════════════════════════════════════════════════════════════════════════════════
# CommBrain — ۷ outputs
# ════════════════════════════════════════════════════════════════════════════════

def test_comm_7_types():
    cb = CommBrain()
    thought = Thought(kind="price", data={"tier":"mid"})
    types = [cb.caption(thought).kind, cb.dm_draft(thought).kind,
             cb.retention_dm("vip").kind, cb.ab_announcement("a","b").kind,
             cb.trend_note(["x"]).kind]
    assert "caption" in types and "dm" in types and "retention_dm" in types


def test_comm_brief_has_all_insights():
    db = DualBrainV3()
    r = db.think_and_communicate(checks=_checks())
    brief = next((m for m in r["messages"] if m["kind"]=="brief_saba"), None)
    assert brief and "بریف" in brief["text"]


def test_comm_report_has_funnel():
    db = DualBrainV3()
    r = db.think_and_communicate(checks=_checks(), visitors=200, subscribers=3)
    report = next((m for m in r["messages"] if m["kind"]=="report_ari"), None)
    assert report and "تبدیل" in report["text"]


# ════════════════════════════════════════════════════════════════════════════════
# DualBrainV3 integration
# ════════════════════════════════════════════════════════════════════════════════

def test_dual_blocked():
    db = DualBrainV3()
    r = db.think_and_communicate(checks={})
    assert r["blocked"] is True


def test_dual_all_human_gated():
    db = DualBrainV3()
    r = db.think_and_communicate(checks=_checks())
    assert all(m["human_gated"] for m in r["messages"])


def test_dual_no_forbidden():
    db = DualBrainV3()
    r = db.think_and_communicate(checks=_checks(), competitor_data=[{"tag":"x","avg_upvotes":50}])
    for m in r["messages"]:
        passed, violations = _guard_text(m["text"])
        assert passed, f"forbidden in {m['kind']}: {violations}"


# ════════════════════════════════════════════════════════════════════════════════
# Studio Telegram v3
# ════════════════════════════════════════════════════════════════════════════════

def test_studio_v3_menu():
    st = StudioTelegramV3()
    assert "inline_keyboard" in MAIN_MENU
    text = st.handle_command("/start")
    assert text and "استودیوی" in text


def test_studio_v3_callback_view():
    st = StudioTelegramV3()
    text, kb = st.dispatch_callback("m:drafts")
    assert text is not None and kb == BACK_KB


def test_studio_v3_callback_submit():
    st = StudioTelegramV3()
    text, kb = st.dispatch_callback("m:submit")
    assert text and "ثبت" in text


def test_studio_v3_callback_menu():
    st = StudioTelegramV3()
    text, kb = st.dispatch_callback("m:menu")
    assert text and kb == MAIN_MENU


def test_studio_v3_callback_back():
    st = StudioTelegramV3()
    text, kb = st.dispatch_callback("m:drafts")
    assert "↩️" in kb["inline_keyboard"][0][0]["text"]


def test_studio_v3_unknown_quarantine():
    st = StudioTelegramV3()
    assert st.handle_command("/unknown_cmd") is None


def test_studio_v3_halt():
    st = StudioTelegramV3()
    r = st.handle_command("/halt")
    assert "متوقف" in r
    assert st._studio.is_halted


def test_studio_v3_not_wired():
    st = StudioTelegramV3(token="", saba_chat_id=None)
    assert st.wired is False
    assert st.send("test") is False


# ════════════════════════════════════════════════════════════════════════════════
# Neural Driver
# ════════════════════════════════════════════════════════════════════════════════

def test_neural_driver_snapshot_to_inputs():
    nd = NeuralDriver()
    inputs = nd.snapshot_to_brain_inputs({"pain_level":0.8, "rhythm":{"readiness":0.9},
        "spectral":{"sigma":0.95}, "sensory":{"afferent_ratio":0.05}, "budget":{"pct":0.9}})
    assert inputs["partner_stress"] > 0.5
    assert inputs["throttle_brain"] is True
    assert inputs["data_confidence"] < 0.1
    assert inputs["advisory_only"] is True


def test_neural_driver_evaluate():
    nd = NeuralDriver()
    result = nd.evaluate(beat=1,
        rhythm={"mode_color":"RED","readiness":0.3,"mode_focus":"CALM"},
        sensory={"afferent_ratio":0.05},
        spectral={"sigma":0.95},
        budget={"pct":0.9})
    assert "snapshot" in result and "pain" in result and "reflexes" in result
    assert result["pain"]["level"] > 0.3  # باید درد داشته باشد
    assert any(r["triggered"] for r in result["reflexes"])
    assert result["brain_inputs"]["advisory_only"] is True


def test_neural_driver_no_effect():
    nd = NeuralDriver()
    result = nd.evaluate(beat=1)
    for r in result["reflexes"]:
        assert r["action"] in ("throttle","slow","pause","alarm","none")


# ════════════════════════════════════════════════════════════════════════════════
# Guards
# ════════════════════════════════════════════════════════════════════════════════

def test_lambda_persist():
    assert LAMBDA_PERSIST == -1.0


def test_no_auto_dm_in_studio():
    import studio_telegram_v3
    src = open(studio_telegram_v3.__file__, encoding="utf-8").read()
    for f in ["send_dm","auto_follow","mass_dm","target_user"]:
        assert f not in src


if __name__ == "__main__":
    failed = harness.run([
        # 10 agents
        ("[T] ۱۰ agent", t_10_agents_all_present),
        ("[T] pricer learns", t_pricer_learns_from_history),
        ("[T] competitor intel", test_competitor_intel_with_data),
        ("[T] trend seasonal", test_trend_forecaster_seasonal),
        ("[T] funnel bottleneck", test_funnel_analyst_bottleneck),
        ("[T] content optimizer", test_content_optimizer_with_history),
        ("[T] retention high churn", test_retention_strategist_high_churn),
        # 7 comm
        ("[C] ۷ type", test_comm_7_types),
        ("[C] brief all insights", test_comm_brief_has_all_insights),
        ("[C] report funnel", test_comm_report_has_funnel),
        # dual
        ("[D] blocked", test_dual_blocked),
        ("[D] human-gated", test_dual_all_human_gated),
        ("[D] no forbidden", test_dual_no_forbidden),
        # studio v3
        ("[S] menu", test_studio_v3_menu),
        ("[S] callback view", test_studio_v3_callback_view),
        ("[S] callback submit", test_studio_v3_callback_submit),
        ("[S] callback menu", test_studio_v3_callback_menu),
        ("[S] callback back", test_studio_v3_callback_back),
        ("[S] unknown quarantine", test_studio_v3_unknown_quarantine),
        ("[S] halt", test_studio_v3_halt),
        ("[S] not wired", test_studio_v3_not_wired),
        # neural driver
        ("[N] snapshot→inputs", test_neural_driver_snapshot_to_inputs),
        ("[N] evaluate", test_neural_driver_evaluate),
        ("[N] no effect", test_neural_driver_no_effect),
        # guards
        ("[G] λ_persist", test_lambda_persist),
        ("[G] no auto-DM", test_no_auto_dm_in_studio),
    ])
    sys.exit(1 if failed else 0)
