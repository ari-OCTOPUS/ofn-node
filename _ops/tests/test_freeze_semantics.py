#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_freeze_semantics — پذیرشِ گیتِ recovery (FREEZE-ROOT-CAUSE-AND-BOUNDED-RECOVERY-01).
بدون تماس با provider: _ask_paid در حالتِ release با mock اثباتِ رسیدن است."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_OPS = Path(__file__).resolve().parent.parent
for p in (str(_OPS), str(_OPS / "cortex"), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

import opslib
import model_router as mr


def _frozen_env(tmp_path, monkeypatch):
    flag = tmp_path / "FREEZE.flag"
    flag.write_text("2026-08-16T20:09:05+10:00 settle failed for ARCHITECT_SYS: [Errno 22] test\n", encoding="utf-8")
    monkeypatch.setattr(opslib, "FREEZE_FLAG", flag)
    monkeypatch.setattr(opslib, "BUDGET_DIR", tmp_path)
    monkeypatch.setattr(mr, "PAID_LOG", tmp_path / "paid-calls.jsonl")
    return flag


def test_1_frozen_paid_request_block_receipted_not_silent(tmp_path, monkeypatch):
    flag = _frozen_env(tmp_path, monkeypatch)
    def _no_paid(*a, **k):  # نباید در حالت یخ اصلاً صدا شود
        raise AssertionError("paid path reached while frozen")
    monkeypatch.setattr(mr, "_ask_paid", _no_paid)
    res = mr.ask(task="live4-test", prompt="پیشنهاد کوتاه بده.", tier="secondary")
    assert res.get("ok") is True  # موجودیت زنده می‌ماند (local)
    assert res.get("fallback_reason") == "PAID_PATH_BLOCKED_BY_FREEZE"
    assert res.get("provider_actual") == "local"
    assert res.get("evaluation_eligible") is False
    rows = [json.loads(l) for l in (tmp_path / "paid-calls.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    blk = [r for r in rows if r.get("receipt_status") == "PAID_PATH_BLOCKED_BY_FREEZE"]
    assert blk, rows
    r = blk[-1]
    for k in ("trace_id", "freeze_id", "freeze_created_at", "freeze_reason_code",
              "freeze_scope", "freeze_expiry_or_review_condition"):
        assert r.get(k), f"missing {k}"


def test_2_release_receipted_then_paid_reachable(tmp_path, monkeypatch):
    flag = _frozen_env(tmp_path, monkeypatch)
    out = opslib.release_freeze("OWNER_APPROVES_FREEZE_RELEASE_TEST")
    assert out["ok"]
    assert (tmp_path / "FREEZE-RELEASE-RECEIPT.json").exists()
    assert not flag.exists() and list(tmp_path.glob("FREEZE.flag.released-*")), "flag archived, not deleted"
    calls = {"n": 0}
    def _fake_paid(tier, prompt, system, max_tokens, task=None):
        calls["n"] += 1
        return {"text": "paid-ok-probe", "model": "deepseek-v4-flash",
                "cost_usd": 0.0004, "ok": True}
    monkeypatch.setattr(mr, "_ask_paid", _fake_paid)
    monkeypatch.setattr(mr, "keys_present", lambda: {"fugu": False, "deepseek": True, "glm": False})
    res = mr.ask(task="live4-test", prompt="پیشنهاد کوتاه بده.", tier="secondary")
    assert calls["n"] == 1 and res.get("text") == "paid-ok-probe"
    assert "fallback_reason" not in res and res.get("evaluation_eligible") is not False


def test_3_tier_map_primary_is_deepseek(tmp_path, monkeypatch):
    _frozen_env(tmp_path, monkeypatch)
    monkeypatch.setattr(mr, "keys_present", lambda: {"fugu": False, "deepseek": True, "glm": False})
    # primary باید فقط با کلید deepseek مجاز باشد (سیاست ثبت‌شدهٔ 2026-08-15)
    src = mr.__dict__["_ask_impl"].__code__.co_consts  # static sanity: map in source
    assert 'bool(kp.get("deepseek")' in Path(mr.__file__).read_text(encoding="utf-8")


def test_4_freeze_state_structured(tmp_path, monkeypatch):
    _frozen_env(tmp_path, monkeypatch)
    st = opslib.freeze_state()
    assert st and st["freeze_reason_code"] == "LEGACY_UNSTRUCTURED"
    assert st["freeze_scope"] and "owner" in st["freeze_expiry_or_review_condition"]
