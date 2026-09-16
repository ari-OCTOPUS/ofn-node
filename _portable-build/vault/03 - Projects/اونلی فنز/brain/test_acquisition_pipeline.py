#!/usr/bin/env python3
"""test_acquisition_pipeline.py — تست‌های آفلاینِ خطِ لولهٔ اکتساب (propose-only، بدونِ اثرِ بیرونی)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from acquisition_pipeline import AcquisitionPipeline  # noqa: E402


def _pipe(tmp_path):
    return AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None)


def test_no_outward_methods(tmp_path):
    p = _pipe(tmp_path)
    for m in ("post", "send", "dm", "publish", "pay", "connect", "login"):
        assert not hasattr(p, m), f"propose-only violated: {m}"


def test_auto_plan_drafts_are_brand_safe(tmp_path):
    p = _pipe(tmp_path)
    items = p.auto_plan(3)
    assert len(items) == 3
    for it in items:
        assert it["status"] == "drafted"
        low = it["caption"].lower()
        for banned in ("sydney", "harbour", "persian", "سیدنی"):
            assert banned not in low          # rule #6 گارد
        assert it["channel"] in ("reddit", "x", "of", "fansly")


def test_approve_then_finalize_never_auto_posts(tmp_path):
    p = _pipe(tmp_path)
    it = p.auto_plan(1)[0]
    assert p.approve(it["id"])["ok"] is True
    r = p.finalize(it["id"])
    assert r["ok"] is True
    assert r["auto_posted"] is False          # هرگز خودکار پست نمی‌شود
    assert r["status"] == "ready"
    assert "channel" in r["payload"] and "caption" in r["payload"]


def test_finalize_requires_approval_fail_closed(tmp_path):
    p = _pipe(tmp_path)
    it = p.auto_plan(1)[0]
    r = p.finalize(it["id"])                    # بدونِ approve
    assert r["ok"] is False and "approved" in r["error"]


def test_pf_live_flag_only_labels_never_posts(tmp_path, monkeypatch):
    p = _pipe(tmp_path)
    it = p.auto_plan(1)[0]
    p.approve(it["id"])
    monkeypatch.setenv("PF_LIVE_PUBLISH", "1")  # حتی با فلگِ زنده
    r = p.finalize(it["id"])
    assert r["auto_posted"] is False            # باز هم هرگز پست نمی‌کند
    assert r["mode"] == "ready-for-live-human-post"


def test_reject_flow(tmp_path):
    p = _pipe(tmp_path)
    it = p.auto_plan(1)[0]
    assert p.reject(it["id"], "off-brand")["ok"] is True
    assert p.by_status("rejected")[0]["id"] == it["id"]


def test_flagged_draft_cannot_be_approved(tmp_path):
    p = _pipe(tmp_path)
    p.auto_plan(1)
    # آیتمِ flagged دستی بساز
    p._items.append({"id": "PF-bad", "status": "drafted", "channel": "x",
                     "caption": "best in Sydney, guaranteed", "flagged": True})
    r = p.approve("PF-bad")
    assert r["ok"] is False and "brand-flagged" in r["error"]


def test_guard_covers_hook_and_tag_not_just_caption(tmp_path):
    # review finding #1: hook/tag باید مثلِ caption گارد شوند
    p = _pipe(tmp_path)
    p._items.append({"id": "PF-h", "status": "drafted", "channel": "x",
                     "caption": "clean soft arches", "hook": "Sydney Harbour session",
                     "tag": "x", "flagged": False})
    # چون خودِ ساختِ دستی flag نزده، گاردِ finalize باید بگیرد (approve→finalize)
    p.approve("PF-h")
    r = p.finalize("PF-h")
    assert r["ok"] is False and "containment" in r["error"].lower()


def test_guard_blocks_creator_codename_and_platform(tmp_path):
    # review finding #2: صبا/saba/onlyfans/fansly باید بن باشند
    p = _pipe(tmp_path)
    for bad in ("saba's soft soles", "صبا", "join my onlyfans", "on fansly"):
        assert p._copy_ok(bad) is False, f"guard missed: {bad}"
    # و «Aussie/Down Under» کشوری مجاز است
    assert p._copy_ok("faceless Aussie soles, down under") is True


class _BannedBrain:
    """brainِ ساختگی که seedِ ناقضِ برند برمی‌گرداند — باید flag + sanitize شود."""
    def plan_week(self):
        return {"posts": [{"platform": "x", "hook": "Sydney Harbour session",
                           "caption": "صبا on onlyfans", "tag": "persian"}]}


def test_flagged_draft_sanitized_and_no_raw_banned_persisted(tmp_path):
    p = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=_BannedBrain())
    it = p.auto_plan(1)[0]
    assert it["flagged"] is True
    # هر سه فیلد پاک‌سازی شده‌اند (متنِ خام persist نشده)
    for field in ("caption", "hook", "tag"):
        low = it[field].lower()
        for banned in ("sydney", "harbour", "صبا", "onlyfans", "persian"):
            assert banned not in low
    raw = (tmp_path / "q.json").read_text("utf-8").lower()
    for banned in ("sydney", "harbour", "صبا", "onlyfans", "persian"):
        assert banned not in raw
    # و flagged نمی‌تواند approve شود
    assert p.approve(it["id"])["ok"] is False


def test_admin_digest_content_free(tmp_path):
    p = _pipe(tmp_path)
    p.auto_plan(2)
    d = p.admin_digest()
    assert d["drafted"] == 2 and d["outward_execution"] is False
    blob = str(d).lower()
    for banned in ("sydney", "onlyfans", "صبا"):
        assert banned not in blob


def test_persistence_roundtrip(tmp_path):
    p1 = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None)
    it = p1.auto_plan(1)[0]
    p2 = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None)
    assert p2._find(it["id"]) is not None       # روی دیسک ماند
