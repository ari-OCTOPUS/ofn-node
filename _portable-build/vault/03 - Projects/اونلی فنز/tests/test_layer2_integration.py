#!/usr/bin/env python3
"""test_layer2_integration.py — تست‌های لایهٔ ۲: Fan/Vault/KPI/FAQ/Octopus.

تضمین می‌کند:
  - fan_admin dispatch کار می‌کند
  - vault_admin dispatch + containment guard کار می‌کند
  - FAQ engine pattern matching + auto-draft به pipeline
  - Octopus bridge fallback isolated وقتی orchestrator غایب
  - acquisition_pipeline از vault draft می‌زند (لایهٔ ۲)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
_LANGAR = _HERE.parent / "langar"
for p in (_BRAIN, _LANGAR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from store import FanDB, VaultBank, KPIRollup, OctopusState, DataSpine  # noqa: E402
import fan_admin  # noqa: E402
import vault_admin  # noqa: E402
from faq_engine import classify, draft_for, auto_draft_to_pipeline  # noqa: E402
from dm_pipeline import DmPipeline  # noqa: E402
from acquisition_pipeline import AcquisitionPipeline  # noqa: E402


# ── fan_admin dispatch ────────────────────────────────────────────────────

def test_fan_admin_add_and_stats(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    fan_admin.handle_fan("/fan_add", "test-fan reddit", db=db)
    msg = fan_admin.handle_fan("/fan_stats", "", db=db)
    assert "total: 1" in msg


def test_fan_admin_buy_updates_segment(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    fan_admin.handle_fan("/fan_add", "vip-fan of", db=db)
    msg = fan_admin.handle_fan("/fan_buy", "vip-fan 60 ppv", db=db)
    assert "vip" in msg
    assert "$60.00" in msg


def test_fan_admin_list_by_segment(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    db.add("vip-1"); db.record_purchase("vip-1", 100)
    db.add("lurker-1")
    msg = fan_admin.handle_fan("/fan_list", "vip", db=db)
    assert "vip-1" in msg
    assert "lurker-1" not in msg


def test_fan_admin_unknown_returns_help(tmp_path):
    db = FanDB(path=tmp_path / "f.json")
    msg = fan_admin.handle_fan("/fan_unknown", "", db=db)
    assert "Fan CRM" in msg


# ── vault_admin dispatch ──────────────────────────────────────────────────

def test_vault_admin_add_and_list(tmp_path):
    vb = VaultBank(path=tmp_path / "v.json")
    vault_admin.handle_vault("/vault_add", "pedicure \"Arch of Day\" reddit", bank=vb)
    msg = vault_admin.handle_vault("/vault_list", "", bank=vb)
    assert "pedicure" in msg


def test_vault_admin_blocked_content(tmp_path):
    """vault_add با کلمهٔ banned باید flag شود."""
    vb = VaultBank(path=tmp_path / "v.json")
    msg = vault_admin.handle_vault("/vault_add", "tag \"buy my onlyfans sub\" reddit", bank=vb)
    assert "flagged" in msg or "containment" in msg


def test_vault_admin_metric(tmp_path):
    vb = VaultBank(path=tmp_path / "v.json")
    vid = vb.add("tag", "hook")["id"]
    msg = vault_admin.handle_vault("/vault_metric", f"{vid} 50 5 2", bank=vb)
    assert "50" in msg


# ── FAQ engine ────────────────────────────────────────────────────────────

def test_classify_price_question():
    assert classify("how much is it?") == ("ppv_offer", "price question")


def test_classify_custom_request():
    assert classify("do you do custom content?") == ("custom_reply", "custom request")


def test_classify_welcome():
    r = classify("just subscribed, hi!")
    assert r is not None and r[0] == "welcome"


def test_classify_unknown_returns_none():
    assert classify("the weather is nice today") is None


def test_classify_short_text_ignored():
    assert classify("hi") is None   # خیلی کوتاه


def test_draft_for_has_placeholders():
    """draftهای FAQ باید [placeholders] داشته باشند که آری پر کند."""
    d = draft_for("how much?")
    assert d is not None
    assert "auto_drafted" in d
    assert "[" in d["body"]   # placeholder نشانه‌دار


def test_draft_for_unknown_returns_none():
    assert draft_for("random unrelated text here") is None


def test_auto_draft_to_pipeline_creates_pending(tmp_path):
    pipe = DmPipeline(store_path=tmp_path / "dm.json")
    r = auto_draft_to_pipeline("how much for content?", pipe)
    assert r["ok"] is True
    assert r["matched"] is True
    assert "id" in r
    # باید pending_review باشد
    item = pipe._find(r["id"])
    assert item["status"] == "pending_review"


def test_auto_draft_unmatched_no_creation(tmp_path):
    pipe = DmPipeline(store_path=tmp_path / "dm.json")
    r = auto_draft_to_pipeline("totally random unrelated message", pipe)
    assert r["ok"] is True
    assert r["matched"] is False
    assert len(pipe.pending()) == 0
    assert len(pipe.by_status("pending_review")) == 0


def test_faq_draft_passes_containment(tmp_path):
    """draftهای FAQ نباید کلمهٔ banned داشته باشند."""
    pipe = DmPipeline(store_path=tmp_path / "dm.json")
    for q in ["how much?", "do you do custom?", "just subscribed hi!"]:
        r = auto_draft_to_pipeline(q, pipe)
        if r.get("matched"):
            item = pipe._find(r["id"])
            assert not item["flagged"], f"FAQ draft flagged: {q}"


# ── Octopus state ─────────────────────────────────────────────────────────

def test_octopus_isolated_when_orchestrator_absent(tmp_path):
    """وقتی orchestrator import نشد، isolated heartbeat ثبت می‌شود."""
    o = OctopusState(path=tmp_path / "o.json")
    r = o.mark_isolated("test: no _ops")
    assert r["isolated"] is True
    snap = o.snapshot()
    assert snap["neural_available"] is False


def test_octopus_snapshot_returns_dict(tmp_path):
    o = OctopusState(path=tmp_path / "o.json")
    snap = o.snapshot()
    assert "beat" in snap
    assert "protective" in snap
    assert "pain" in snap


# ── acquisition_pipeline vault integration ────────────────────────────────

def test_pipeline_seeds_from_vault(tmp_path):
    """auto_plan باید از vault assetها draft بزند اگه vault وصل باشد."""
    vb = VaultBank(path=tmp_path / "v.json")
    vb.add("pedicure-asmr", "Arch of the Day — soft", channel="reddit")
    vb.add("nylon-soft", "Sole Sunday ep", channel="x")
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None, vault=vb)
    items = pipe.auto_plan(2)
    # حداقل یکی باید از vault آمده باشد (vault_id دارد)
    vault_items = [i for i in items if i.get("vault_id")]
    assert len(vault_items) >= 1


def test_pipeline_fallback_to_safe_hooks_when_vault_empty(tmp_path):
    """اگه vault خالی باشد، fallback به _SAFE_HOOKS."""
    vb = VaultBank(path=tmp_path / "v.json")   # خالی
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None, vault=vb)
    items = pipe.auto_plan(2)
    assert len(items) == 2
    # هیچ‌کدام vault_id نباید داشته باشند
    assert all(not i.get("vault_id") for i in items)


def test_pipeline_finalize_marks_vault_used(tmp_path):
    """finalize باید vault.mark_used صدا بزند."""
    vb = VaultBank(path=tmp_path / "v.json")
    vb.add("tag", "hook", channel="reddit")
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None, vault=vb)
    items = pipe.auto_plan(1)
    vid = items[0].get("vault_id")
    assert vid is not None
    pipe.approve(items[0]["id"])
    pipe.finalize(items[0]["id"])
    # used_count باید ۱ باشد
    asset = vb.all()[0]
    assert asset["used_count"] == 1


def test_pipeline_backward_compat_without_vault(tmp_path):
    """بدون vault (backward-compat)، pipeline مثل قبل کار می‌کند."""
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None, vault=None)
    items = pipe.auto_plan(2)
    assert len(items) == 2


# ── DataSpine full integration ────────────────────────────────────────────

def test_spine_end_to_end(tmp_path):
    """یک سناریوی کامل: fan اضافه، خرید، vault draft، KPI ثبت."""
    spine = DataSpine(store_dir=tmp_path)
    # fan
    spine.fans.add("customer-1", "of")
    spine.fans.record_purchase("customer-1", 25.0, "ppv")
    # vault
    spine.vault.add("pedicure", "Nice arch today", channel="reddit")
    # pipeline از vault
    pipe = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None, vault=spine.vault)
    drafts = pipe.auto_plan(1)
    assert len(drafts) == 1
    # KPI
    spine.kpi.record(revenue_usd=25, ppv_unlocks=1, posts=1,
                     fan_summary=spine.fans.summary())
    # verify
    snap = spine.full_snapshot()
    assert snap["fans"]["total"] == 1
    assert snap["fans"]["total_ltv_usd"] == 25.0
    assert snap["vault"]["total"] == 1
    assert snap["kpi"]["total_revenue_usd"] == 25.0
