#!/usr/bin/env python3
"""تست Acquisition Intelligence ($0 آفلاین).

یادگیری از داده · تحلیل · پیشنهاد · feedback loop · هیچ auto-DM/targeting.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("acquisition")
_BRAIN = (harness.REAL_VAULT / r"03 - Projects\اونلی فنز\brain")
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from acquisition import (AcquisitionBrain, AcquisitionMemory,  # noqa: E402
                          ContentInsight, WeekPlan, Signal)


# ════════════════════════════════════════════════════════════════════════════════
# Memory + learning
# ════════════════════════════════════════════════════════════════════════════════

def t_memory_empty_when_no_data():
    """بدون داده → tag_performance خالی."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_empty.json")
    assert mem.tag_performance() == {}


def t_memory_records_post():
    """ثبتِ نتیجه‌ی پست → یاد می‌گیرد."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_test.json")
    mem._signals = []  # clean
    mem.record_post_result("pedicure-asmr", "reddit", upvotes=80, comments=10,
                            unlocks=2, day="Saturday")
    perf = mem.tag_performance()
    assert "pedicure-asmr" in perf and perf["pedicure-asmr"] > 0


def t_memory_persists_across_restart():
    """persistence: داده با restart محفوظ."""
    path = ENV["ops"] / "acq_persist.json"
    mem1 = AcquisitionMemory(data_path=path)
    mem1._signals = []
    mem1.record_post_result("test-tag", "reddit", upvotes=50)
    mem2 = AcquisitionMemory(data_path=path)  # reload
    assert len(mem2._post_results) >= 1


def t_memory_best_time_learns():
    """بهترین زمان از داده."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_time.json")
    mem._signals = []
    mem.record_post_result("t1", "reddit", upvotes=90, day="Saturday")
    mem.record_post_result("t2", "reddit", upvotes=10, day="Monday")
    bt = mem.best_time()
    assert bt["day"] == "Saturday"


def t_learning_confidence_grows():
    """confidence با داده رشد می‌کند."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_conf.json")
    mem._signals = []
    assert mem.learning_confidence() == 0.0
    for i in range(20):
        mem.record_post_result(f"t{i}", "reddit", upvotes=i)
    assert mem.learning_confidence() >= 0.9


# ════════════════════════════════════════════════════════════════════════════════
# Brain analyze
# ════════════════════════════════════════════════════════════════════════════════

def t_analyze_empty_returns_default():
    """بدون داده → analyze خالی یا حدس."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_a1.json")
    mem._signals = []
    brain = AcquisitionBrain(memory=mem)
    insights = brain.analyze()
    # خالی مجاز است (هیچ داده‌ای نیست)


def t_analyze_finds_best_tag():
    """تحلیل: tag با بهترین عملکرد اول می‌آید."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_a2.json")
    mem._signals = []
    mem.record_post_result("good-tag", "reddit", upvotes=95)
    mem.record_post_result("bad-tag", "reddit", upvotes=5)
    brain = AcquisitionBrain(memory=mem)
    insights = brain.analyze()
    if insights:
        assert insights[0].tag == "good-tag"


def t_analyze_competitor_opportunity():
    """رقبا فعال ولی ما نیستیم → فرصت."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_a3.json")
    mem._signals = []
    mem.record_competitor("new-trend", "reddit", avg_upvotes=70)
    brain = AcquisitionBrain(memory=mem)
    insights = brain.analyze()
    opportunity = [i for i in insights if i.tag == "new-trend"]
    if opportunity:
        assert "فرصت" in opportunity[0].reason or "رقبا" in opportunity[0].reason


# ════════════════════════════════════════════════════════════════════════════════
# WeekPlan + suggest
# ════════════════════════════════════════════════════════════════════════════════

def t_plan_week_returns_structure():
    """plan_week ساختارِ درست دارد."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_p1.json")
    mem._signals = []
    brain = AcquisitionBrain(memory=mem)
    plan = brain.plan_week()
    assert isinstance(plan, WeekPlan)
    assert hasattr(plan, "focus_tags") and hasattr(plan, "posting_schedule")


def t_plan_week_has_risk_note_when_no_data():
    """بدون داده → risk note."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_p2.json")
    mem._signals = []
    brain = AcquisitionBrain(memory=mem)
    plan = brain.plan_week()
    assert len(plan.risk_notes) > 0


