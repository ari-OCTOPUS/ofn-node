"""OWNER_ABSENT + Conservation Mode — the stand-without-slipping locks
(OCTOPUS-AUTONOMY-SPEC §3/§6).

Pins: threshold tiers; zero sends in conservation EVEN WITHIN CAP (the
hook sits before cap and before release_and_settle so nothing is consumed);
corrupt conservation state = deny (fail-closed); doctor silence >=3 ticks
forces conservation on; the OWNER-QUEUE accumulates with stable ids; and
owner_absence has no merge/push/send paths at all."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import owner_absence as oa  # noqa: E402
import outbound_worker as ow  # noqa: E402


# ── آستانه‌ها ────────────────────────────────────────────────────────────────

def test_tier_ladder() -> None:
    assert oa.absence_tier(3.0) == "present"
    assert oa.absence_tier(25.0) == "soft"
    assert oa.absence_tier(8 * 24.0) == "hard"
    assert oa.absence_tier(31 * 24.0) == "deep"
    assert oa.absence_tier(None) == "hard"  # UNKNOWN → conservative


def test_hard_tier_and_doctor_silence_turn_conservation_on() -> None:
    v = oa.evaluate_conservation(31 * 24.0, doctor_report_age_h=0.5)
    assert v["on"] and "tier=deep" in v["reason"]
    v = oa.evaluate_conservation(1.0, doctor_report_age_h=4.0)
    assert v["on"] and "doctor-silent" in v["reason"]


def test_present_owner_keeps_sends_possible() -> None:
    v = oa.evaluate_conservation(2.0, doctor_report_age_h=0.5)
    assert not v["on"]


# ── فایل حالت: خواندنِ گیتِ ارسال ──────────────────────────────────────────

def test_missing_state_file_means_off(tmp_path) -> None:
    assert oa.conservation_active(tmp_path) == ""


def test_corrupt_state_file_means_on_fail_closed(tmp_path) -> None:
    (tmp_path / "conservation-mode.json").write_text("{broken",
                                                     encoding="utf-8")
    assert "unreadable" in oa.conservation_active(tmp_path)


def test_on_state_gives_reason(tmp_path) -> None:
    oa.write_conservation({"on": True, "reason": "owner-absent tier=hard"},
                          tmp_path)
    assert "tier=hard" in oa.conservation_active(tmp_path)


# ── قلاب: صفر ارسال در Conservation، حتی زیر سقف ────────────────────────────

def _send_with_state(tmp_path) -> dict:
    env_flag = "1"
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = env_flag
    old_state = oa.opslib.STATE_DIR
    oa.opslib.STATE_DIR = tmp_path
    try:
        return ow.send_one("e-test", {"lead_id": "lead:x"}, gate=None)
    finally:
        oa.opslib.STATE_DIR = old_state
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)


def test_conservation_denies_send_within_cap(tmp_path) -> None:
    oa.write_conservation({"on": True, "reason": "owner-absent tier=hard"},
                          tmp_path)
    res = _send_with_state(tmp_path)
    assert res["sent"] is False
    assert res["status"] == "conservation-denied"
    assert "tier=hard" in res["gate_reason"]


def test_no_conservation_no_behavior_change(tmp_path) -> None:
    # بدون فایل حالت، مسیرِ قبلی برقرار است: deny از conservation نمی‌آید؛
    # ادامهٔ مسیر (gate/transport) خودش تعیین‌کننده است — این host بدون
    # lead_effect_gate است پس worker_error انتظار می‌رود، نه conservation.
    res = _send_with_state(tmp_path)
    assert res["status"] != "conservation-denied"


# ── OWNER-QUEUE ──────────────────────────────────────────────────────────────

def test_owner_queue_accumulates_with_stable_ids(tmp_path) -> None:
    doc = tmp_path / "doctor" / "report.json"
    doc.parent.mkdir(parents=True)
    doc.write_text(json.dumps({
        "generated_at": "2026-09-03T00:00:00Z",
        "measurements": [
            {"name": "unit.octopus-x", "verdict": "unhealthy",
             "detail": "Result=exit-code", "command": "systemctl show x"},
            {"name": "flags.managed", "verdict": "unknown",
             "detail": "missing", "command": "cat f"},
        ]}), encoding="utf-8")
    text = oa.build_owner_queue(
        {"last_action": "2026-09-02T00:00:00Z", "age_h": 26.0},
        {"on": True, "reason": "owner-absent tier=hard"},
        doctor_report=doc)
    assert "OQ-unit-octopus-x" in text and "OQ-flags-managed" in text
    assert "OQ-conservation" in text  # خودِ conservation هم آیتم است


def test_tick_run_writes_both_files_and_honest_json(tmp_path) -> None:
    res = oa.run(state_dir=tmp_path)
    assert res["schema"] == "octopus.owner-absence.v1"
    assert (tmp_path / "conservation-mode.json").exists()
    assert (tmp_path / "OWNER-QUEUE.md").exists()


# ── منفی‌های §۶ ─────────────────────────────────────────────────────────────

def test_owner_absence_has_no_merge_or_send_paths() -> None:
    src = (AGENTS / "owner_absence.py").read_text(encoding="utf-8")
    for banned in ("gh pr merge", "git push", "sendMessage", "smtp",
                   "owner_notify", "subprocess"):
        assert banned not in src, banned


def test_worker_denies_when_absence_subsystem_breaks(monkeypatch, tmp_path) -> None:
    # خرابیِ خودِ زیرسیستم غیبت هم باید deny بدهد (fail-closed) — نه عبور
    monkeypatch.setattr(oa, "conservation_active",
                        lambda state_dir=None: "conservation-subsystem-error")
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    try:
        res = ow.send_one("e-err", {"lead_id": "lead:x"}, gate=None)
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
    assert res["status"] == "conservation-denied"
    assert res["gate_reason"] == "conservation-subsystem-error"
