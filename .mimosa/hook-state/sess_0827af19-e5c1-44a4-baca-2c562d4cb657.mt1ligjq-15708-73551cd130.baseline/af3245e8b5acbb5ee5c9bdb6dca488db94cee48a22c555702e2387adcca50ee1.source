#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for cortex/wlos_bridge.py — flag-off {}, whitelist-only output,
PII scrubbing, clamping, never-raise."""
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_OPS, "cortex"))
import wlos_bridge as wb  # noqa: E402


def _with_flag(value):
    class _Ctx:
        def __enter__(self):
            self.old = os.environ.get(wb._FLAG)
            if value is None:
                os.environ.pop(wb._FLAG, None)
            else:
                os.environ[wb._FLAG] = value
            return self

        def __exit__(self, *a):
            if self.old is None:
                os.environ.pop(wb._FLAG, None)
            else:
                os.environ[wb._FLAG] = self.old
    return _Ctx()


def _write_signal(td, payload):
    p = Path(td) / "wlos" / "owner-summary.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False), "utf-8")
    return p


def test_flag_off_empty():
    with _with_flag(None), tempfile.TemporaryDirectory() as td:
        _write_signal(td, {"week": "2026-W29", "adherence_pct": 80})
        assert wb.read_owner_signal(state_dir=td) == {}


def test_missing_or_invalid_file_empty():
    with _with_flag("1"), tempfile.TemporaryDirectory() as td:
        assert wb.read_owner_signal(state_dir=td) == {}
        p = Path(td) / "wlos" / "owner-summary.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{not json", "utf-8")
        assert wb.read_owner_signal(state_dir=td) == {}
        p.write_text("[1,2]", "utf-8")
        assert wb.read_owner_signal(state_dir=td) == {}


def test_whitelist_only_and_clamps():
    with _with_flag("1  "), tempfile.TemporaryDirectory() as td:  # strip-safe هم
        _write_signal(td, {
            "week": "2026-W29-EXTRA-LONG", "weight_trend": "DOWN",
            "adherence_pct": 250, "checkins_done": -3, "energy_avg": 7.25,
            "flags": ["Plateau!", "night_snacking", "", "x" * 99, "ok", "extra6"],
            "note": "good week",
            "weight_kg": 92.5, "user_id": 12345, "chat_id": 999,  # باید حذف شوند
        })
        sig = wb.read_owner_signal(state_dir=td)
        assert set(sig) <= {"week", "weight_trend", "adherence_pct",
                            "checkins_done", "energy_avg", "flags", "note"}
        assert "weight_kg" not in sig and "user_id" not in sig
        assert sig["week"] == "2026-W29-EX"[:10] and sig["weight_trend"] == "down"
        assert sig["adherence_pct"] == 100 and sig["checkins_done"] == 0
        assert sig["energy_avg"] == 7.2 or sig["energy_avg"] == 7.3
        assert len(sig["flags"]) <= 5 and "plateau" in sig["flags"]


def test_note_scrubbed_of_pii():
    with _with_flag("1"), tempfile.TemporaryDirectory() as td:
        _write_signal(td, {"note": "call me a@b.com or 0412345678 see https://x.io/z " + "n" * 300})
        note = wb.read_owner_signal(state_dir=td).get("note", "")
        assert "a@b.com" not in note and "0412345678" not in note
        assert "https://" not in note and len(note) <= 140


def test_never_raises():
    with _with_flag("1"):
        assert wb.read_owner_signal(state_dir="Z:\\no\\such\\dir\\ever") == {}


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ✓ {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} green")
