#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_spine_wired.py — فاز ۲ دستورالعمل ۲۰۲۶-۰۸-۱۶: تأییدِ wired بودن Event Spine.

واقعیتِ اندازه‌گیری‌شده (AGENT-INVENTORY-2026-08-16 §2): spine در تولید از قبل زنده است —
پرچم `OCTOPUS_WIRE_SPINE=1` در env هر ۵ پروسه و spine.db با ۴۷۷۰+ رویداد. این تست همان
قرارداد را hermetic اثبات می‌کند تا regression (پرچمِ خاموشِ تصادفی، شکستنِ adapter) قرمز شود:

  ۱. flag-on → emit از سطحِ تولیدِ واحد (spine_adapters.emit_event) publish می‌کند
     و event ثبت‌شده envelope کامل با correlation_id/trace_id دارد.
  ۲. flag-off → emit = صفر I/O (هیچ فایلی ساخته نمی‌شود) — همان قراردادِ no-op.
  ۳. رویدادِ بی‌corr (بی‌trace_id) رد می‌شود (ناوردیِ R8).
  ۴. تکرارِ همان رویداد (idempotency_key) duplicate می‌شود، نه دو ردیف.
  ۵. production-wiring: کدِ wiring.py نمادِ spine را می‌شناسد (LEG-07 زنده مانده).
"""
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "spine"),
           str(_HERE.parent / "outcomes"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("spine-wired")

import event_spine as es        # noqa: E402
import spine_adapters as sa     # noqa: E402


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


class _Flag:
    def __init__(self, value):
        self._v = value

    def __enter__(self):
        self._prev = os.environ.get(es.FLAG)
        os.environ[es.FLAG] = self._v
        return self

    def __exit__(self, *a):
        if self._prev is None:
            os.environ.pop(es.FLAG, None)
        else:
            os.environ[es.FLAG] = self._prev


def test_flag_on_emits_event_with_trace_id():
    with _tmp() as td, _Flag("1"):
        db = Path(td) / "spine" / "spine.db"
        res = sa.emit_event(event_type="outcome-recorded", domain="system",
                            correlation_id="oct-20260816-phase2-verify",
                            subject="phase2-wiring-check",
                            producer="worker-agent:phase2", trust="DETERMINISTIC",
                            payload={"phase": 2, "wired": True},
                            idempotency_key="phase2|spine-wired|verify",
                            spine=es.EventSpine(path=db))
        assert res["published"] is True, res
        spine = es.EventSpine(path=db)
        try:
            rows = spine.events(correlation_id="oct-20260816-phase2-verify")
            assert len(rows) == 1
            row = rows[0]
            # envelope کامل + trace (R8)
            assert row["correlation_id"] == "oct-20260816-phase2-verify"
            assert row["producer"] == "worker-agent:phase2"
            assert row["trust"] == "DETERMINISTIC"
            assert sa.validate_row(row)[0] is True, sa.validate_row(row)
        finally:
            spine.close()


def test_flag_off_is_zero_io():
    """adapter با spine=None (مسیرِ تولید): flag خاموش → return پیش از هر I/O.
    db نباید زیرِ STATE_DIR ایزولهٔ harness ساخته شود."""
    import opslib
    with _Flag("0"):
        db = Path(opslib.STATE_DIR) / "spine" / "spine.db"
        existed = db.exists()
        res = sa.emit_event(event_type="outcome-recorded", domain="system",
                            correlation_id="nope")
        assert res == {"published": False, "reason": "flag-off"}, res
        assert db.exists() == existed, "flag-off must not create spine.db"


def test_untraced_event_rejected():
    with _tmp() as td, _Flag("1"):
        spine = es.EventSpine(path=Path(td) / "spine.db")
        try:
            import pytest
            with pytest.raises(ValueError):
                spine.publish({"event_type": "outcome-recorded", "domain": "system"})
        finally:
            spine.close()


def test_idempotent_replay_is_duplicate():
    with _tmp() as td, _Flag("1"):
        spine = es.EventSpine(path=Path(td) / "spine.db")
        try:
            kw = dict(event_type="outcome-recorded", domain="system",
                      correlation_id="idem-1", idempotency_key="idem|1")
            r1 = sa.emit_event(spine=spine, **kw)
            r2 = sa.emit_event(spine=spine, **kw)
            assert r1["published"] is True and r2["published"] is False, (r1, r2)
            assert r2["reason"] == "duplicate"
            assert len(spine.events(correlation_id="idem-1")) == 1
        finally:
            spine.close()


def test_production_wiring_still_references_spine():
    """LEG-07 زنده مانده: wiring.py هنوز spine را پشتِ فلگ init می‌کند (regression guard)."""
    src = (_HERE.parent / "wiring.py").read_text("utf-8")
    assert "OCTOPUS_WIRE_SPINE" in src
    assert "event_spine" in src


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
