#!/usr/bin/env python3
"""test_store.py — تست‌های DataSpine (لایهٔ ۲ منبعِ حقیقت یکپارچه).

تضمین می‌کند:
  - FanDB: add/purchase/touch/tag، segment خودکار، صفر PII (فقط هش)
  - VaultBank: add/pick fair rotation، mark_used، record_metric
  - KPIRollup: bucket هفتگی، جمعِ چندثبتی، trend
  - OctopusState: record_tick، mark_isolated، snapshot
  - DataSpine: container یکپارچه، full_snapshot
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from store import FanDB, VaultBank, KPIRollup, OctopusState, DataSpine, _fan_id  # noqa: E402


def _spine(tmp_path):
    return DataSpine(store_dir=tmp_path)


# ── FanDB ────────────────────────────────────────────────────────────────

def test_fan_add_creates_lurker(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    r = db.add("fan-1", "of")
    assert r["ok"]
    assert r["segment"] == "lurker"
    assert r["id"].startswith("F-")


def test_fan_zero_pii_only_hash_stored(tmp_path):
    """نام واقعی هرگز ذخیره نمی‌شود — فقط هش + alias کوتاه."""
    db = FanDB(path=tmp_path / "f.json")
    db.add("John Smith The Third", "of")
    state = db._state()
    # هیچ fan با کلیدِ «John» نباید وجود داشته باشد
    for fid, fan in state["fans"].items():
        assert fid.startswith("F-")
        assert "John Smith The Third" not in fid


def test_fan_purchase_updates_ltv_and_segment(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    db.add("fan-1", "of")
    db.record_purchase("fan-1", 20.0, "ppv")
    r = db.record_purchase("fan-1", 35.0, "ppv")
    assert r["ltv_usd"] == 55.0
    assert r["segment"] == "vip"   # ≥ 50


def test_fan_segment_regular_below_vip(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    db.add("fan-1")
    r = db.record_purchase("fan-1", 10.0, "ppv")
    assert r["segment"] == "regular"


def test_fan_purchase_creates_if_missing(tmp_path):
    """purchase روی fan ناشناخته → fan ساخته می‌شود."""
    db = FanDB(path=tmp_path / "f.json")
    r = db.record_purchase("ghost-fan", 5.0, "tip")
    assert r["ok"]
    assert r["ltv_usd"] == 5.0


def test_fan_tag_appends(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    db.add("fan-1")
    db.tag("fan-1", "vip-list")
    r = db.tag("fan-1", "whale")
    assert "vip-list" in r["tags"]
    assert "whale" in r["tags"]
    # duplicate نباید اضافه شود
    db.tag("fan-1", "whale")
    assert db.get("fan-1")["tags"].count("whale") == 1


def test_fan_tag_unknown_fan_errors(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    r = db.tag("ghost", "x")
    assert r["ok"] is False


def test_fan_by_segment(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    db.add("vip-fan")
    db.record_purchase("vip-fan", 100)
    db.add("reg-fan")
    db.record_purchase("reg-fan", 10)
    db.add("lurker-fan")
    assert len(db.by_segment("vip")) == 1
    assert len(db.by_segment("regular")) == 1
    assert len(db.by_segment("lurker")) == 1


def test_fan_summary_counts(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    db.add("a"); db.add("b"); db.record_purchase("a", 30)
    s = db.summary()
    assert s["total"] == 2
    assert s["total_ltv_usd"] == 30.0
    assert "segments" in s


def test_fan_persistence_across_instances(tmp_path):
    p = tmp_path / "f.json"
    FanDB(path=p).add("fan-1", "of")
    db2 = FanDB(path=p)
    assert db2.get("fan-1") is not None


# ── VaultBank ────────────────────────────────────────────────────────────

def test_vault_add_and_pick(tmp_path):
    vb = VaultBank(path=tmp_path / "v.json")
    vb.add("pedicure", "Arch of Day", channel="reddit")
    vb.add("nylon", "Soft Sunday", channel="x")
    reddit_picks = vb.pick("reddit", 5)
    assert len(reddit_picks) == 1
    assert reddit_picks[0]["tag"] == "pedicure"


def test_vault_pick_fair_rotation(tmp_path):
    """کم‌استفاده‌ترین asset اول انتخاب می‌شود."""
    vb = VaultBank(path=tmp_path / "v.json")
    a1 = vb.add("tag-a", "hook-a")["id"]
    a2 = vb.add("tag-b", "hook-b")["id"]
    vb.mark_used(a1)
    picks = vb.pick(n=1)
    assert picks[0]["id"] == a2   # a2 کم‌استفاده‌تر


def test_vault_mark_used_increments(tmp_path):
    vb = VaultBank(path=tmp_path / "v.json")
    vid = vb.add("tag", "hook")["id"]
    vb.mark_used(vid)
    vb.mark_used(vid)
    assert vb.all()[0]["used_count"] == 2


def test_vault_record_metric_accumulates(tmp_path):
    vb = VaultBank(path=tmp_path / "v.json")
    vid = vb.add("tag", "hook")["id"]
    vb.record_metric(vid, upvotes=10, comments=2, unlocks=1)
    vb.record_metric(vid, upvotes=5, comments=1)
    m = vb.all()[0]["metrics"]
    assert m["upvotes"] == 15
    assert m["comments"] == 3
    assert m["unlocks"] == 1


def test_vault_by_tag(tmp_path):
    vb = VaultBank(path=tmp_path / "v.json")
    vb.add("asmr", "h1"); vb.add("asmr", "h2"); vb.add("nylon", "h3")
    assert len(vb.by_tag("asmr")) == 2
    assert len(vb.by_tag("nylon")) == 1


# ── KPIRollup ────────────────────────────────────────────────────────────

def test_kpi_record_creates_week_bucket(tmp_path):
    k = KPIRollup(path=tmp_path / "k.json")
    r = k.record(revenue_usd=20, ppv_unlocks=2, posts=1)
    assert r["ok"]
    assert r["current"]["revenue_usd"] == 20
    assert r["current"]["ppv_unlocks"] == 2


def test_kpi_multiple_records_same_week_accumulate(tmp_path):
    """چند record در یک هفته → جمع، نه replace."""
    k = KPIRollup(path=tmp_path / "k.json")
    k.record(revenue_usd=10)
    k.record(revenue_usd=15, ppv_unlocks=1)
    cur = k.current_week()
    assert cur["revenue_usd"] == 25
    assert cur["ppv_unlocks"] == 1


def test_kpi_trend_returns_history(tmp_path):
    k = KPIRollup(path=tmp_path / "k.json")
    k.record(revenue_usd=5)
    trend = k.trend(4)
    assert len(trend) >= 1


def test_kpi_summary_total(tmp_path):
    k = KPIRollup(path=tmp_path / "k.json")
    k.record(revenue_usd=10)
    k.record(revenue_usd=20)
    s = k.summary()
    assert s["total_revenue_usd"] == 30


# ── OctopusState ─────────────────────────────────────────────────────────

def test_octopus_record_tick(tmp_path):
    o = OctopusState(path=tmp_path / "o.json")
    r = o.record_tick(beat=5, protective=False, pain=0.2,
                      brain_loaded=True, neural_available=True)
    assert r["ok"]
    snap = o.snapshot()
    assert snap["beat"] == 5
    assert snap["neural_available"] is True


def test_octopus_mark_isolated(tmp_path):
    o = OctopusState(path=tmp_path / "o.json")
    r = o.mark_isolated("no _ops")
    assert r["isolated"] is True
    snap = o.snapshot()
    assert snap["neural_available"] is False


def test_octopus_history_capped(tmp_path):
    """history فقط ۵۰ آخر را نگه می‌دارد."""
    o = OctopusState(path=tmp_path / "o.json")
    for i in range(60):
        o.record_tick(i, False, 0.1, True, True)
    state = o._state()
    assert len(state["history"]) <= 50


# ── DataSpine integration ────────────────────────────────────────────────

def test_spine_full_snapshot(tmp_path):
    spine = _spine(tmp_path)
    spine.fans.add("fan-1", "of")
    spine.vault.add("tag", "hook")
    spine.kpi.record(revenue_usd=5)
    snap = spine.full_snapshot()
    assert "fans" in snap and "vault" in snap
    assert "kpi" in snap and "octopus" in snap
    assert snap["fans"]["total"] == 1
    assert snap["vault"]["total"] == 1


def test_spine_stores_share_dir(tmp_path):
    """همهٔ stores در یک dir می‌نویسند."""
    spine = _spine(tmp_path)
    spine.fans.add("f"); spine.vault.add("t", "h")
    files = sorted(p.name for p in tmp_path.iterdir() if p.suffix == ".json")
    assert "fan_db.json" in files
    assert "vault.json" in files
