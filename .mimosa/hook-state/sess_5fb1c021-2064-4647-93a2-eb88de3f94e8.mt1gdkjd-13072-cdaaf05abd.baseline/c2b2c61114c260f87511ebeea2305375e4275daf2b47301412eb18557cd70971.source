#!/usr/bin/env python3
"""test_ziman_wiring.py — Ziman runtime seam: offline tests, no Telegram/network/spend.

قرارداد:
  * هر تست‌ $0, بدون شبکه، بدون فایل secret.
  * make_ziman_leg / ziman_beat در wiring.py وجود دارند.
  * زیمان هرگز publish/send/pay ندارد.
  * ORGANISM-STATE.ziman نوشته نمی‌شود مگر آرگومان leg داده شود و flag روشن باشد.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest                    # noqa: E402

_OPS = Path(__file__).resolve().parents[1]
for p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

import wiring                    # noqa: E402
from ziman_leg import ZimanLeg   # noqa: E402


# ─── make_ziman_leg ──────────────────────────────────────────────────────────

def test_make_ziman_leg_returns_none_when_flag_off(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "0")
    # singleton را پاک کن تا flag-check تازه اجرا شود
    import wiring as _w
    _w._ZIMAN_STATE["leg"] = None
    result = wiring.make_ziman_leg(organ_table={"ZIMAN": {}})
    assert result is None


def test_make_ziman_leg_returns_leg_when_flag_on(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    import wiring as _w
    _w._ZIMAN_STATE["leg"] = None           # singleton flush
    leg = wiring.make_ziman_leg(organ_table={"ZIMAN": {"floor": 1}})
    assert leg is not None
    assert isinstance(leg, ZimanLeg)
    assert leg.packet.organ == "ZIMAN"


def test_make_ziman_leg_singleton(monkeypatch):
    """make_ziman_leg دوباره همان شیء را برمی‌گرداند."""
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    import wiring as _w
    _w._ZIMAN_STATE["leg"] = None
    a = wiring.make_ziman_leg(organ_table={"ZIMAN": {}})
    b = wiring.make_ziman_leg(organ_table={"ZIMAN": {}})
    assert a is b


# ─── ziman_beat ──────────────────────────────────────────────────────────────

def test_ziman_beat_returns_none_when_flag_off(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "0")
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    assert wiring.ziman_beat(leg, beat=7) is None


def test_ziman_beat_returns_status_only(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    monkeypatch.setenv("CHRONO_ZIMAN_EVERY_N_BEATS", "0")   # هر beat
    # state_path را به tmp هدایت کن (هیچ vault اصلی لمس نشود)
    import wiring as _w
    _w._ZIMAN_STATE["state_path"] = tmp_path / "ORGANISM-STATE.ziman"
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    result = wiring.ziman_beat(leg, beat=7)
    assert result is not None
    assert result["leg_id"] == "ziman-gallery"
    assert result["organ"] == "ZIMAN"
    assert result["propose_only"] is True
    assert result["outward_execution"] is False
    assert result["beat"] == 7


def test_ziman_beat_never_exposes_effector_methods(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    monkeypatch.setenv("CHRONO_ZIMAN_EVERY_N_BEATS", "0")
    import wiring as _w
    _w._ZIMAN_STATE["state_path"] = tmp_path / "ORGANISM-STATE.ziman"
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    wiring.ziman_beat(leg)
    assert not hasattr(leg, "send")
    assert not hasattr(leg, "publish")
    assert not hasattr(leg, "pay")


def test_ziman_beat_writes_state_file(monkeypatch, tmp_path):
    """باید ORGANISM-STATE.ziman را بنویسد (atomic)."""
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    monkeypatch.setenv("CHRONO_ZIMAN_EVERY_N_BEATS", "0")
    import json
    import wiring as _w
    sp = tmp_path / "ORGANISM-STATE.ziman"
    _w._ZIMAN_STATE["state_path"] = sp
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    wiring.ziman_beat(leg, beat=1)
    assert sp.exists()
    data = json.loads(sp.read_text("utf-8"))
    assert data["leg_id"] == "ziman-gallery"
    assert data["propose_only"] is True
    assert data["outward_execution"] is False


def test_ziman_beat_cadence_respected(monkeypatch, tmp_path):
    """با every_n=10 فقط beat % 10 == 0 باید نتیجه بدهد."""
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    monkeypatch.setenv("CHRONO_ZIMAN_EVERY_N_BEATS", "10")
    import wiring as _w
    _w._ZIMAN_STATE["state_path"] = tmp_path / "ORGANISM-STATE.ziman"
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    assert wiring.ziman_beat(leg, beat=7) is None     # 7 % 10 != 0
    assert wiring.ziman_beat(leg, beat=10) is not None  # 10 % 10 == 0


def test_ziman_beat_digest_present(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    monkeypatch.setenv("CHRONO_ZIMAN_EVERY_N_BEATS", "0")
    import wiring as _w
    _w._ZIMAN_STATE["state_path"] = tmp_path / "ORGANISM-STATE.ziman"
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    result = wiring.ziman_beat(leg, beat=5)
    assert "digest" in result
    assert "Ziman" in result["digest"]


def test_ziman_beat_d4_enforced_via_leg(monkeypatch, tmp_path):
    """ZimanLeg D4 flag داخل beat بررسی‌پذیر است."""
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    monkeypatch.setenv("CHRONO_ZIMAN_EVERY_N_BEATS", "0")
    import wiring as _w
    _w._ZIMAN_STATE["state_path"] = tmp_path / "ORGANISM-STATE.ziman"
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=6)
    _ = wiring.ziman_beat(leg, beat=1)
    # D4 از طریق leg.campaign_check قابل بررسی مستقیم
    over = leg.campaign_check(100)
    assert over["approved"] is False


def test_ziman_beat_no_telegram_no_spend(monkeypatch, tmp_path):
    """هیچ متد send/pay/publish در نتیجه یا leg نیست."""
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    monkeypatch.setenv("CHRONO_ZIMAN_EVERY_N_BEATS", "0")
    import wiring as _w
    _w._ZIMAN_STATE["state_path"] = tmp_path / "ORGANISM-STATE.ziman"
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    result = wiring.ziman_beat(leg, beat=3)
    assert result is not None
    # نتیجه هیچ کلید اجرایی ندارد
    for forbidden in ("send", "publish", "pay", "dm", "deploy"):
        assert forbidden not in result


def test_ziman_beat_keeps_biology_unwired_without_owner_verdict(monkeypatch, tmp_path):
    """The runtime seam stays inert; independent biology tests cover the module itself."""
    monkeypatch.setenv("OCTOPUS_WIRE_ZIMAN", "1")
    monkeypatch.setenv("CHRONO_ZIMAN_EVERY_N_BEATS", "0")
    import wiring as _w
    _w._ZIMAN_STATE["state_path"] = tmp_path / "ORGANISM-STATE.ziman"

    class ExplodingDoctor:
        def run_cycle(self, beat=0, trace=None):
            raise AssertionError("unapproved biology wiring reached the doctor")

    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    result = wiring.ziman_beat(leg, beat=1, doctor=ExplodingDoctor())
    assert result is not None
    assert result["biology"] is None
    assert result["outward_execution"] is False
    assert leg.status_snapshot()["biology"] is None
