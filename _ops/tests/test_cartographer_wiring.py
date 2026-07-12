#!/usr/bin/env python3
"""test_cartographer_wiring.py — سیم‌کشیِ پای نقشه‌بردار (flag-gated، STOP-aware، offline).

اثبات می‌کند: flag پیش‌فرض خاموش (incubating)، ساخت فقط با flag=1، beat = status محتوا-آزادِ
propose-only، STOP/HALT مقدم، None-leg امن. هیچ اثرِ بیرونی.
"""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

import wiring  # noqa: E402


def test_flag_off_returns_none(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CARTOGRAPHER", "0")
    assert wiring.make_cartographer_leg() is None
    assert wiring.cartographer_beat(object()) is None       # beat هم پشتِ همان flag


def test_not_in_paper_full_flags():
    # عمداً default-off: نباید در PAPER_FULL_FLAGS باشد (تا گام ۵/verdict مالک)
    assert "OCTOPUS_WIRE_CARTOGRAPHER" not in wiring.PAPER_FULL_FLAGS


def test_flag_on_builds_incubating_leg(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CARTOGRAPHER", "1")
    leg = wiring.make_cartographer_leg()
    assert leg is not None
    assert leg.packet.leg_id == "vault-cartographer"
    assert leg.money_link == "incubating"                   # organ در budgets نیست
    for m in ("send", "publish", "pay"):
        assert not hasattr(leg, m)


def test_beat_returns_contained_status(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CARTOGRAPHER", "1")
    leg = wiring.make_cartographer_leg()
    st = wiring.cartographer_beat(leg, beat=3)
    assert st is not None
    assert st["organ"] == "CARTOGRAPHER"
    assert st["propose_only"] is True
    assert st["outward_execution"] is False
    assert st["read_only"] is True
    assert st["beat"] == 3


def test_beat_none_leg_safe(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CARTOGRAPHER", "1")
    assert wiring.cartographer_beat(None) is None


def test_stop_organism_wins(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CARTOGRAPHER", "1")
    leg = wiring.make_cartographer_leg()
    monkeypatch.setattr(wiring.opslib, "halted", lambda: True)   # STOP/HALT مقدم
    assert wiring.cartographer_beat(leg) is None
