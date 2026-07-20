#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for legs/tradequote_bridge.py — flag-off no-op, strip-safe flag,
integer-cents mapping (R3), atomic export, fail-soft."""
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_OPS, "legs"))
import tradequote_bridge as tb  # noqa: E402

_REC = {
    "ts": "2026-07-20T15:00:00+10:00",
    "schema": "lead-quote.v1",
    "qt_number": "QT-20260720-001",
    "attribution_id": "LD-test-1",
    "intake": {"scope": "exterior repaint 120m2"},
    "breakdown": {
        "line_items": [
            {"description": "Labor: exterior weatherboard (prep: standard, 2 coat(s))",
             "qty": 120, "unit": "m2", "rate_aud": [8.0, 12.5],
             "subtotal_aud": [1000.0, 1500.0]},
            {"description": "Materials: paint + supplies (premium)",
             "qty": 2, "unit": "lot", "rate_aud": [100.25, 150.125],
             "subtotal_aud": [200.5, 300.25]}],
        "subtotal_excl_gst": [1200.5, 1800.25],
        "gst": [120.05, 180.03],
        "total_incl_gst": [1320.55, 1980.28],
        "max_deposit_nsw": [132.06, 198.03],
    },
}


def _with_flag(value):
    class _Ctx:
        def __enter__(self):
            self.old = os.environ.get(tb._FLAG)
            if value is None:
                os.environ.pop(tb._FLAG, None)
            else:
                os.environ[tb._FLAG] = value
            return self

        def __exit__(self, *a):
            if self.old is None:
                os.environ.pop(tb._FLAG, None)
            else:
                os.environ[tb._FLAG] = self.old
    return _Ctx()


def test_flag_off_is_noop():
    with _with_flag(None), tempfile.TemporaryDirectory() as td:
        assert tb.maybe_export(_REC, state_dir=td) is None
        assert not (Path(td) / "legs" / "tradequote-outbox").exists()


def test_flag_strip_safe_trailing_spaces():
    # درسِ دلتا-اسکن: «1» با فاصلهٔ انتهایی نباید فلگ را بکُشد
    with _with_flag("1   "), tempfile.TemporaryDirectory() as td:
        p = tb.maybe_export(_REC, state_dir=td)
        assert p is not None and p.exists()


def test_mapping_integer_cents_and_ranges():
    pkg = tb.to_tradequote(_REC)
    assert pkg["schema"] == tb.SCHEMA and pkg["draft_only"] is True
    t = pkg["totals"]["total_incl_gst"]
    assert t == {"lo_cents": 132055, "hi_cents": 198028}
    for li in pkg["line_items"]:
        a = li["amount"]
        assert isinstance(a["lo_cents"], int) and isinstance(a["hi_cents"], int)
    assert pkg["line_items"][1]["qty_milli"] == 2000


def test_export_writes_json_and_txt():
    with _with_flag("1"), tempfile.TemporaryDirectory() as td:
        p = tb.maybe_export(_REC, state_dir=td)
        assert p and p.name == "QT-20260720-001.tq.json"
        data = json.loads(p.read_text("utf-8"))
        assert data["qt_number"] == "QT-20260720-001"
        txt = (p.parent / "QT-20260720-001.txt").read_text("utf-8")
        assert "TOTAL (incl GST)" in txt and "1,320.55" in txt
        assert not list(p.parent.glob("*.tmp"))  # atomic: هیچ tmp باقی نمانده


def test_fail_soft_bad_record():
    with _with_flag("1"), tempfile.TemporaryDirectory() as td:
        assert tb.maybe_export(None, state_dir=td) is None
        assert tb.maybe_export({"no_qt": True}, state_dir=td) is None
        assert tb.maybe_export({"qt_number": "QT-X", "breakdown": "garbage"},
                               state_dir=td) is not None  # نگاشتِ مقاوم


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ✓ {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} green")
