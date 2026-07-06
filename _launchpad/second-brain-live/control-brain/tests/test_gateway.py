# -*- coding: utf-8 -*-
"""آزمون Gateway — بدون شبکه: _post فیک می‌شود. تمرکز: بودجه + کش + شمارش orchestration."""
from core.gateway import BudgetExceeded, Gateway, GatewayError
from core.memory import Memory


def _gw(td, **env):
    m = Memory(td / "core.db")
    e = {"DEEPSEEK_API_KEY": "x", "SAKANA_API_KEY": "y", "TAVILY_API_KEY": "z",
         "FUGU_BUDGET_MONTHLY": "40", "DEEPSEEK_BUDGET_DAILY": "3", **env}
    g = Gateway(m, e)
    return g, m


def _fake_llm_response(text="جواب", tin=100, tout=50, orch=0):
    return {"choices": [{"message": {"content": text}}],
            "usage": {"prompt_tokens": tin, "completion_tokens": tout,
                      "input_tokens_details": {"orchestration_input_tokens": orch},
                      "output_tokens_details": {"orchestration_output_tokens": orch}}}


def test_cheap_llm_and_cache(td):
    g, m = _gw(td)
    calls = []
    g._post = lambda url, p, h, timeout=90: (calls.append(url), _fake_llm_response())[1]
    out1 = g.llm("سوال", business="ziman")
    out2 = g.llm("سوال", business="ziman")     # باید از کش بیاید
    assert out1 == out2 == "جواب"
    assert len(calls) == 1 and "deepseek.com" in calls[0]
    assert m.day_cost("deepseek") > 0


def test_fugu_budget_gate(td):
    g, m = _gw(td)
    g._post = lambda *a, **k: _fake_llm_response(tin=1_200_000, tout=1_200_000, orch=100_000)
    g.llm("سخت", tier="escalate", use_cache=False)      # 1.3M/1.3M → ~$45.5 (بالای سقف $40)
    assert m.month_cost("fugu") > 42                     # orchestration هم شمرده شد
    try:
        g.llm("سخت ۲", tier="escalate", use_cache=False)
        raise AssertionError("باید BudgetExceeded می‌داد")
    except BudgetExceeded:
        pass


def test_deepseek_daily_cap(td):
    g, m = _gw(td, DEEPSEEK_BUDGET_DAILY="0.0001")
    g._post = lambda *a, **k: _fake_llm_response()
    m.usage_add("deepseek", 10_000, 10_000, 0.01)
    try:
        g.llm("سوال", use_cache=False)
        raise AssertionError("باید BudgetExceeded می‌داد")
    except BudgetExceeded:
        pass


def test_offline_without_key(td):
    g, _ = _gw(td, DEEPSEEK_API_KEY="")
    try:
        g.llm("سوال", use_cache=False)
        raise AssertionError("باید GatewayError می‌داد")
    except GatewayError:
        pass


def test_search_cached(td):
    g, _ = _gw(td)
    calls = []
    g._post = lambda url, p, h, timeout=90: (calls.append(url),
        {"results": [{"title": "t", "url": "u", "content": "c"}]})[1]
    r1 = g.search("بازار هدیه سیدنی")
    r2 = g.search("بازار هدیه سیدنی")
    assert r1 == r2 and r1[0]["title"] == "t"
    ass