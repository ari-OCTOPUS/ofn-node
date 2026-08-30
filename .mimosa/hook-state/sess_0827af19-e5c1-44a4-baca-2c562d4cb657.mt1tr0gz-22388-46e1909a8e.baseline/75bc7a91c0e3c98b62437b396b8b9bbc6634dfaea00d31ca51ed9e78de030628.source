#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_life_currency.py — فاز ۴ دستورالعمل ۲۰۲۶-۰۸-۱۶: Life Currency 3D + مبادلهٔ آزاد (D4).

قیودِ اثبات‌شده:
  · ۱۱ عضو کورتکس در beat GREEN بودجه می‌گیرند؛ AMBER نصف؛ RED فقط survival
  · رزروِ ۲۰٪ هرگز پخش نمی‌شود؛ سقفِ سخت ۲× سهمِ beat
  · تبدیل به API با وزنِ ریسک (A6=inf ممنوع)
  · transfer آزاد با لاگ + trace_id؛ بدهی مجاز و دیده می‌شود
  · نوشتنِ latest پشتِ فلگ (dry-run پیش‌فرض) — هم‌الگوی budget_judge
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "heart"),
           str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("life-currency")

import budget_transfer as bt   # noqa: E402
import life_currency as lc     # noqa: E402
from life_currency import ActionClass, LifeBudget   # noqa: E402


# ── تخصیص ────────────────────────────────────────────────────────────────────

def test_green_allocates_to_all_11_members():
    a = lc.allocate_beat("GREEN", daily_cap=2000.0, period_s=124.0)
    assert len(a["members"]) == 11, a["members"].keys()
    assert set(a["members"]) == set(lc.CORTEX_MEMBERS)
    total = sum(m["tokens"] for m in a["members"].values())
    # رزروِ ۲۰٪ پخش نمی‌شود: total == beat_pool × (1 − RESERVE_FLOOR)
    assert abs(total - a["beat_pool"] * (1 - lc.RESERVE_FLOOR_PCT)) < 0.01
    assert a["reserve"] > 0


def test_hard_cap_two_x_beat_share():
    # حتی با سقفِ بزرگ، تخصیصِ یک beat از ۲× سهمِ روزانه/ضربانِ روز عبور نمی‌کند
    a = lc.allocate_beat("GREEN", daily_cap=10_000_000.0, period_s=124.0)
    beat_share = 10_000_000.0 / (86400.0 / 124.0)
    assert a["beat_pool"] <= 2 * beat_share + 1e-6
    assert abs(a["beat_pool"] - beat_share) < 1e-3   # GREEN کامل = دقیقاً سهمِ beat
    assert abs(a["hard_cap"] - 2 * beat_share) < 0.01   # سقفِ سختِ ۲×


def test_amber_halves_red_survival_only():
    g = lc.allocate_beat("GREEN", daily_cap=2000.0)
    a = lc.allocate_beat("AMBER", daily_cap=2000.0)
    y = lc.allocate_beat("YELLOW", daily_cap=2000.0)   # مترادفِ AMBER (سند §۶)
    r = lc.allocate_beat("RED", daily_cap=2000.0)
    assert abs(a["beat_pool"] * 2 - g["beat_pool"]) < 0.01
    assert abs(y["beat_pool"] - a["beat_pool"]) < 0.01
    assert set(r["members"]) == set(lc.SURVIVAL_MEMBERS)   # organism + heart


def test_unknown_color_allocates_nothing():
    for bad in ("", None, "purple"):
        assert lc.allocate_beat(bad, daily_cap=2000.0)["members"] == {}


def test_cost_formula_and_a6_forbidden():
    assert abs(lc.cost(100.0, ActionClass.A0) - 100.0 * 0.1 - 1.0) < 1e-9
    assert abs(lc.cost(10.0, ActionClass.A2) - 10.0 * 2.0 - 1.0) < 1e-9
    assert lc.cost(1.0, ActionClass.A6) == float("inf")


