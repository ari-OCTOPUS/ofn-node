#!/usr/bin/env python3
"""تست یکپارچه: Orchestrator + ContentEngine + KPI + ABTracker + Lifecycle ($0)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("pf-full")
_PF = (harness.REAL_VAULT / r"03 - Projects\اونلی فنز")
for _p in [str(_PF), str(_PF/"brain"), str(_PF/"studio"),
           str(_PF.parent/"_ops"/"neural"), str(_PF.parent/"_ops")]:
    if _p not in sys.path: sys.path.insert(0, _p)

# #1 Orchestrator
from orchestrator import PFOrchestrator, TickResult  # noqa: E402

# #2 ContentEngine
from content_engine import ContentEngine, ContentIdea, ScriptScene  # noqa: E402

# #3 KPI
from kpi_dashboard import KPIRenderer  # noqa: E402

# #4 ABTracker
from ab_tracker import ABTestTracker  # noqa: E402

# #5 Lifecycle
from lifecycle import SubscriberLifecycle  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# #1 Orchestrator
# ════════════════════════════════════════════════════════════════════════════════

def t_orch_tick_no_data():
    orch = PFOrchestrator()
    r = orch.tick()
    assert r.advisory_only is True
    assert r.beat == 1
    assert r.mode in ("normal","throttled")

def t_orch_tick_protective():
    orch = PFOrchestrator()
    r = orch.tick(budget={"pct":1.0}, rhythm={"mode_color":"RED","readiness":0.1},
                  sensory={"afferent_ratio":0.01}, spectral={"sigma":1.2})
    assert r.pain > 0.5

def t_orch_tick_normal():
    orch = PFOrchestrator()
    r = orch.tick(rhythm={"mode_color":"GREEN","readiness":0.8,"mode_focus":"STEADY"},
                  sensory={"afferent_ratio":0.5}, spectral={"sigma":0.3},
                  budget={"pct":0.1})
    assert r.mode in ("normal","throttled")
    assert len(r.snapshot) > 0

def t_orch_status():
    orch = PFOrchestrator()
    orch.tick()
    s = orch.status()
    assert "beat" in s and "lambda_persist" in s


# ════════════════════════════════════════════════════════════════════════════════
# #2 ContentEngine
# ════════════════════════════════════════════════════════════════════════════════

def t_engine_generate_10():
    eng = ContentEngine()
    ideas = eng.generate_ideas(tag_performance={"asmr":0.8,"nylon":0.3}, season="summer")
    assert len(ideas) == 10

def t_engine_script():
    eng = ContentEngine()
    ideas = eng.generate_ideas()
    scenes = eng.script_from_idea(ideas[0])
    assert len(scenes) == 3
    assert all(hasattr(s,"angle") for s in scenes)

def t_engine_batch():
    eng = ContentEngine()
    ideas = eng.generate_ideas(count=5)
    plan = eng.batch_plan(ideas)
    assert plan.total_time_min > 0

def t_engine_reuse_5():
    eng = ContentEngine()
    idea = eng.generate_ideas(count=1)[0]
    matrix = eng.reuse_matrix(idea)
    assert len(matrix.targets) == 5

def t_engine_ab_pairs():
    eng = ContentEngine()
    ideas = eng.generate_ideas(count=6)
    pairs = eng.ab_pairs(ideas)
    assert len(pairs) >= 2


# ════════════════════════════════════════════════════════════════════════════════
# #3 KPI Dashboard
# ════════════════════════════════════════════════════════════════════════════════

def t_kpi_html_has_sections():
    r = KPIRenderer().render(
        config={"analytics":{"churn_rate":0.27}, "calendar":{"season":"summer"}},
        acquisition_data={"visitors":200,"subscribers":10,"ppv_buyers":2,
                          "tag_performance":{"asmr":0.8,"nylon":0.3}},
        neural_snap={"rhythm":{"mode_focus":"STEADY","mode_color":"GREEN"},"pain_level":0.1},
        brain_status={"agent_count":10,"last_insight":"price: $15"})
    assert "قیفِ تبدیل" in r and "tag" in r.lower() and "عصبی" in r

def t_kpi_no_pii():
    r = KPIRenderer().render()
    for f in ["name","email","phone","address","ip"]:
        assert f not in r.lower()

def t_kpi_funnel_pct():
    r = KPIRenderer().render(acquisition_data={"visitors":200,"subscribers":10,"ppv_buyers":2})
    assert "5.0%" in r  # 10/200


# ════════════════════════════════════════════════════════════════════════════════
# #4 ABTracker
# ════════════════════════════════════════════════════════════════════════════════

def t_ab_create():
    tr = ABTestTracker(data_path=ENV["ops"]/"ab1.json")
    tid = tr.create_test("test1", {"tag":"asmr"}, {"tag":"nylon"})
    assert tid.startswith("AB-")

def t_ab_record_and_analyze():
    tr = ABTestTracker(data_path=ENV["ops"]/"ab2.json")
    tid = tr.create_test("t", {"tag":"a"}, {"tag":"b"})
    for _ in range(5):
        tr.record_result(tid, "a", upvotes=80, comments=10)
        tr.record_result(tid, "b", upvotes=20, comments=2)
    result = tr.analyze(tid)
    assert result["winner"] == "a"

def t_ab_auto_winner():
    tr = ABTestTracker(data_path=ENV["ops"]/"ab3.json")
    tid = tr.create_test("t", {"tag":"a"}, {"tag":"b"})
    for _ in range(5):
        tr.record_result(tid, "a", upvotes=90)
        tr.record_result(tid, "b", upvotes=10)
    w = tr.auto_winner(tid)
    assert w == "a"

def t_ab_persists():
    p = ENV["ops"]/"ab4.json"
    tr1 = ABTestTracker(data_path=p)
    tr1.create_test("persist", {"x":1},{"y":2})
    tr2 = ABTestTracker(data_path=p)
    assert len(tr2.tests) >= 1


# ════════════════════════════════════════════════════════════════════════════════
# #5 Lifecycle
# ════════════════════════════════════════════════════════════════════════════════

def t_lifecycle_track():
    lc = SubscriberLifecycle(data_path=ENV["ops"]/"lc1.json")
    lc.track("W1", total=10, new_count=5, churned_count=1)
    assert lc.period_count >= 1

def t_lifecycle_churn_rate():
    lc = SubscriberLifecycle(data_path=ENV["ops"]/"lc2.json")
    lc.track("W1", total=10, new_count=5, churned_count=2)
    lc.track("W2", total=13, new_count=5, churned_count=2)
    assert lc.churn_rate() > 0

def t_lifecycle_predict():
    lc = SubscriberLifecycle(data_path=ENV["ops"]/"lc3.json")
    lc.track("W1", total=20, churned_count=5)
    lc.track("W2", total=15, churned_count=8)
    pred = lc.predict_at_risk()
    assert "at_risk_pct" in pred and "trend" in pred

def t_lifecycle_win_back():
    lc = SubscriberLifecycle(data_path=ENV["ops"]/"lc4.json")
    lc.track("W1", total=10, churned_count=5)
    strategies = lc.win_back_strategy()
    assert len(strategies) >= 1

def t_lifecycle_no_pii():
    lc = SubscriberLifecycle(data_path=ENV["ops"]/"lc5.json")
    lc.track("W1", total=10)
    for p in lc.history:
        for f in ["name","email","phone","user_id","subscriber_name"]:
            assert f not in str(p).lower()


if __name__ == "__main__":
    failed = harness.run([
        # #1
        ("[O] tick no data", t_orch_tick_no_data),
        ("[O] tick protective", t_orch_tick_protective),
        ("[O] tick normal", t_orch_tick_normal),
        ("[O] status", t_orch_status),
        # #2
        ("[CE] generate 10", t_engine_generate_10),
        ("[CE] script", t_engine_script),
        ("[CE] batch", t_engine_batch),
        ("[CE] reuse 5", t_engine_reuse_5),
        ("[CE] ab pairs", t_engine_ab_pairs),
        # #3
        ("[K] html sections", t_kpi_html_has_sections),
        ("[K] no PII", t_kpi_no_pii),
        ("[K] funnel pct", t_kpi_funnel_pct),
        # #4
        ("[AB] create", t_ab_create),
        ("[AB] analyze", t_ab_record_and_analyze),
        ("[AB] auto winner", t_ab_auto_winner),
        ("[AB] persists", t_ab_persists),
        # #5
        ("[L] track", t_lifecycle_track),
        ("[L] churn rate", t_lifecycle_churn_rate),
        ("[L] predict", t_lifecycle_predict),
        ("[L] win-back", t_lifecycle_win_back),
        ("[L] no PII", t_lifecycle_no_pii),
    ])
    sys.exit(1 if failed else 0)
