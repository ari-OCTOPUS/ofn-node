# -*- coding: utf-8 -*-
"""C13 (مگا‌دستور #۱۷) — property tests برای ratio_model.

قواعد الزامی:
۱. افزودن source معتبر ratio را کاهش ندهد
۲. stale source مانند fresh امتیاز نگیرد
۳. duplicate event contribution دوبرابر نشود
۴. UNKNOWN به صفر coercion نشود
۵. floating boundary 0.50 با epsilon صریح — BORDERLINE نه HEALTHY"""
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))

from organs.ratio_model import (afferent_ratio, SourceState, EPSILON,  # noqa: E402
                                DEFAULT_THRESHOLD)


def _src(name, rate=1.0, reader=True, fresh=1.0, qual=1.0, weight=1.0):
    return SourceState(name=name, rate=rate, reader_ok=reader,
                       freshness=fresh, quality=qual, weight=weight)


def test_adding_valid_source_never_decreases_ratio():
    """Property ۱: افزودن source معتبر (rate>0, reader>0, fresh, clean)."""
    a = afferent_ratio([_src("A", rate=2)])
    ab = afferent_ratio([_src("A", rate=2), _src("B", rate=5)])
    assert ab.total_ratio >= a.total_ratio, \
        f"adding B decreased ratio: {a.total_ratio} → {ab.total_ratio}"


def test_stale_source_scores_less_than_fresh():
    """Property ۲: stale (freshness=0) باید کمتر از fresh امتیاز بگیرد."""
    fresh = afferent_ratio([_src("X", rate=5, fresh=1.0)])
    stale = afferent_ratio([_src("X", rate=5, fresh=0.1)])
    assert stale.total_ratio < fresh.total_ratio, \
        f"stale({stale.total_ratio}) should < fresh({fresh.total_ratio})"
    assert stale.stale_penalty > 0


def test_duplicate_source_does_not_double():
    """Property ۳: دو source هم‌نام با همان rate — contribution جمع نمی‌شود (weight normalize)."""
    one = afferent_ratio([_src("X", rate=5)])
    two = afferent_ratio([_src("X", rate=5, weight=0.5), _src("X", rate=5, weight=0.5)])
    # دو نیمه باید ≈ یکی باشد (جمع weight همان ۱)
    assert abs(one.total_ratio - two.total_ratio) < 0.01


def test_unknown_not_coerced_to_zero():
    """Property ۴: UNKNOWN quality باید penalty بگیرد نه اینکه صفر شود."""
    clean = afferent_ratio([_src("X", rate=5, qual=1.0)])
    unknown = afferent_ratio([_src("X", rate=5, qual=0.3)])
    assert unknown.quality_penalty > 0
    assert unknown.total_ratio < clean.total_ratio


def test_counterfactual_050_is_borderline_not_healthy():
    """Property ۵: scenario از C1 (counterfactual) — ratio≈0.50 باید BORDERLINE."""
    # بازتولید scenario B از STARVATION-COUNTERFACTUAL.json
    sources = [
        _src("spend_snapshot", rate=2, reader=True),
        _src("knowledge_notes", rate=8, reader=True),
        _src("telegram_inbound", rate=0, reader=False),
        _src("telemetry", rate=0, reader=False),
    ]
    r = afferent_ratio(sources)
    # ratio باید نزدیک 0.5 باشد و verdict=BORDERLINE
    assert r.verdict == "BORDERLINE", \
        f"ratio={r.total_ratio} → {r.verdict} (expected BORDERLINE near 0.5)"
    assert abs(r.margin) <= EPSILON


def test_no_sources_starved():
    r = afferent_ratio([])
    assert r.verdict == "STARVED" and r.total_ratio == 0.0


def test_all_sources_healthy():
    sources = [_src(f"s{i}", rate=5) for i in range(5)]
    r = afferent_ratio(sources)
    assert r.verdict == "HEALTHY"
    assert r.total_ratio > DEFAULT_THRESHOLD + EPSILON


def test_broken_reader_penalized():
    """اگر reader خراب باشد (reader_ok=False)، contribution=0 و penalty>0."""
    r = afferent_ratio([_src("X", rate=5, reader=False)])
    assert r.source_contributions["X"] == 0.0
    assert r.reader_failure_penalty > 0
    assert r.total_ratio < DEFAULT_THRESHOLD
