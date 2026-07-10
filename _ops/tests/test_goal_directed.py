"""test_goal_directed.py — خودبهبودیِ هدف‌محور، ضدِ دایره‌ای (جلسه ۴۶).

پیشنهادِ درخودمانده (بلوغ/probe/سند بدونِ هدف) به ته می‌رود؛ کسب‌وکار/درآمد/هدف بالا؛
نیتِ سنجش ثبت می‌شود و measure می‌گوید آیا برون‌داد واقعاً جابه‌جا شد.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("goal-directed")

import goal_directed as gd   # noqa: E402
import opslib               # noqa: E402


def _goals():
    (opslib.OPS / "GOALS-OCTOPUS.md").write_text(
        "# GOALS\n- درآمد و لیدِ واقعیِ نقاشی و Ziman مقدم بر آزمایش\n"
        "- حافظهٔ ماندگار و یادگیریِ در خدمتِ تصمیم\n", "utf-8")


def t_a_circular_detected_business_not():
    circ = {"title": "بلوغِ ماتریس را بالا ببر", "suggested_action": "یک probe اضافه کن",
            "source": "audit", "priority": "P2"}
    biz = {"title": "Lead-نقاشی: یه لیدِ نو ثبت کن", "source": "business-brain",
           "priority": "P1", "category": "business"}
    p0 = {"title": "امنیت: human-append", "source": "audit", "priority": "P0"}
    assert gd.is_circular(circ) is True
    assert gd.is_circular(biz) is False       # کسب‌وکار هرگز دایره‌ای نیست
    assert gd.is_circular(p0) is False        # P0 امنیت واقعی است


def t_b_impact_business_highest_circular_lowest():
    _goals()
    goals = gd.load_goals()
    biz = {"title": "درآمدِ نقاشی", "source": "business-brain", "category": "business"}
    circ = {"title": "خودآگاهیِ سند", "suggested_action": "docstring بده", "source": "audit", "priority": "P3"}
    assert gd.impact(biz, goals) > gd.impact(circ, goals)
    assert gd.impact(circ, goals) < 1.0


def t_c_rerank_puts_goal_serving_first_drops_circular():
    _goals()
    props = [
        {"title": "بلوغ را بالا ببر", "suggested_action": "probe", "source": "audit", "priority": "P2"},
        {"title": "یک ماژول را مستند کن", "suggested_action": "docstring", "source": "self_model", "priority": "P3"},
        {"title": "Lead-نقاشی: لیدِ نو", "source": "business-brain", "priority": "P1", "category": "business"},
        {"title": "خودآگاهیِ سند ۲", "suggested_action": "توضیح", "source": "audit", "priority": "P3"},
    ]
    r = gd.rerank(props, max_circular=1)
    # اولین = کسب‌وکار (هدف‌محور)
    assert r["ranked"][0]["source"] == "business-brain"
    # فقط ۱ دایره‌ای نگه داشته شد (بقیه drop)
    assert r["n_circular_dropped"] >= 1
    assert all("serves_goal" in p and "impact" in p for p in r["ranked"])


def t_d_record_and_measure_closes_loop():
    """نیتِ سنجش ثبت می‌شود؛ اگر برون‌داد جابه‌جا شد measure=moved."""
    with opslib.LockedJson(opslib.STATE_DIR / "fitness-latest.json") as lj:
        lj.write({"attribution": {"confirmed": 0, "revenue_by_cell": {}}})
    gd.record_intent([{"id": "x", "title": "لیدِ نقاشی", "serves_goal": "درآمد", "impact": 3.0}])
    m0 = gd.measure()
    assert m0["tracked"] >= 1 and m0["moved"] is False       # هنوز جابه‌جا نشده
    # درآمد ثبت شد → measure می‌گوید moved (برون‌دادِ واقعی حرکت کرد)
    with opslib.LockedJson(opslib.STATE_DIR / "fitness-latest.json") as lj:
        lj.write({"attribution": {"confirmed": 3, "revenue_by_cell": {"lead": 500}}})
    assert gd.measure()["moved"] is True


def t_e_improve_run_is_goal_directed():
    """improve.run حالا هدف‌محور است: digest شاملِ goal_directed + top دایره‌ای‌مسلط نیست."""
    _goals()
    import improve
    d = improve.run(write=False, use_local_brain=False)
    assert "goal_directed" in d
    assert "n_goal_serving" in d["goal_directed"] and "outcome" in d["goal_directed"]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_goal_directed: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