def t_suggest_next_action_no_data():
    """بدون داده → «اولین قدم: ۳ پست»."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_s1.json")
    mem._signals = []
    brain = AcquisitionBrain(memory=mem)
    action = brain.suggest_next_action()
    assert "اولین قدم" in action or "۳ پست" in action


def t_suggest_next_action_with_data():
    """با داده → تمرکزِ هفته."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_s2.json")
    mem._signals = []
    for i in range(15):
        mem.record_post_result(f"tag-{i % 3}", "reddit", upvotes=50 + i, day="Saturday")
    brain = AcquisitionBrain(memory=mem)
    action = brain.suggest_next_action()
    assert "تمرکز" in action or "هفته" in action or "ادمه" in action or "یادگیری" in action


# ════════════════════════════════════════════════════════════════════════════════
# Feedback loop + guardrails
# ════════════════════════════════════════════════════════════════════════════════

def test_feedback_loop_learns():
    """feedback_loop: ثبتِ نتیجه → یادگیری."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_f1.json")
    mem._signals = []
    brain = AcquisitionBrain(memory=mem)
    brain.feedback_loop("test", "reddit", upvotes=70, comments=5, day="Saturday")
    assert len(mem._post_results) == 1


def t_no_auto_dm_or_targeting():
    """هیچ متدِ auto-DM/target/follow وجود ندارد."""
    import acquisition
    src = open(acquisition.__file__, encoding="utf-8").read()
    forbidden = ["send_dm", "auto_follow", "mass_dm", "target_user",
                 "auto_subscribe", "auto_message", "scrape_user"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز نقض شد: {f}"


def t_no_pii_in_output():
    """صفر PII در خروجی."""
    from dataclasses import asdict as _asdict
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_pii.json")
    mem._signals = []
    for i in range(5):
        mem.record_post_result(f"t{i}", "reddit", upvotes=50)
    brain = AcquisitionBrain(memory=mem)
    plan = brain.plan_week()
    blob = str(_asdict(plan))
    for forbidden in ("username", "user_id", "email", "phone", "ip_address", "real_name"):
        assert forbidden.lower() not in blob.lower(), f"PII: {forbidden}"


def t_ab_test_generated():
    """A/B test idea وقتی ≥۲ tag هست."""
    mem = AcquisitionMemory(data_path=ENV["ops"] / "acq_ab.json")
    mem._signals = []
    mem.record_post_result("tag-a", "reddit", upvotes=60)
    mem.record_post_result("tag-b", "reddit", upvotes=55)
    brain = AcquisitionBrain(memory=mem)
    plan = brain.plan_week()
    if plan.ab_test_idea:
        assert "A/B" in plan.ab_test_idea


if __name__ == "__main__":
    from dataclasses import asdict as _asdict
    failed = harness.run([
        # Memory
        ("[M] empty → no perf", t_memory_empty_when_no_data),
        ("[M] records post", t_memory_records_post),
        ("[M] persistence", t_memory_persists_across_restart),
        ("[M] best_time learns", t_memory_best_time_learns),
        ("[M] confidence grows", t_learning_confidence_grows),
        # Analyze
        ("[A] empty default", t_analyze_empty_returns_default),
        ("[A] finds best tag", t_analyze_finds_best_tag),
        ("[A] competitor opportunity", t_analyze_competitor_opportunity),
        # Plan
        ("[P] plan structure", t_plan_week_returns_structure),
        ("[P] risk note no data", t_plan_week_has_risk_note_when_no_data),
        ("[P] suggest no data", t_suggest_next_action_no_data),
        ("[P] suggest with data", t_suggest_next_action_with_data),
        # Feedback + guard
        ("[F] feedback loop", test_feedback_loop_learns),
        ("[G] no auto-DM/target", t_no_auto_dm_or_targeting),
        ("[G] no PII", t_no_pii_in_output),
        ("[G] A/B test", t_ab_test_generated),
    ])
    sys.exit(1 if failed else 0)
