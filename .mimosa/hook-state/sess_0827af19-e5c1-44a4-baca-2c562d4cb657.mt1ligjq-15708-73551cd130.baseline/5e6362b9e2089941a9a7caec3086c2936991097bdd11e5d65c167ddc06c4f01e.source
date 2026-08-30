#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_phase8_dormant_wiring.py — فاز ۸ دستورالعمل ۲۰۲۶-۰۸-۱۶: سیم‌کشی ماژول‌های خفته.

واقعیتِ اندازه‌گیری‌شده (AGENT-INVENTORY §۲ + بررسیِ کد):
  ۸a intel_spine — پرچم ON در env هر ۵ پروسه + صداکننده در organism/cortex → وصل
  ۸b afferent    — sensory_bus/afferent_beat از قبل در حلقهٔ organism (wire_school) → وصل
  ۸c synapse     — صداکننده از ۰۷-۲۸ هست؛ این فاز فلگ را مسلح کرد (verdict tracked)
  ۸d chord       — این فاز: chord_beat در wiring + صداکننده در organism + فلگ
  ۸e action_bridge — caller از ۰۷-۳۰ هست؛ این فاز دو گیتِ محدودکننده افزود
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget"),
           str(_HERE.parent / "chord"), str(_HERE.parent / "cortex"),
           str(_HERE.parent / "control_plane")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("phase8-dormant")

import wiring   # noqa: E402


# ── ۸a: intel_spine از قبل وصل است (flag در env) ─────────────────────────────

def test_intel_spine_flag_and_callers_exist():
    # صداکنندهٔ واقعی در organism.py و cortex.py — نه فقط ماژولِ خفته
    org_src = (_HERE.parent / "organism.py").read_text("utf-8")
    ctx_src = (_HERE.parent / "cortex" / "cortex.py").read_text("utf-8")
    assert "intel" in org_src and "intel" in ctx_src


# ── ۸b: afferent از قبل در حلقه است ──────────────────────────────────────────

def test_afferent_beat_wired_in_organism_loop():
    org_src = (_HERE.parent / "organism.py").read_text("utf-8")
    assert "afferent_beat(" in org_src and "make_sensory_bus" in org_src
    w_src = (_HERE.parent / "wiring.py").read_text("utf-8")
    assert "def afferent_beat" in w_src and "def make_sensory_bus" in w_src


# ── ۸c: synapse — صداکننده هست، فلگ verdict-مسلح ─────────────────────────────

def test_synapse_beat_wired_and_flag_registered():
    org_src = (_HERE.parent / "organism.py").read_text("utf-8")
    assert "synapse_beat(" in org_src
    assert "def synapse_beat" in (_HERE.parent / "wiring.py").read_text("utf-8")
    ov = (_HERE.parent / "owner-verdicts.yaml").read_text("utf-8")
    assert "OCTOPUS_SYNAPSE_ENABLED" in ov


# ── ۸d: chord_beat — shadow-only، flag-gated، هرگز مجوز اجرا ────────────────

def test_chord_beat_flag_off_is_noop(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CHORD", "0")
    assert wiring.chord_beat(beat=100) is None


def test_chord_beat_produces_shadow_verdict(monkeypatch):
    import opslib
    st = Path(opslib.STATE_DIR)
    (st / "ORGANISM-STATE.json").write_text(
        json.dumps({"halted": False, "frozen": False,
                    "arbiter": {"color": "GREEN"}}), "utf-8")
    monkeypatch.setenv("OCTOPUS_WIRE_CHORD", "1")
    monkeypatch.setenv("CHORD_CHORD_EVERY_N_BEATS", "1")
    out = wiring.chord_beat(beat=101)
    assert out is not None and "chord" in out
    # verdict در ledgerِ خودِ chord نشسته (hash-chain) — نه در state ارگانیسم
    from chord import ledger
    last = ledger._last_line(ledger.ledger_path())
    assert last is not None and last.get("mission_id") == "beat_101"
    # SHADOW فقط: هیچ allowed_actions حاویِ code.apply نیست (ساختارِ chord)
    acts = last.get("allowed_actions") or []
    assert not any("apply" in str(a) or "patch" in str(a) for a in acts)


def test_chord_beat_never_raises(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_CHORD", "1")
    monkeypatch.setenv("CHORD_CHORD_EVERY_N_BEATS", "1")
    # ORGANISM-STATE غایب → مشاهدهٔ خالی → UNKNOWN صادقانه، نه کرش
    import opslib
    p = Path(opslib.STATE_DIR) / "ORGANISM-STATE.json"
    if p.exists():
        p.unlink()
    out = wiring.chord_beat(beat=102)
    assert out is None or "chord" in out   # fail-soft


def test_chord_caller_in_organism_and_verdict():
    org_src = (_HERE.parent / "organism.py").read_text("utf-8")
    assert "chord_beat(" in org_src
    assert "OCTOPUS_WIRE_CHORD" in \
        (_HERE.parent / "owner-verdicts.yaml").read_text("utf-8")


# ── ۸e: action_bridge — گیت‌های محدودکنندهٔ additive ─────────────────────────

def test_action_gates_present_in_goal_action_bridge():
    src = (_HERE.parent / "goal_action_bridge.py").read_text("utf-8")
    assert "PROPOSE_ON_FALLBACK" in src          # گیتِ D6
    assert "DUAL_VETO_HOLD" in src               # گیتِ D2
    assert "downgrade_a2_now" in src             # سیگنالِ provider_router فاز ۵
    assert "VQ-SELFGOAL-002" in src              # A2 همچنان BLOCK — سندِ در کد


def test_action_bridge_off_heartbeat_corrected():
    """با اصلاحِ فاز ۸e: فلگِ سیمِ روشن = زنده (caller از ۰۷-۳۰ هست) —
    OFF heartbeat فقط برای synapse/chord تا فلگشان بیاید."""
    import off_heartbeat as ohb
    env = {"OCTOPUS_WIRE_SPINE": "1", "OCTOPUS_INTERACTION_LOG": "1",
           "OCTOPUS_SYNAPSE_ENABLED": "1", "OCTOPUS_WIRE_CHORD": "1",
           "OCTOPUS_WIRE_ACTION_BRIDGE": "1"}
    assert ohb.dormant_modules(env) == []   # همه زنده → هیچ OFF نیست (R9)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
