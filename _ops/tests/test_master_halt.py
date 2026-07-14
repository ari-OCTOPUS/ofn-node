#!/usr/bin/env python3
"""test_master_halt.py — مرزِ سختِ سراسریِ توقف (رفعِ G-no-master-halt، 2026-07-13).

اثبات می‌کند:
  * opslib.master_halted() = اوراکلِ واحد (HALT-ALL ← STOP معمار)، ترتیب‌دار.
  * opslib.halted() سازگارِ عقب می‌ماند (STOP معمار → دقیقاً "STOP(architect)"؛
    قرارداد test_go_live)، ولی HALT-ALL مقدم است.
  * telegram_center.Center.stopped() حالا مرزِ سراسری + STOP-ORGANISM را honor می‌کند
    (کانکتورِ بیرونی دیگر STOP را نادیده نمی‌گیرد).
  * events.emit نامِ ناشناخته را به task.failed (نه task.completed) می‌برد (fail-loud، رفعِ E2).

صفر نوشتن روی مسیرهای زنده: همهٔ path constantها به یک tmp dir مونکی‌پچ می‌شوند.
اجرا: python -X utf8 test_master_halt.py
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


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="halt-test-"))


def _isolate_opslib(d: pathlib.Path) -> None:
    """همهٔ STOP/HALT پرچم‌ها را به tmp ببر — هیچ فایلِ زنده لمس نمی‌شود."""
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
    opslib.STOP_ORGANISM = d / "STOP-ORGANISM"
    opslib.STOP_METABOLIC = d / "STOP-METABOLIC"
    opslib.STOP_DEBATE = d / "STOP-DEBATE"


def test_master_halted_ordering() -> None:
    d = _tmp()
    _isolate_opslib(d)
    assert opslib.master_halted() is None
    opslib.STOP_ARCHITECT.write_text("x", "utf-8")
    assert opslib.master_halted() == "STOP(architect)"
    opslib.HALT_ALL.write_text("panic", "utf-8")
    assert opslib.master_halted() == "HALT-ALL"      # پنیک مقدم
    opslib.HALT_ALL.unlink()
    assert opslib.master_halted() == "STOP(architect)"


def test_halted_backward_compat() -> None:
    d = _tmp()
    _isolate_opslib(d)
    assert opslib.halted() is None                    # هیچ پرچم = None
    opslib.STOP_ARCHITECT.write_text("x", "utf-8")
    assert opslib.halted() == "STOP(architect)"       # قراردادِ test_go_live دست‌نخورده
    opslib.HALT_ALL.write_text("panic", "utf-8")
    assert opslib.halted() == "HALT-ALL"              # مرزِ سراسری مقدم
    opslib.HALT_ALL.unlink()
    opslib.STOP_ARCHITECT.unlink()
    opslib.STOP_METABOLIC.write_text("x", "utf-8")
    assert opslib.halted() == "STOP-METABOLIC"        # scoped ِ متابولیسم بعد از سراسری


def test_raise_and_clear_halt_all() -> None:
    d = _tmp()
    _isolate_opslib(d)
    opslib.ALERTS_MD = d / "alerts.md"                # alert() به tmp
    assert opslib.master_halted() is None
    opslib.raise_halt_all("unit-test panic")
    assert opslib.HALT_ALL.exists()
    assert opslib.master_halted() == "HALT-ALL"
    assert opslib.clear_halt_all() is True
    assert not opslib.HALT_ALL.exists()
    assert opslib.clear_halt_all() is False           # دومین بار: چیزی نبود


def test_center_stopped_honors_global_boundary() -> None:
    """کانکتورِ تلگرام: هر یک از مرزِ سراسری / STOP-ORGANISM / STOP-TG-CENTER = ایست."""
    import center  # noqa: E402
    d = _tmp()
    _isolate_opslib(d)
    center.STOP_TG_CENTER = d / "STOP-TG-CENTER"
    inst = center.Center.__new__(center.Center)       # bypass __init__؛ stopped() از self استفاده نمی‌کند

    assert inst.stopped() is False                    # هیچ پرچم
    opslib.HALT_ALL.write_text("panic", "utf-8")      # 🔴 مرزِ سراسری
    assert inst.stopped() is True                     # ← رفعِ اصلیِ G-no-master-halt
    opslib.HALT_ALL.unlink()

    opslib.STOP_ARCHITECT.write_text("x", "utf-8")    # STOP معمار
    assert inst.stopped() is True
    opslib.STOP_ARCHITECT.unlink()

    opslib.STOP_ORGANISM.write_text("x", "utf-8")     # STOP-ORGANISM (طبقِ mandate)
    assert inst.stopped() is True
    opslib.STOP_ORGANISM.unlink()
    assert inst.stopped() is False

    center.STOP_TG_CENTER.write_text("x", "utf-8")    # scoped ِ خودش
    assert inst.stopped() is True


def test_events_unknown_name_is_fail_loud() -> None:
    """رفعِ E2: نامِ خارج از taxonomy → task.failed (قرمز)، نه task.completed (سبز)."""
    import events  # noqa: E402
    d = _tmp()
    events.LOG = d / "events.jsonl"                   # نوشتن به tmp
    ev = events.emit("bogus.random.name", "unit-test")
    assert ev["event_name"] == "task.failed", ev["event_name"]
    assert "drift" in ev["summary"] and "bogus.random.name" in ev["summary"]
    ev2 = events.emit("task.started", "unit-test")    # نامِ معتبر دست‌نخورده
    assert ev2["event_name"] == "task.started"
    ev3 = events.emit("incident.opened", "unit-test") # نامِ additive ِ #۱۳
    assert ev3["event_name"] == "incident.opened"


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_master_halt: {len(_tests)}/{len(_tests)} سبز")
