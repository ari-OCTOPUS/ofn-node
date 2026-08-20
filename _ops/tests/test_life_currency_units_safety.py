# -*- coding: utf-8 -*-
"""واحد life_credit و مشتق beat_pool — گیت ایمنی بودجه 2026-08-20.

اثبات می‌کند:
  1. daily_cap=1000 با period=107.69s → beat_pool≈1.246 (شاهد زنده beat 42165)
  2. سقف ۲× سهمِ beat یک سقف است نه دو برابر کردنِ استخرِ GREEN
  3. UNIT=life_credit و credits_to_aud همیشه raise می‌کند
  4. life_currency / model_router / money_gate به هم import ندارند
     → این عدد نمی‌تواند به خرج AUD تبدیل شود مگر سیم‌کشی تازه (که این تست قرمزش می‌کند)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "heart"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "budget"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cortex"))

import harness  # noqa: E402
harness.setup("life-currency-units-safety")

from heart.life_currency import (  # noqa: E402
    UNIT, MONEY_PATH, DAILY_BUDGET_HARD_CAP_X, RESERVE_FLOOR_PCT,
    allocate_beat, credits_to_aud,
)

_OPS = Path(__file__).resolve().parents[1]


def test_unit_is_life_credit_not_aud():
    assert UNIT == "life_credit"
    assert MONEY_PATH is False
    try:
        credits_to_aud(1000)
    except RuntimeError as e:
        assert "life_credit_is_not_aud" in str(e)
    else:
        raise AssertionError("credits_to_aud must fail-closed")


def test_beat_pool_1000_at_period_107_69_matches_live_1_246():
    """شاهد زنده beat 42165: daily_cap=1000, beat_pool=1.246.
    period زنده آن لحظه ≈107.69s (arbiter.effective_period_s).
    30s فرضِ نادرست است: 1000/(86400/30)=0.347 ≠ 1.246."""
    r = allocate_beat("GREEN", daily_cap=1000.0, period_s=107.69)
    beats_per_day = 86400.0 / 107.69
    share = 1000.0 / beats_per_day
    assert abs(r["beat_pool"] - 1.246) < 0.002
    assert r["beat_pool"] == round(share, 3)
    assert r["hard_cap"] == round(DAILY_BUDGET_HARD_CAP_X * share, 3)
    # GREEN: استخر = سهمِ نامی؛ ۲× فقط سقف است نه ضریبِ اعمال‌شده
    assert r["beat_pool"] <= r["hard_cap"] + 1e-9
    assert abs(r["beat_pool"] * 2 - r["hard_cap"]) < 0.01
    assert len(r["members"]) == 11
    assert r["reserve"] == round(r["beat_pool"] * RESERVE_FLOOR_PCT, 3)


def test_thirty_second_period_does_not_produce_1_246():
    r = allocate_beat("GREEN", daily_cap=1000.0, period_s=30.0)
    assert r["beat_pool"] == round(1000.0 / (86400.0 / 30.0), 3)
    assert abs(r["beat_pool"] - 0.347) < 0.001
    assert abs(r["beat_pool"] - 1.246) > 0.5


def test_life_currency_source_has_no_money_imports():
    src = (_OPS / "heart" / "life_currency.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for bad in ("model_router", "money_gate", "cost_receipt"):
        assert bad not in imported, imported
    assert "credits_to_aud" in src
    assert "life_credit_is_not_aud" in src


def test_money_modules_do_not_read_life_currency():
    for rel in ("cortex/model_router.py", "budget/money_gate.py",
                "cortex/cost_receipt.py"):
        p = _OPS / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        assert "life_currency" not in text
        assert "life-currency-latest" not in text


def test_rollback_cap_30_still_allocates_eleven_members():
    r = allocate_beat("GREEN", daily_cap=30.0, period_s=107.69)
    assert len(r["members"]) == 11
    assert r["beat_pool"] > 0.0
    assert r["beat_pool"] == round(30.0 / (86400.0 / 107.69), 3)
    # 30 life_credit/روز اگر ۱:۱ AUD بود از سقف ۲ AUD/روز عبور می‌کرد.
    # ایمنی = نبودِ مسیر تبدیل (تست‌های بالا)، نه خودِ عدد ۳۰.


def test_cap30_is_thirty_three_times_smaller_than_1000():
    period = 107.69
    share_1000 = 1000.0 / (86400.0 / period)
    share_30 = 30.0 / (86400.0 / period)
    assert abs(share_1000 / share_30 - (1000.0 / 30.0)) < 1e-12
    a = allocate_beat("GREEN", daily_cap=1000.0, period_s=period)
    b = allocate_beat("GREEN", daily_cap=30.0, period_s=period)
    assert a["beat_pool"] == round(share_1000, 3) == 1.246
    assert b["beat_pool"] == round(share_30, 3) == 0.037
    # نسبتِ گردشده 1.246/0.037≈33.68 است نه 33.33 — اثر round(..., 3)


def test_cap30_floor_30s_green_hits_milli_granularity():
    r = allocate_beat("GREEN", daily_cap=30.0, period_s=30.0)
    assert r["beat_pool"] == 0.01
    assert r["reserve"] == 0.002
    toks = {m["tokens"] for m in r["members"].values()}
    assert toks == {0.001}
    assert all(m["calls"] == 0 for m in r["members"].values())


def test_cap30_floor_30s_amber_silent_zero_tokens():
    """بدترین حالت واقعی داور: کف ۳۰ثانیه × AMBER → گرد کردن به صفر."""
    r = allocate_beat("AMBER", daily_cap=30.0, period_s=30.0)
    assert r["beat_pool"] == 0.005
    toks = [m["tokens"] for m in r["members"].values()]
    assert toks == [0.0] * 11
    assert all(m["calls"] == 0 for m in r["members"].values())


def test_calls_remain_zero_below_call_cost_even_at_1000():
    for cap in (30.0, 1000.0):
        r = allocate_beat("GREEN", daily_cap=cap, period_s=107.69)
        assert all(m["calls"] == 0 for m in r["members"].values())
        assert max(m["tokens"] for m in r["members"].values()) < 10.0
