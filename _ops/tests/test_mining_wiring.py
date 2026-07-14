#!/usr/bin/env python3
"""test_mining_wiring.py — سیم‌کشیِ پای Mining (flag-gated، STOP-aware، offline).

اثبات می‌کند: flag پیش‌فرض خاموش (Security Gate بسته → خارج از PAPER_FULL_FLAGS)،
ساخت فقط با flag=1، beat = status دو-مغزیِ propose-only، STOP/HALT مقدم، None-leg امن،
و ثبت در مرکز تلگرام اختاپوس. هیچ اثر بیرونی، هیچ شبکه، $0.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

import wiring  # noqa: E402


def test_flag_off_returns_none(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_MINING", "0")
    assert wiring.make_mining_leg() is None
    assert wiring.mining_beat(object()) is None          # beat هم پشتِ همان flag


def test_mining_NOT_in_paper_full_flags():
    # Security Gateِ Mining بسته است → نباید با بوت خودکار روشن شود (verdictِ مالک لازم)
    assert "OCTOPUS_WIRE_MINING" not in wiring.PAPER_FULL_FLAGS


def test_apply_profile_does_not_activate_mining(monkeypatch):
    # apply_profile (پیش‌فرض paper-full) نباید Mining را روشن کند (برخلاف cartographer)
    monkeypatch.delenv("OCTOPUS_WIRE_MINING", raising=False)
    monkeypatch.delenv("OCTOPUS_PROFILE", raising=False)
    wiring.apply_profile()
    assert os.environ.get("OCTOPUS_WIRE_MINING") in (None, "0")


def test_flag_on_builds_incubating_leg(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_MINING", "1")
    leg = wiring.make_mining_leg()
    assert leg is not None
    assert leg.packet.leg_id == "mining-fleet"
    assert leg.money_link == "incubating"                # organ در budgets نیست
    for m in ("send", "publish", "pay", "trade"):
        assert not hasattr(leg, m)


def test_beat_returns_contained_status(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_MINING", "1")
    leg = wiring.make_mining_leg()
    st = wiring.mining_beat(leg, beat=7)
    assert st is not None
    assert st["organ"] == "MINING"
    assert st["propose_only"] is True
    assert st["outward_execution"] is False
    assert st["read_only"] is True
    assert st["beat"] == 7
    assert st["brains"] == ["hardware_control", "coin_discovery"]


def test_beat_none_leg_safe(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_MINING", "1")
    assert wiring.mining_beat(None) is None


def test_stop_organism_wins(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_MINING", "1")
    leg = wiring.make_mining_leg()
    monkeypatch.setattr(wiring.opslib, "halted", lambda: True)   # STOP/HALT مقدم
    assert wiring.mining_beat(leg) is None


def test_wire_summary_includes_mining(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_MINING", "1")
    assert wiring.wire_summary()["wire_mining"] is True


def test_registered_in_central_telegram():
    # محیطِ تلگرام از طریقِ اختاپوس: کلیدِ 'mining' در مرکز ثبت شده
    import importlib
    render = importlib.import_module("telegram_center.render")
    center = importlib.import_module("telegram_center.center")
    assert "mining" in render.LEGS
    assert render.LEG_ICONS["mining"] == "⛏"
    assert "mining" in center.LEG_KEYS


def test_render_maps_mining_status():
    # UI: _collect_legs باید بلوکِ miningِ ORGANISM-STATE را به سلولِ دایجست نگاشت کند
    import importlib
    render = importlib.import_module("telegram_center.render")
    feeds = {"organism": {"mining": {
        "electricity_mood": "🔴", "electricity_safe": False,
        "nodes_total": 6, "nodes_running": 0, "hashrate_measured": False,
        "thermal_warn": ["OPI-1"]}}}
    legs = render._collect_legs(feeds)
    m = legs["mining"]
    assert m["status"] == "🔴"
    assert "0/6" in m["detail"]
    assert "دمای بالا" in m.get("next", "")
