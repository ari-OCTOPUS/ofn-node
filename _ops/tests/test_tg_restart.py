#!/usr/bin/env python3
"""test_tg_restart.py — توقفِ restart-aware ِ tg-center (WP3، owner decision #25).

مرزِ سخت دست‌نخورده می‌ماند اما یک ری‌استارتِ روتینِ ارگانیسم دیگر tg-center را نمی‌کشد.
اثبات می‌کند center.Center.stopped():
  * هیچ پرچم → not stopped.
  * HALT-ALL (via master_halted) → stopped (مرزِ سخت، هرگز ضعیف نمی‌شود).
  * STOP(architect) (via master_halted) → stopped (مرزِ سخت).
  * STOP-ORGANISM به‌تنهایی → stopped (ایستِ کاملِ سازگارِ عقب).
  * STOP-ORGANISM + RESTART-REQUESTED → NOT stopped (از ری‌استارت جان به‌در می‌برد).
  * STOP-TG-CENTER → stopped (scoped ِ خودش).

صفر نوشتن روی مسیرهای زنده: همهٔ path constantها به یک tmp dir مونکی‌پچ می‌شوند.
اجرا: python -X utf8 test_tg_restart.py
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent / "budget", _HERE.parent / "telegram_center", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import opslib  # noqa: E402
import center   # noqa: E402


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="tg-restart-test-"))


def _isolate(d: pathlib.Path):
    """همهٔ پرچم‌های STOP/HALT/RESTART را به tmp ببر — هیچ فایلِ زنده لمس نمی‌شود.
    برمی‌گرداند instance ِ Center که __init__ را دور می‌زند (stopped() از self استفاده نمی‌کند)."""
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
    opslib.STOP_ORGANISM = d / "STOP-ORGANISM"
    center.STOP_TG_CENTER = d / "STOP-TG-CENTER"
    center.RESTART_REQUESTED = d / "RESTART-REQUESTED"
    return center.Center.__new__(center.Center)


def test_no_flags_not_stopped() -> None:
    d = _tmp()
    inst = _isolate(d)
    assert inst.stopped() is False


def test_halt_all_stops() -> None:
    """مرزِ سختِ سراسری (پنیک) — همیشه می‌ایستاند، هرگز ضعیف نمی‌شود."""
    d = _tmp()
    inst = _isolate(d)
    opslib.HALT_ALL.write_text("panic", "utf-8")
    assert inst.stopped() is True


def test_stop_architect_stops() -> None:
    """STOP(architect) via master_halted — مرزِ سخت."""
    d = _tmp()
    inst = _isolate(d)
    opslib.STOP_ARCHITECT.write_text("x", "utf-8")
    assert inst.stopped() is True


def test_stop_organism_alone_stops() -> None:
    """STOP-ORGANISM بدونِ RESTART = ایستِ کامل → می‌ایستاند (سازگارِ عقب)."""
    d = _tmp()
    inst = _isolate(d)
    opslib.STOP_ORGANISM.write_text("x", "utf-8")
    assert inst.stopped() is True


def test_stop_organism_with_restart_survives() -> None:
    """STOP-ORGANISM + RESTART-REQUESTED = ری‌استارتِ روتین → NOT stopped (رفعِ WP3)."""
    d = _tmp()
    inst = _isolate(d)
    opslib.STOP_ORGANISM.write_text("x", "utf-8")
    center.RESTART_REQUESTED.write_text("dashboard", "utf-8")
    assert inst.stopped() is False               # ← از ری‌استارت جان به‌در برد


def test_hard_boundary_beats_restart_marker() -> None:
    """RESTART-REQUESTED هرگز مرزِ سخت را ضعیف نمی‌کند: HALT-ALL + RESTART = هنوز stopped."""
    d = _tmp()
    inst = _isolate(d)
    center.RESTART_REQUESTED.write_text("dashboard", "utf-8")
    opslib.HALT_ALL.write_text("panic", "utf-8")
    assert inst.stopped() is True
    opslib.HALT_ALL.unlink()
    opslib.STOP_ARCHITECT.write_text("x", "utf-8")
    assert inst.stopped() is True                # STOP(architect) هم مصون است


def test_stale_restart_marker_does_not_mask_full_stop() -> None:
    """سخت‌سازی (verifier): markerِ کهنهٔ RESTART-REQUESTED نباید STOP-ORGANISMِ «ایستِ کامل»
    را نامحدود ماسک کند. marker با mtimeِ قدیمی (> RESTART_FRESH_S) = ری‌استارتِ نامعتبر → می‌ایستاند."""
    import os
    import time as _t
    d = _tmp()
    inst = _isolate(d)
    opslib.STOP_ORGANISM.write_text("x", "utf-8")
    center.RESTART_REQUESTED.write_text("stale", "utf-8")
    old = _t.time() - (center.RESTART_FRESH_S + 60)   # قدیمی‌تر از پنجرهٔ تازگی
    os.utime(center.RESTART_REQUESTED, (old, old))
    assert inst.stopped() is True                     # ← markerِ کهنه دیگر ماسک نمی‌کند


def test_stop_tg_center_stops() -> None:
    """scoped ِ خودِ کانکتور — همیشه می‌ایستاند."""
    d = _tmp()
    inst = _isolate(d)
    center.STOP_TG_CENTER.write_text("x", "utf-8")
    assert inst.stopped() is True


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_tg_restart: {len(_tests)}/{len(_tests)} سبز")
