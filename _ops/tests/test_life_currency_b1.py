# -*- coding: utf-8 -*-
"""تست‌های B1 (سیم‌کشی daily_cap) — رأی مالک 2026-08-19؛ گیت ماشینی اعمال."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "heart"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "budget"))

import opslib  # noqa: E402
from heart.life_currency import daily_pool, plan  # noqa: E402


def test_cardiac_source_wins_when_present(tmp_path, monkeypatch):
    (tmp_path / "cardiac-budget.json").write_text(
        json.dumps({"date": "2026-08-19", "spent": 1, "resting": 0, "daily_cap": 42.0}),
        encoding="utf-8")
    monkeypatch.setattr(opslib, "STATE_DIR", tmp_path)
    dp = daily_pool()
    assert dp["daily_cap"] == 42.0
    assert dp["source"] == "cardiac-budget.json"


def test_budgets_fallback_when_cardiac_has_no_key(tmp_path, monkeypatch):
    (tmp_path / "cardiac-budget.json").write_text(
        json.dumps({"date": "2026-08-19", "spent": 1, "resting": 0}), encoding="utf-8")
    monkeypatch.setattr(opslib, "STATE_DIR", tmp_path)
    monkeypatch.setattr(opslib, "load_budgets",
                        lambda: {"global": {"life_currency_daily_cap": 500.0}})
    dp = daily_pool()
    assert dp["daily_cap"] == 500.0
    assert dp["source"] == "budgets.yaml"
    assert dp["known"] is True


def test_zero_when_no_source(tmp_path, monkeypatch):
    (tmp_path / "cardiac-budget.json").write_text(
        json.dumps({"date": "2026-08-19"}), encoding="utf-8")
    monkeypatch.setattr(opslib, "STATE_DIR", tmp_path)
    monkeypatch.setattr(opslib, "load_budgets", lambda: {"global": {}})
    dp = daily_pool()
    assert dp["daily_cap"] == 0.0
    assert dp["known"] is False


def test_plan_allocates_with_fallback(tmp_path, monkeypatch):
    (tmp_path / "cardiac-budget.json").write_text(
        json.dumps({"date": "2026-08-19", "spent": 1, "resting": 0}), encoding="utf-8")
    monkeypatch.setattr(opslib, "STATE_DIR", tmp_path)
    monkeypatch.setattr(opslib, "load_budgets",
                        lambda: {"global": {"life_currency_daily_cap": 1000.0}})
    p = plan(color="GREEN")
    assert p["daily_cap"] == 1000.0
    assert len(p.get("members") or {}) == 11
    assert p["beat_pool"] > 0.0


def test_explicit_zero_cardiac_is_respected_not_overridden(tmp_path, monkeypatch):
    # cardiac صفرِ عمدی نوشته → fallback نباید جایگزین شود
    (tmp_path / "cardiac-budget.json").write_text(
        json.dumps({"date": "2026-08-19", "daily_cap": 0.0}), encoding="utf-8")
    monkeypatch.setattr(opslib, "STATE_DIR", tmp_path)
    monkeypatch.setattr(opslib, "load_budgets",
                        lambda: {"global": {"life_currency_daily_cap": 500.0}})
    dp = daily_pool()
    assert dp["daily_cap"] == 0.0
    assert dp["source"] == "cardiac-budget.json"
