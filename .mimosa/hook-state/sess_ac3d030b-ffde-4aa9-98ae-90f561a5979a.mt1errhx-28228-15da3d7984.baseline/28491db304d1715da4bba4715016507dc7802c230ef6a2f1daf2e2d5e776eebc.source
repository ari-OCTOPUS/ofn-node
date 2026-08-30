#!/usr/bin/env python3
"""test_warmup_guard.py — تست‌های safety net #2: warm-up guard.

تضمین می‌کند که تا رسیدنِ کارما به آستانه، هیچ آیتمِ فروشی روی Reddit
finalize نمی‌شود (fail-closed). این محافظت در برابرِ shadowban است.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from guards import WarmupGuard, ChannelLocks, check_all_guards  # noqa: E402
from acquisition_pipeline import AcquisitionPipeline  # noqa: E402


# ── WarmupGuard unit tests ────────────────────────────────────────────────

def test_warmup_blocks_sale_when_karma_low(tmp_path):
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    ok, _ = wg.link_allowed("reddit", hook="check my link in bio for more")
    assert ok is False, "sale item must be blocked when karma=0"


def test_warmup_allows_sfw_when_karma_low(tmp_path):
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    ok, _ = wg.link_allowed("reddit", hook="arch of the day, soft light")
    assert ok is True, "SFW post must be allowed during warm-up"


def test_warmup_allows_sale_after_threshold(tmp_path):
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    wg.set_karma(25, "manual")
    ok, _ = wg.link_allowed("reddit", hook="link in bio", caption="subscribe for ppv")
    assert ok is True, "sale must be allowed once karma threshold met"


def test_warmup_non_warmup_channel_always_allowed(tmp_path):
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    # X / OF channels don't need Reddit karma
    ok, _ = wg.link_allowed("x", hook="subscribe now", caption="ppv unlock")
    assert ok is True


def test_warmup_detects_sale_markers(tmp_path):
    """بزرگ‌ترین فهرست از نشانه‌های فروش — هر یک باید detected شود."""
    cases = [
        ("link in bio", True), ("subscribe to my of", True),
        ("ppv unlock $5", True), ("DM me for custom", True),
        ("nice pedicure today", False), ("arch of the day", False),
        ("soft light feet", False),
    ]
    for text, expected in cases:
        assert WarmupGuard.is_sale_item(hook=text) is expected, f"missed: {text}"


def test_warmup_persistence_across_instances(tmp_path):
    """set_karma باید persist شود — instance جدید همان کارما را ببیند."""
    p = tmp_path / "rs.json"
    wg1 = WarmupGuard(state_path=p, karma_threshold=20)
    wg1.set_karma(25, "first")
    wg2 = WarmupGuard(state_path=p, karma_threshold=20)
    assert wg2.get_karma() == 25
    assert wg2.threshold_met() is True


def test_warmup_threshold_boundary(tmp_path):
    """درست روی آستانه (20) باید met=True."""
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    wg.set_karma(20)
    assert wg.threshold_met() is True
    wg.set_karma(19)
    assert wg.threshold_met() is False


# ── Pipeline integration: finalize respects warm-up guard ────────────────

def test_pipeline_finalize_blocks_sale_during_warmup(tmp_path):
    """finalize() روی آیتمِ فروشی با کارمای کم باید fail-closed کنه."""
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    # karma هنوز 0 است
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None,
                                warmup=wg, locks=None)
    # یک آیتم فروشی دستی بساز
    pipe._items.append({
        "id": "PF-SALE1", "status": "approved", "channel": "reddit",
        "tag": "ppv", "hook": "link in bio for ppv", "caption": "subscribe for content",
        "flagged": False, "approved_by": "test",
    })
    pipe._save()
    r = pipe.finalize("PF-SALE1")
    assert r["ok"] is False, "sale must be blocked during warm-up"
    assert "warm-up guard" in r["error"] or "blocked" in r["error"]
    # آیتم نباید reject شده باشد — باید approved بماند برای retry بعدی
    assert r.get("item_status") == "approved"


def test_pipeline_finalize_allows_sfw_during_warmup(tmp_path):
    """SFW آیتم حتی با کارمای کم باید finalize شود."""
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None,
                                warmup=wg, locks=None)
    pipe._items.append({
        "id": "PF-SFW1", "status": "approved", "channel": "reddit",
        "tag": "faceless-feet", "hook": "arch of the day soft light",
        "caption": "arch of the day", "flagged": False, "approved_by": "test",
    })
    pipe._save()
    r = pipe.finalize("PF-SFW1")
    assert r["ok"] is True
    assert r["auto_posted"] is False


def test_pipeline_finalize_allows_sale_after_warmup_done(tmp_path):
    """وقتی کارما به آستانه رسید، آیتم فروشی باید finalize شود."""
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    wg.set_karma(25)
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None,
                                warmup=wg, locks=None)
    pipe._items.append({
        "id": "PF-SALE2", "status": "approved", "channel": "reddit",
        "tag": "ppv", "hook": "link in bio", "caption": "subscribe",
        "flagged": False, "approved_by": "test",
    })
    pipe._save()
    r = pipe.finalize("PF-SALE2")
    assert r["ok"] is True


def test_pipeline_backward_compat_no_guards(tmp_path):
    """بدونِ guards (backward-compat)، finalize باید مثلِ قبل کار کنه."""
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None,
                                warmup=None, locks=None)
    pipe._items.append({
        "id": "PF-OLD1", "status": "approved", "channel": "reddit",
        "tag": "anything", "hook": "link in bio subscribe", "caption": "buy now",
        "flagged": False, "approved_by": "test",
    })
    pipe._save()
    r = pipe.finalize("PF-OLD1")
    # بدون guards، حتی sale هم finalize می‌شود (guard اختیاری است)
    assert r["ok"] is True