# ── مبادلهٔ آزاد (D4) ────────────────────────────────────────────────────────

def test_transfer_free_with_log_and_debt_allowed():
    bs = {"heart": LifeBudget("heart", 100.0, 10, 50.0),
          "sigma": LifeBudget("sigma", 100.0, 10, 50.0)}
    rec = bt.transfer(bs, "heart", "sigma", 30.0, 3, "test trade")
    assert rec["trace_id"].startswith("bt-") and rec["trace_id"]
    assert bs["heart"].tokens == 70.0 and bs["heart"].calls == 7
    assert bs["sigma"].tokens == 130.0 and bs["sigma"].calls == 13
    # بدهی مجاز است ولی در لاگ دیده می‌شود
    rec2 = bt.transfer(bs, "heart", "sigma", 200.0, 0, "overdrawn on purpose")
    assert bs["heart"].tokens == -130.0
    assert rec2["debt"] is True
    # هر دو رکورد با trace_id در ledger نشسته‌اند (الزامِ D4)
    lines = [json.loads(x) for x in
             bt.LEDGER_PATH.read_text("utf-8").splitlines() if x.strip()]
    mine = [x for x in lines if x.get("trace_id") in (rec["trace_id"], rec2["trace_id"])]
    assert len(mine) == 2 and all(x["event_type"] == "budget.transfer" for x in mine)


def test_transfer_rejects_unknown_member():
    bs = {"heart": LifeBudget("heart", 10.0, 1, 0.0)}
    rec = bt.transfer(bs, "heart", "ghost", 1.0, 1)
    assert rec.get("error") == "unknown-member" and rec["logged"] is False
    assert bs["heart"].tokens == 10.0   # بدونِ تغییر


def test_transfer_accepts_raw_dicts_too():
    bs = {"a": {"tokens": 5.0, "calls": 1}, "b": {"tokens": 0.0, "calls": 0}}
    rec = bt.transfer(bs, "a", "b", 2.5, 1)
    assert bs["a"]["tokens"] == 2.5 and bs["b"]["tokens"] == 2.5
    assert rec["trace_id"]


# ── نوشتن پشتِ فلگ (dry-run پیش‌فرض) ─────────────────────────────────────────

def test_emit_is_dry_run_without_flag(monkeypatch):
    monkeypatch.delenv(lc.FLAG, raising=False)
    # بدونِ env، رأیِ tracked هم در محیطِ تست غایب است (harness رجیستری واقعی را
    # نمی‌خواند چون owner_verdicts از _ops واقعی import می‌شود — پس env را صریح
    # صفر می‌گذاریم تا fallback قطعی خاموش باشد)
    monkeypatch.setenv(lc.FLAG, "0")
    res = lc.emit(lc.plan(color="GREEN", daily_cap=2000.0))
    assert res["written"] is False and res["ok"] is True
    assert not lc.LATEST_PATH.exists()


def test_emit_writes_with_flag(monkeypatch):
    monkeypatch.setenv(lc.FLAG, "1")
    res = lc.emit(lc.plan(color="GREEN", daily_cap=2000.0))
    assert res["written"] is True
    doc = json.loads(lc.LATEST_PATH.read_text("utf-8"))
    assert doc["schema"] == "life-currency.v1" and len(doc["members"]) == 11


def test_tick_never_raises(monkeypatch):
    monkeypatch.setenv(lc.FLAG, "0")
    out = lc.tick(38410)
    assert out["ok"] is True
    assert lc.tick(0)["ok"] is True


def test_organism_loop_calls_life_currency():
    src = (_HERE.parent / "organism.py").read_text("utf-8")
    assert "life_currency" in src and "_lc.tick(" in src


def test_owner_verdict_registered():
    """W5 (LIFE_CURRENCY) باید رأیِ tracked داشته باشد — env همچنان برنده است."""
    ov_text = (_HERE.parent / "owner-verdicts.yaml").read_text("utf-8")
    assert "OCTOPUS_WIRE_LIFE_CURRENCY" in ov_text


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
