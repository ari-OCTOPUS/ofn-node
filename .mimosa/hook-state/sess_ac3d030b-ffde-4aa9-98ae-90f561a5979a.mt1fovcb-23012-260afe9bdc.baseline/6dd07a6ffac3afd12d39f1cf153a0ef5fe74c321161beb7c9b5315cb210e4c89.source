#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_off_heartbeat.py — فاز ۳ دستورالعمل ۲۰۲۶-۰۸-۱۶: HEARTSTATE audit fix + OFF heartbeat.

بخش A (audit fix): snapshot فلگ‌درift باید فلگ‌های فایل‌مسلح (ACTIVATION-*.flag) را
گزارش کند تا HEARTSTATE که با *فایل* مسلح است دیگر «خاموش» گزارش نشود (باگِ
ACTIVATION-FLAGS.md §هشدارِ اصلی). مصرف‌کنندهٔ ممیزی (capability_classifier) هم
fallback به همان بخش را یاد می‌گیرد.

بخش B (R9 — هیچی خاموش): هر ۱۰ beat، هر ماژولِ خفته event_name=module.heartbeat
با status=OFF و trace_id در events.jsonl می‌فرستد؛ beatهای غیرمضرب no-op؛ ماژولِ
زنده (spine با فلگِ روشن) از فهرست حذف می‌شود.
"""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("off-heartbeat")

import events           # noqa: E402
import flag_drift       # noqa: E402
import off_heartbeat    # noqa: E402


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


# ── بخش A: HEARTSTATE audit fix ──────────────────────────────────────────────

def test_activation_flags_on_disk_reports_on():
    with _tmp() as td:
        ops = Path(td)
        (ops / "ACTIVATION-HEARTSTATE.flag").write_text("armed 2026-07-23\n", "utf-8")
        (ops / "ACTIVATION-GO-LIVE.flag").write_text("armed\n", "utf-8")
        (ops / "ACTIVATION-GOVERNOR-LLM.flag.off").write_text("legacy off\n", "utf-8")
        act = flag_drift.activation_flags_on_disk(ops)
        assert act == {"GO-LIVE": "ON", "HEARTSTATE": "ON"}, act


def test_snapshot_reports_heartstate_on_when_flag_file_exists():
    with _tmp() as td:
        ops = Path(td)
        (ops / "ACTIVATION-HEARTSTATE.flag").write_text("armed\n", "utf-8")
        cmd = ops / "OCTOPUS-flags.cmd"
        cmd.write_text('@set "OCTOPUS_BEAT_PARALLEL=1"\r\n', "utf-8")
        doc = flag_drift.snapshot(cmd, ops / "flags-loaded-test.json")
        assert doc["activation_flags"]["HEARTSTATE"] == "ON", doc["activation_flags"]
        # پایداری روی دیسک (ممیزی از فایل می‌خواند، نه از خروجیِ حافظه)
        on_disk = json.loads((ops / "flags-loaded-test.json").read_text("utf-8"))
        assert on_disk["activation_flags"]["HEARTSTATE"] == "ON"


def test_classifier_flag_armed_falls_back_to_activation_flags(monkeypatch):
    import capability_classifier as cc
    with _tmp() as td:
        st = Path(td)
        snap = {"schema": "flags-loaded.v1",
                "flags": {},                       # HEARTSTATE_SHADOW در env نیست — همان کوریِ قبلی
                "activation_flags": {"HEARTSTATE": "ON"}}
        (st / "flags-loaded-organism.json").write_text(
            json.dumps(snap, ensure_ascii=False), "utf-8")
        monkeypatch.setattr(cc, "STATE", st)
        assert cc._flag_armed("HEARTSTATE_SHADOW") == "armed"
        # env صریح همچنان برنده است (تقدمِ env حفظ می‌شود)
        snap2 = dict(snap, flags={"HEARTSTATE_SHADOW": "0"})
        (st / "flags-loaded-organism.json").write_text(
            json.dumps(snap2, ensure_ascii=False), "utf-8")
        assert cc._flag_armed("HEARTSTATE_SHADOW") == "disarmed"


# ── بخش B: OFF heartbeat هر ۱۰ beat ─────────────────────────────────────────

def _env(**over):
    base = {"OCTOPUS_WIRE_SPINE": "1", "OCTOPUS_INTERACTION_LOG": "1",
            "OCTOPUS_SYNAPSE_ENABLED": "0", "OCTOPUS_WIRE_CHORD": "0",
            "OCTOPUS_WIRE_ACTION_BRIDGE": "1"}   # caller از ۰۷-۳۰ flag-gated
    base.update(over)
    return base


def test_dormant_modules_reflect_live_flags():
    env = _env()
    assert off_heartbeat.module_live("spine", env) is True          # wired → حذف از خاموش‌ها
    assert off_heartbeat.module_live("intel_spine", env) is True
    assert off_heartbeat.module_live("action_bridge", env) is True  # فلگِ سیم = زنده
    assert off_heartbeat.module_live("synapse", env) is False
    assert off_heartbeat.module_live("chord", env) is False
    assert off_heartbeat.module_live("synapse",
                                     _env(OCTOPUS_SYNAPSE_ENABLED="1")) is True
    assert off_heartbeat.dormant_modules(env) == ["synapse", "chord"]


def test_off_heartbeat_emits_only_every_10th_beat():
    env = _env()
    emitted = 0
    for beat in range(38401, 38421):
        out = off_heartbeat.emit_off_heartbeat(beat, env=env)
        emitted += len(out)
        if beat % 10 == 0:
            assert len(out) == 2, (beat, out)      # synapse + chord
        else:
            assert out == [], (beat, out)
    assert emitted == 4                              # دو مضربِ ۱۰ × دو ماژول


def test_off_heartbeat_event_shape_and_log():
    env = _env()
    out = off_heartbeat.emit_off_heartbeat(38410, env=env)
    assert {e["agent_id"] for e in out} == {"synapse", "chord"}
    for e in out:
        assert e["event_name"] == "module.heartbeat"
        assert e["status"] == "OFF"
        assert e["trace_id"].startswith("hb-off-") and e["trace_id"].endswith("38410")
        assert e["correlation_id"] == e["trace_id"]
        assert e["approval_state"] == "none"
    # واقعاً در events.jsonl نشسته (LOG ایزولهٔ harness) و نامِ رویداد بدونِ drift است
    lines = [json.loads(x) for x in events.LOG.read_text("utf-8").splitlines()[-8:]]
    hb = [x for x in lines if x["event_name"] == "module.heartbeat"]
    assert {x["agent_id"] for x in hb} >= {"synapse", "chord"}


def test_events_taxonomy_accepts_module_heartbeat():
    assert "module.heartbeat" in events.EVENT_NAMES


def test_off_heartbeat_never_raises():
    assert off_heartbeat.tick(0) == []
    assert off_heartbeat.tick(-5) == []
    assert off_heartbeat.emit_off_heartbeat(None, env=_env()) == []


def test_organism_loop_calls_off_heartbeat():
    """سیم‌کشیِ حلقهٔ اصلی زنده مانده (regression guard — فایل داغ، additive)."""
    src = (_HERE.parent / "organism.py").read_text("utf-8")
    assert "off_heartbeat" in src and "_ohb.tick(" in src


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
