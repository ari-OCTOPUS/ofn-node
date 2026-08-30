#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_live4_reservation — پذیرشِ لایهٔ رزرو (LIVE-4-CAPACITY-RESERVATION-01). pytest استاندارد."""
import json, sys, time
from pathlib import Path
import pytest
_OPS = Path(__file__).resolve().parent.parent
for p in (str(_OPS), str(_OPS / "cortex"), str(_OPS / "budget")):
    sys.path.insert(0, p) if p not in sys.path else None
import live4_reservation as LR
import model_router as mr

def _env(tmp_path, monkeypatch, quota_day="2026-08-20", prev="2026-08-19"):
    monkeypatch.setattr(LR, "STATE", tmp_path / "res.json")
    monkeypatch.setattr(LR, "QUOTA", tmp_path / "fugu-quota.json")
    (tmp_path / "fugu-quota.json").write_text(json.dumps({"day": quota_day, "used_total": 2}), encoding="utf-8")
    monkeypatch.setattr(mr, "PAID_LOG", tmp_path / "paid.jsonl")
    return prev

def test_start_requires_observed_reset(tmp_path, monkeypatch):
    _env(tmp_path, monkeypatch, quota_day="2026-08-19", prev="2026-08-19")
    out = LR.start("2026-08-19")
    assert not out["active"] and out["reason"] == "QUOTA-RESET-NOT-OBSERVED"

def test_reset_observed_then_live4_passes_others_deferred(tmp_path, monkeypatch):
    _env(tmp_path, monkeypatch)
    out = LR.start("2026-08-19")
    assert out["active"] and (tmp_path / "QUOTA-RESET-OBSERVATION.json").exists()
    assert LR.gate_paid("live4-b1-base-0") is None          # عبور اختصاصی
    d = LR.gate_paid("orchestrate")                          # ارگانیسم → DEFERRED رسیددار
    assert d["receipt_status"] == "DEFERRED_FOR_LIVE4_RESERVATION"
    assert d["provider_actual"] == "none" and d["cost_aud"] == 0
    assert d["evaluation_eligible"] is False and d["retry_after"]

def test_window_expiry_and_caps(tmp_path, monkeypatch):
    _env(tmp_path, monkeypatch); LR.start("2026-08-19")
    st = json.loads((tmp_path / "res.json").read_text(encoding="utf-8"))
    st["started_at"] = time.time() - 91 * 60                 # انقضای ۹۰ دقیقه
    (tmp_path / "res.json").write_text(json.dumps(st), encoding="utf-8")
    assert not LR.is_active()
    LR.start("2026-08-19")
    st = json.loads((tmp_path / "res.json").read_text(encoding="utf-8"))
    st["provider_attempts"] = LR.CAPS["max_provider_attempts"]   # سقف تلاش
    (tmp_path / "res.json").write_text(json.dumps(st), encoding="utf-8")
    assert not LR.is_active()

def test_router_ask_defers_ordinary_paid_during_window(tmp_path, monkeypatch):
    _env(tmp_path, monkeypatch); LR.start("2026-08-19")
    res = mr.ask(task="synthesize", prompt="یک جمله.", tier="primary")
    assert res.get("ok") is False
    assert res.get("reason") == "DEFERRED_FOR_LIVE4_RESERVATION"
    rows = [json.loads(l) for l in (tmp_path / "paid.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert any(r.get("receipt_status") == "DEFERRED_FOR_LIVE4_RESERVATION" for r in rows)
