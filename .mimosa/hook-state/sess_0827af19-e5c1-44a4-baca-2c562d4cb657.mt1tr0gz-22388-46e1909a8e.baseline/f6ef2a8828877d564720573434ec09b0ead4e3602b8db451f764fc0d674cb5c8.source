# -*- coding: utf-8 -*-
"""آزمون دو رکن (فاز ۳) — کل جریان با gateway فیک، بدون شبکه."""
from adapters.business import ALL, engines_for
from adapters.business.base import parse_brief
from core.contracts import Feedback
from core.memory import Memory


class FakeGW:
    def __init__(self, llm_out=None):
        self.searches = []
        self.llm_out = llm_out or ("عنوان: باکس هدیه شرکتی\nفرصت: شرکت‌های سیدنی برای عید سفارش گروهی می‌دهند\n"
                                   "چرا: فصل مناسبتی نزدیک است\nاقدام: تماس با ۳ دفتر محلی\nمنبع: https://example.com")

    def search(self, q, business="", n=5):
        self.searches.append(q)
        return [{"title": "t1", "url": "u1", "content": "محتوا"}]

    def llm(self, prompt, system="", tier="cheap", business="", max_tokens=900, use_cache=True):
        return self.llm_out


def test_parse_brief_full_and_fallback(td):
    b = parse_brief("ziman", "عنوان: تست\nفرصت: ف\nچرا: چ\nاقدام: الف\nمنبع: م")
    assert b.title == "تست" and b.action == "الف" and b.source == "م"
    b2 = parse_brief("ziman", "فقط یک متن آزاد بدون قالب")
    assert b2.title and b2.source == "تحلیل داخلی"     # fallback امن


def test_registry_covers_three_businesses(td):
    assert set(ALL.keys()) == {"ziman", "painting", "accounting"}


def test_full_cycle_per_business(td):
    m = Memory(td / "core.db")
    gw = FakeGW()
    for biz in ALL:
        research, owner = engines_for(biz, gw, m)
        brief = research.run(research.gather_context())
        assert brief.id is not None and brief.business == biz
        msg = owner.compose(brief)
        assert msg.to_ref and msg.status == "pending" and msg.brief_id == brief.id
        m.add_outbox(msg)
    st = m.stats()
    assert st["briefs"] == 3 and st["pending"] == 3
    # هر تحقیق باید وب را دیده باشد
    assert len(gw.searches) == 3


def test_learn_changes_topic_weights(td):
    m = Memory(td / "core.db")
    gw = FakeGW()
    research, _ = engines_for("ziman", gw, m)
    t0 = research._pick_topic()
    bid = m.add_brief(parse_brief("ziman", "عنوان: x\nفرصت: f\nچرا: c\nاقدام: a\nمنبع: s"))
    research.learn([Feedback(brief_id=bid, useful=False)] * 3)     # سه بار 👎
    w = research._weights()
    assert w and min(w.values()) <= -3                              # وزن موضوع فعلی منفی شد
    assert isinstance(t0, str) and t0


def test_ziman_discover_occasions(td):
    m = Memory(td / "core.db")
    _, owner = engines_for("ziman", FakeGW(), m)
    msgs = owner.discover()
    # بسته به ماه ممکن است ۰..۲ مناسبت نزدیک باشد؛ ساختار هرچه بود باید سالم باشد
    for msg in msgs:
        assert msg.business == "ziman" and msg.to_ref == "mom" and msg.status == "pending"


def test_offline_compose_fallback(td):
    class DeadGW(FakeGW):
        def llm(self, *a, **k):
            raise RuntimeError("آفلاین")

    m = Memory(td / "core.db")
    _, owner = engines_for("painting", DeadGW(), m)
    b = parse_brief("painting", "عنوان: لید strata\nفرصت: f\nچرا: c\nاقدام: زنگ بزن\nمنبع: s")
    b.id = m.add_brief(b)
    msg = owner.compose(b)
    assert "لید strata" in msg.text and msg.to_ref == "admin"       # قالب امن، بدون کرش
