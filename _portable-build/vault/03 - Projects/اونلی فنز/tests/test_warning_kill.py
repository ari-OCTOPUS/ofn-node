#!/usr/bin/env python3
"""test_warning_kill.py — تست‌های safety net #3: platform-warning kill-switch.

تضمین می‌کند:
  - ۱ warning روی یک کانال → کانال lock می‌شود.
  - ۲ warning روی یک کانال → full_stop فعال می‌شود (کل قیف).
  - full_stop تا verdict آری پایدار است.
  - pipeline.finalize هنگام lock/full_stop fail-closed می‌کند.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from guards import ChannelLocks, WarmupGuard, check_all_guards  # noqa: E402
from acquisition_pipeline import AcquisitionPipeline  # noqa: E402


def _locks(tmp_path):
    return ChannelLocks(state_path=tmp_path / "cl.json")


# ── ChannelLocks unit ────────────────────────────────────────────────────

def test_one_warning_locks_channel(tmp_path):
    cl = _locks(tmp_path)
    r = cl.report_warning("reddit", "shadowban suspected")
    assert r["locked"] is True
    assert r["full_stop"] is False
    assert cl.channel_locked("reddit") is True
    assert cl.channel_locked("x") is False   # کانال دیگر باز است


def test_two_warnings_on_same_channel_triggers_full_stop(tmp_path):
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "first")
    r = cl.report_warning("reddit", "second warning")
    assert r["full_stop"] is True
    assert cl.full_stop_active() is True


def test_warnings_on_different_channels_no_full_stop(tmp_path):
    """۱ warning روی reddit + ۱ روی x → هیچ‌کدام full_stop نمی‌شود."""
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "r warning")
    cl.report_warning("x", "x warning")
    assert cl.full_stop_active() is False
    assert cl.channel_locked("reddit") is True
    assert cl.channel_locked("x") is True


def test_clear_warning_unlocks_channel(tmp_path):
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "test")
    assert cl.channel_locked("reddit")
    r = cl.clear_warning("reddit")
    assert r["ok"] is True
    assert cl.channel_locked("reddit") is False


def test_clear_warning_blocked_during_full_stop(tmp_path):
    """وقتی full_stop فعال است، clear_warning کار نمی‌کند — فقط clear_full_stop."""
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "1")
    cl.report_warning("reddit", "2")
    assert cl.full_stop_active()
    r = cl.clear_warning("reddit")
    assert r["ok"] is False
    assert "full_stop" in r["error"]


def test_clear_full_stop_unlocks_all(tmp_path):
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "1")
    cl.report_warning("reddit", "2")
    cl.report_warning("x", "x")
    assert cl.full_stop_active()
    r = cl.clear_full_stop()
    assert r["ok"] is True
    assert cl.full_stop_active() is False
    assert cl.channel_locked("reddit") is False
    assert cl.channel_locked("x") is False


def test_snapshot_is_content_free(tmp_path):
    """snapshot نباید reason کامل را لو بدهد — فقط counts و last_reason کوتاه."""
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "some detailed reason with maybe sensitive info")
    snap = cl.snapshot()
    assert "channels" in snap
    assert snap["channels"]["reddit"]["warnings"] == 1
    assert isinstance(snap["channels"]["reddit"]["last_reason"], str)


# ── check_all_guards composite ───────────────────────────────────────────

def test_check_all_guards_full_stop_wins(tmp_path):
    """full_stop باید قبل از warm-up deny کند."""
    cl = _locks(tmp_path)
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    wg.set_karma(100)   # warm-up pass
    cl.report_warning("reddit", "1")
    cl.report_warning("reddit", "2")
    ok, reason = check_all_guards("reddit", warmup=wg, locks=cl)
    assert ok is False
    assert "full_stop" in reason


def test_check_all_guards_channel_lock_wins(tmp_path):
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "1")   # lock بدون full_stop
    ok, reason = check_all_guards("reddit", warmup=None, locks=cl)
    assert ok is False
    assert "locked" in reason


def test_check_all_guards_all_pass(tmp_path):
    cl = _locks(tmp_path)
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    wg.set_karma(25)
    ok, _ = check_all_guards("reddit", hook="link in bio",
                             caption="subscribe", warmup=wg, locks=cl)
    assert ok is True


# ── Pipeline integration ─────────────────────────────────────────────────

def test_pipeline_finalize_blocked_when_channel_locked(tmp_path):
    """وقتی reddit lock است، حتی آیتمِ SFW هم finalize نمی‌شود."""
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "warning")
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    wg.set_karma(25)   # warm-up pass
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None,
                                warmup=wg, locks=cl)
    pipe._items.append({
        "id": "PF-LK1", "status": "approved", "channel": "reddit",
        "tag": "sfw", "hook": "arch of day", "caption": "nice feet",
        "flagged": False, "approved_by": "test",
    })
    pipe._save()
    r = pipe.finalize("PF-LK1")
    assert r["ok"] is False
    assert "locked" in r["error"]


def test_pipeline_admin_digest_includes_guards(tmp_path):
    """admin_digest باید وضعیت guards را نشان دهد (برای /pf_status)."""
    cl = _locks(tmp_path)
    wg = WarmupGuard(state_path=tmp_path / "rs.json", karma_threshold=20)
    wg.set_karma(10)
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None,
                                warmup=wg, locks=cl)
    d = pipe.admin_digest()
    assert "warmup" in d
    assert d["warmup"]["karma"] == 10
    assert d["warmup"]["met"] is False
    assert "locks" in d


def test_pipeline_finalize_blocked_when_full_stop(tmp_path):
    cl = _locks(tmp_path)
    cl.report_warning("reddit", "1")
    cl.report_warning("reddit", "2")
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None,
                                warmup=None, locks=cl)
    pipe._items.append({
        "id": "PF-FS1", "status": "approved", "channel": "x",
        "tag": "sfw", "hook": "nice day", "caption": "hello",
        "flagged": False, "approved_by": "test",
    })
    pipe._save()
    r = pipe.finalize("PF-FS1")
    assert r["ok"] is False
    assert "full_stop" in r["error"]
