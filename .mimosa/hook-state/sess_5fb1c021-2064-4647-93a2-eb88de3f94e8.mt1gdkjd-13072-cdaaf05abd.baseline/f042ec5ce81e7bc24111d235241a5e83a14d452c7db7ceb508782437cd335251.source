#!/usr/bin/env python3
"""test_cartographer_wiring.py — سیم‌کشیِ پای نقشه‌بردار (flag-gated، STOP-aware، offline).

اثبات می‌کند: flag پیش‌فرض خاموش (incubating)، ساخت فقط با flag=1، beat = status محتوا-آزادِ
propose-only، STOP/HALT مقدم، None-leg امن. هیچ اثرِ بیرونی.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

import wiring  # noqa: E402


def _isolate_stop_paths(monkeypatch) -> None:
    """kill-switch را خنثی کن: هیچ STOP/HALT زندهٔ ارگانیسمِ واقعی لمس نشود
    (همان الگوی test_route_scorer_wire.py::_isolate). cartographer_beat قبل از
    ساختِ status، opslib.STOP_ORGANISM.exists() و opslib.halted() (که HALT_ALL،
    STOP_ARCHITECT و STOP_METABOLIC را می‌بیند) را چک می‌کند؛ بی‌ایزوله، یک
    HALT/restart واقعیِ هم‌پوشان با اجرای این تست، beat را به None می‌کِشد و
    تستِ محتوا-محورِ زیر بی‌آنکه باگی باشد قرمز چشمک می‌زند."""
    d = Path(tempfile.mkdtemp(prefix="cartographer-wire-test-"))
    monkeypatch.setattr(wiring.opslib, "STOP_ORGANISM", d / "STOP-ORGANISM")
    monkeypatch.setattr(wiring.opslib, "HALT_ALL", d / "HALT-ALL")
    monkeypatch.setattr(wiring.opslib, "STOP_ARCHITECT", d / "STOP-ARCHITECT")
    monkeypatch.setattr(wiring.opslib, "STOP_METABOLIC", d / "STOP-METABOLIC")


def test_flag_off_returns_none(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CARTOGRAPHER", "0")
    assert wiring.make_cartographer_leg() is None
    assert wiring.cartographer_beat(object()) is None       # beat هم پشتِ همان flag


def test_boot_coupled_in_paper_full_flags():
    # verdictِ مالک 2026-07-12: با بوتِ اختاپوس روشن شود → در PAPER_FULL_FLAGS
    assert "OCTOPUS_WIRE_CARTOGRAPHER" in wiring.PAPER_FULL_FLAGS


def test_apply_profile_activates_on_boot(monkeypatch):
    # apply_profile (پیش‌فرض paper-full) باید فلگ را روشن کند اگر ست‌نشده باشد
    monkeypatch.delenv("OCTOPUS_WIRE_CARTOGRAPHER", raising=False)
    monkeypatch.delenv("OCTOPUS_PROFILE", raising=False)
    wiring.apply_profile()
    assert os.environ.get("OCTOPUS_WIRE_CARTOGRAPHER") == "1"


def test_registered_in_central_telegram():
    # محیطِ تلگرام از طریقِ اختاپوس: کلیدِ 'cartographer' در مرکز ثبت شده
    import importlib
    render = importlib.import_module("telegram_center.render")
    center = importlib.import_module("telegram_center.center")
    assert "cartographer" in render.LEGS
    assert "cartographer" in render.LEG_ICONS
    assert "cartographer" in center.LEG_KEYS


def test_flag_on_builds_incubating_leg(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CARTOGRAPHER", "1")
    leg = wiring.make_cartographer_leg()
    assert leg is not None
    assert leg.packet.leg_id == "vault-cartographer"
    assert leg.money_link == "incubating"                   # organ در budgets نیست
    for m in ("send", "publish", "pay"):
        assert not hasattr(leg, m)


def test_beat_returns_contained_status(monkeypatch):
    _isolate_stop_paths(monkeypatch)
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


def test_beat_includes_real_drift_pulse(monkeypatch):
    # عملکردِ واقعی: beat باید سیگنالِ drift-pulse را از repoِ واقعی برگرداند
    _isolate_stop_paths(monkeypatch)
    monkeypatch.setenv("OCTOPUS_WIRE_CARTOGRAPHER", "1")
    leg = wiring.make_cartographer_leg()
    st = wiring.cartographer_beat(leg, beat=1)
    assert st is not None
    for k in ("map_updated", "map_age_days", "map_stale", "drift_files",
              "refresh_recommended", "mood"):
        assert k in st, f"missing drift-pulse field: {k}"
    assert st["mood"] in ("🟢", "🟡", "🔴")
    assert isinstance(st["refresh_recommended"], bool)


def test_render_maps_cartographer_drift_pulse():
    # UI: _collect_legs باید بلوکِ cartographerِ ORGANISM-STATE را به سلولِ دایجست نگاشت کند
    import importlib
    render = importlib.import_module("telegram_center.render")
    feeds = {"organism": {"cartographer": {
        "mood": "🔴", "map_age_days": 21, "drift_files": 7, "refresh_recommended": True}}}
    legs = render._collect_legs(feeds)
    c = legs["cartographer"]
    assert c["status"] == "🔴"
    assert "drift 7" in c["detail"] and "21d" in c["detail"]
    assert "refresh" in c.get("next", "")
