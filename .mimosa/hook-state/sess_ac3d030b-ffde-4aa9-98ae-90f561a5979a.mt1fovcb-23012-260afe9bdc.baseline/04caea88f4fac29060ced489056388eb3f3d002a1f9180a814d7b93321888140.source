# -*- coding: utf-8 -*-
"""C-042 floor rounding — fully offline (no live process, no model calls).

Owner formula (دستور مالک #۲):
  beat_share = cap / (86400 / period)
  hard_cap   = 2 × beat_share
  pool       = min(beat_share × scale, hard_cap)
  reserve    = pool × 0.20
  per_member = (pool − reserve) / 11

Rounding policy documented here:
  • Conservation is asserted on RAW floats: 11×per_member + reserve == pool.
  • Published fields independently round(..., 3) (life_currency.allocate_beat).
  • After 3dp, 11×tokens + reserve_pub need NOT equal beat_pool (C-042).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "heart"))

import harness  # noqa: E402
harness.setup("life-currency-floor-rounding")

from heart.life_currency import (  # noqa: E402
    RESERVE_FLOOR_PCT, allocate_beat, color_scale,
)

N_MEMBERS = 11
EPS = 1e-9


def _raw(*, cap: float, period: float, scale: float, n: int = N_MEMBERS):
    beat_share = cap / (86400.0 / period)
    hard_cap = 2.0 * beat_share
    pool = min(beat_share * scale, hard_cap)
    reserve = pool * 0.20
    per_member = (pool - reserve) / n
    return beat_share, hard_cap, pool, reserve, per_member


def test_amber_floor_raw_share_0_000379_reports_0_000():
    """cap=30 period=30.0 scale=0.5 members=11 → raw 0.000379 · reported 0.000."""
    cap, period, scale = 30.0, 30.0, 0.5
    assert abs(color_scale("AMBER") - scale) < EPS
    _share, _hc, pool, reserve, per = _raw(cap=cap, period=period, scale=scale)
    assert abs(per - 0.000379) < 5e-7
    assert abs(11 * per + reserve - pool) < EPS
    r = allocate_beat("AMBER", daily_cap=cap, period_s=period)
    assert len(r["members"]) == N_MEMBERS
    toks = [m["tokens"] for m in r["members"].values()]
    assert toks == [0.0] * N_MEMBERS
    assert round(per, 3) == 0.0
    # published 3dp does not conserve (C-042): 11*0.000 + 0.001 ≠ 0.005
    assert r["beat_pool"] == 0.005
    assert r["reserve"] == 0.001
    assert abs(sum(toks) + r["reserve"] - r["beat_pool"]) > 1e-6


def test_regression_cap30_green_period_114():
    _share, _hc, pool, reserve, per = _raw(cap=30.0, period=114.0, scale=1.0)
    assert abs(pool - 0.039583) < 5e-7
    assert abs(reserve - 0.007917) < 5e-7
    assert abs(per - 0.002879) < 5e-7
    assert abs(11 * per + reserve - pool) < EPS
    r = allocate_beat("GREEN", daily_cap=30.0, period_s=114.0)
    toks = {m["tokens"] for m in r["members"].values()}
    assert toks == {0.003}
    assert r["beat_pool"] == round(pool, 3)
    assert r["reserve"] == round(reserve, 3)


def test_regression_cap30_amber_period_113_65():
    _share, _hc, pool, reserve, per = _raw(cap=30.0, period=113.65, scale=0.5)
    assert abs(pool - 0.019731) < 5e-7
    assert abs(reserve - 0.003946) < 5e-7
    assert abs(per - 0.001435) < 5e-7
    assert abs(11 * per + reserve - pool) < EPS
    r = allocate_beat("AMBER", daily_cap=30.0, period_s=113.65)
    toks = {m["tokens"] for m in r["members"].values()}
    assert toks == {0.001}
    assert r["beat_pool"] == round(pool, 3) == 0.02
    assert r["reserve"] == round(reserve, 3) == 0.004


def test_regression_cap1000_green_period_114_01():
    _share, _hc, pool, reserve, per = _raw(cap=1000.0, period=114.01, scale=1.0)
    assert abs(pool - 1.319560) < 5e-7
    assert abs(reserve - 0.263912) < 5e-7
    assert abs(per - 0.095968) < 5e-7
    assert abs(11 * per + reserve - pool) < EPS
    r = allocate_beat("GREEN", daily_cap=1000.0, period_s=114.01)
    toks = {m["tokens"] for m in r["members"].values()}
    assert toks == {0.096}
    assert r["beat_pool"] == round(pool, 3)
    assert r["reserve"] == round(pool * RESERVE_FLOOR_PCT, 3)


def test_raw_conservation_holds_on_owner_table_rows():
    rows = [
        (1000.0, 114.01, 1.0),
        (30.0, 114.00, 1.0),
        (30.0, 113.65, 0.5),
        (30.0, 30.00, 1.0),
        (30.0, 30.00, 0.5),
    ]
    for cap, period, scale in rows:
        _s, _h, pool, reserve, per = _raw(cap=cap, period=period, scale=scale)
        assert abs(11 * per + reserve - pool) < EPS, (cap, period, scale)
        # worst-case daily: AMBER floor per_member * (86400/30) ≈ 1.0920
        if cap == 30.0 and period == 30.0 and scale == 0.5:
            beats = 86400.0 / period
            # table 6dp share 0.000379 × 2880 = 1.09152 ≈ owner 1.0920
            # 11×1.09152 = 12.00672 ≈ owner 12.0067; reserve_day raw = 3.0
            # 12.0067+3.0 is display; exact total uses RAW per not 6dp share
            table_share = 0.000379
            assert abs(table_share * beats - 1.0920) < 5e-4
            assert abs(table_share * beats * 11 - 12.0067) < 5e-4
            assert abs(reserve * beats - 3.0) < 5e-3
            assert abs(11 * per * beats + reserve * beats - cap * scale) < 1e-9
