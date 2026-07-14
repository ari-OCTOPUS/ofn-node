#!/usr/bin/env python3
"""test_route_scorer_wire.py — سیم‌کشیِ route_scorer به model_router (CORTEX-02).

اثبات می‌کند:
  * پرچمِ خاموش (پیش‌فرض): ask() ردهٔ خود را از نگاشتِ ایستای TASK_TIERS می‌گیرد
    و route_scorer اصلاً مشورت نمی‌شود (byte-identical با امروز).
  * پرچمِ روشن + بدونِ tierِ صریح: route_scorer.score_route مشورت می‌شود و ردهٔ
    پیشنهادیِ آن به‌کار می‌رود (حتی اگر با TASK_TIERS فرق کند).
  * خطای scorer → سقوطِ نرم به نگاشتِ ایستا (fail-soft).
  * tierِ صریح، حتی با پرچمِ روشن، scorer را دور می‌زند.

صفر callِ واقعیِ LLM: مسیرِ پولی (_ask_paid) و local_llm.ask مونکی‌پچ می‌شوند تا
فقط ردهٔ resolve‌شده مشاهده شود. همهٔ پرچم‌های STOP/HALT به tmp می‌روند.
اجرا: python -X utf8 test_route_scorer_wire.py
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent / "budget", _HERE.parent / "cortex", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import opslib          # noqa: E402
import model_router    # noqa: E402
import route_scorer    # noqa: E402
import local_llm       # noqa: E402


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="route-wire-test-"))


def _isolate(d: pathlib.Path) -> None:
    """kill-switch را خنثی کن: هیچ STOP/HALT زنده لمس نشود."""
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
    opslib.STOP_ORGANISM = d / "STOP-ORGANISM"
    opslib.STOP_METABOLIC = d / "STOP-METABOLIC"
    opslib.STOP_DEBATE = d / "STOP-DEBATE"


class _Spy:
    """جای‌گزینِ _ask_paid: ردهٔ درخواستی را ثبت می‌کند و یک dictِ موفق می‌دهد."""
    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, tier, prompt, system, max_tokens):
        self.calls.append(tier)
        return {"text": f"paid:{tier}", "tier": tier, "model": "spy"}


def _install(monkey_paid=True, local_ret=None):
    """_ask_paid و local_llm.ask را مونکی‌پچ کن؛ نسخهٔ اصلی را برگردان تا restore شود."""
    orig_paid = model_router._ask_paid
    orig_local = local_llm.ask
    spy = _Spy() if monkey_paid else orig_paid
    if monkey_paid:
        model_router._ask_paid = spy
    local_llm.ask = lambda prompt, system="", max_tokens=400, opener=None: (
        local_ret if local_ret is not None else {"text": "local", "tier": "local"})
    return spy, orig_paid, orig_local


def _restore(orig_paid, orig_local, orig_score):
    model_router._ask_paid = orig_paid
    local_llm.ask = orig_local
    route_scorer.score_route = orig_score
    os.environ.pop("CORTEX_ROUTE_SCORER", None)


def test_flag_off_uses_static_map_and_never_consults_scorer() -> None:
    d = _tmp(); _isolate(d)
    os.environ.pop("CORTEX_ROUTE_SCORER", None)
    orig_score = route_scorer.score_route
    consulted = {"n": 0}

    def _boom(task, ctx=None):
        consulted["n"] += 1
        raise AssertionError("scorer must NOT be consulted when flag is off")
    route_scorer.score_route = _boom
    spy, op, ol = _install()
    try:
        # research → TASK_TIERS = secondary (مسیرِ پولی → spy)
        res = model_router.ask("research", "یک تحقیقِ کوتاه")
        assert res["ok"] is True and res["tier"] == "secondary", res
        assert spy.calls == ["secondary"], spy.calls
        # classify → local (مسیرِ محلی؛ _ask_paid صدا نمی‌شود)
        spy.calls.clear()
        res2 = model_router.ask("classify", "یک متن")
        assert res2["ok"] is True and res2.get("tier") == "local", res2
        assert spy.calls == [], spy.calls
        assert consulted["n"] == 0
    finally:
        _restore(op, ol, orig_score)


def test_flag_on_consults_scorer_and_uses_its_tier() -> None:
    d = _tmp(); _isolate(d)
    os.environ["CORTEX_ROUTE_SCORER"] = "1"
    orig_score = route_scorer.score_route
    seen = {"task": None}

    def _fake(task, ctx=None):
        seen["task"] = task
        return {"tier": "primary", "scores": {}, "reasons": ["stub"]}
    route_scorer.score_route = _fake
    spy, op, ol = _install()
    try:
        # classify معمولاً local است؛ ولی scorer می‌گوید primary → باید primary شود
        res = model_router.ask("classify", "یک متن")
        assert res["ok"] is True and res["tier"] == "primary", res
        assert spy.calls == ["primary"], spy.calls
        assert seen["task"] == "classify"
    finally:
        _restore(op, ol, orig_score)


def test_scorer_error_falls_back_to_static() -> None:
    d = _tmp(); _isolate(d)
    opslib.ALERTS_MD = d / "alerts.md"        # alert() به tmp
    os.environ["CORTEX_ROUTE_SCORER"] = "1"
    orig_score = route_scorer.score_route

    def _raise(task, ctx=None):
        raise RuntimeError("scorer blew up")
    route_scorer.score_route = _raise
    spy, op, ol = _install()
    try:
        # scorer می‌ترکد → باید به TASK_TIERS["research"] = secondary برگردد
        res = model_router.ask("research", "تحقیق")
        assert res["ok"] is True and res["tier"] == "secondary", res
        assert spy.calls == ["secondary"], spy.calls
    finally:
        _restore(op, ol, orig_score)


def test_scorer_returns_invalid_tier_falls_back() -> None:
    d = _tmp(); _isolate(d)
    os.environ["CORTEX_ROUTE_SCORER"] = "1"
    orig_score = route_scorer.score_route
    route_scorer.score_route = lambda task, ctx=None: {"tier": "bogus"}
    spy, op, ol = _install()
    try:
        # ردهٔ نامعتبر از scorer → نادیده، سقوط به TASK_TIERS["orchestrate"] = primary
        res = model_router.ask("orchestrate", "کار")
        assert res["ok"] is True and res["tier"] == "primary", res
        assert spy.calls == ["primary"], spy.calls
    finally:
        _restore(op, ol, orig_score)


def test_explicit_tier_bypasses_scorer_even_when_flag_on() -> None:
    d = _tmp(); _isolate(d)
    os.environ["CORTEX_ROUTE_SCORER"] = "1"
    orig_score = route_scorer.score_route
    consulted = {"n": 0}

    def _boom(task, ctx=None):
        consulted["n"] += 1
        return {"tier": "local"}
    route_scorer.score_route = _boom
    spy, op, ol = _install()
    try:
        # tierِ صریح = primary؛ scorer نباید مشورت شود
        res = model_router.ask("classify", "متن", tier="primary")
        assert res["ok"] is True and res["tier"] == "primary", res
        assert spy.calls == ["primary"], spy.calls
        assert consulted["n"] == 0
    finally:
        _restore(op, ol, orig_score)


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_route_scorer_wire: {len(_tests)}/{len(_tests)} سبز")
