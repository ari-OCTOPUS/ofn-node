#!/usr/bin/env python3
"""test_wiring_cleanup.py — WP4: پاکسازیِ F2 (import مردهٔ phantom) + سیم‌کشیِ F3.

اثبات می‌کند:
  F2 · ziman_beat دیگر ماژولِ ناموجودِ ziman_biology را import نمی‌کند و در هیچ beat
       alertِ «ziman biology» تولید نمی‌کند (نویزِ لاگ حذف شد). خروجی بایت‌به‌بایت حفظ:
       کلیدِ "biology" هنوز هست و None است (مثلِ قبل که import همیشه شکست می‌خورد).
  F3 · scheduler_seed_beat با flag خاموش عیناً no-op است (None، producer صدا نمی‌شود =
       بایت‌به‌بایت) و با flag روشن producer (scheduler_seed_doctor_rfc → pacemaker.schedule)
       را صدا می‌زند. kill-switch (STOP/halt) مقدم است.

صفر نوشتن روی مسیرهای زنده: STOP/HALT و state_path به tmp مونکی‌پچ می‌شوند.
اجرا: python -X utf8 test_wiring_cleanup.py
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent / "budget", _HERE.parent / "legs", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import opslib   # noqa: E402
import wiring   # noqa: E402  ← اثباتِ ضمنی: wiring بدونِ خطا import می‌شود


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="wire-clean-"))


def _isolate_halt(d: pathlib.Path) -> None:
    """همهٔ پرچم‌های STOP/HALT به tmp — kill-switch هیچ‌وقت به‌خاطرِ فایلِ زنده نمی‌افتد."""
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
    opslib.STOP_ORGANISM = d / "STOP-ORGANISM"
    opslib.STOP_METABOLIC = d / "STOP-METABOLIC"
    opslib.STOP_DEBATE = d / "STOP-DEBATE"


class _CaptureAlert:
    """opslib.alert را می‌گیرد تا بتوانیم نبودِ alertِ biology را assert کنیم."""
    def __init__(self):
        self.calls: list[str] = []

    def __call__(self, lines):
        for ln in (lines if isinstance(lines, (list, tuple)) else [lines]):
            self.calls.append(str(ln))


class _StubZimanLeg:
    """کمینه‌ترین legِ لازم برای ziman_beat (بدونِ budgets.yaml / import واقعی)."""
    def status_snapshot(self) -> dict:
        return {"leg_id": "ziman-gallery", "organ": "ZIMAN", "money_link": "incubating",
                "capacity_ceiling_per_week": 3, "inventory_hint": "ok", "drafts_count": 0}

    def telegram_digest(self) -> str:
        return "digest-stub"

    # accept_biology_status عمداً نیست — اثبات می‌کند بلوکِ حذف‌شده دیگر آن را صدا نمی‌زند.


class _StubRFC:
    def __init__(self, status: str):
        self.status = status


class _StubDoctor:
    def __init__(self):
        self._rfcs = {"rfc-1": _StubRFC("submitted"),
                      "rfc-2": _StubRFC("closed")}   # فقط submitted باید schedule شود


class _StubPacemaker:
    def __init__(self):
        self.scheduled: list[dict] = []

    def schedule(self, **kw) -> int:
        self.scheduled.append(kw)
        return len(self.scheduled)


def _set_flag(name: str, val: str | None) -> str | None:
    prev = os.environ.get(name)
    if val is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = val
    return prev


# ─── F2 ─────────────────────────────────────────────────────────────────────

def test_wiring_imports_without_phantom() -> None:
    """موردِ ۱: importِ تمیز + متنِ منبع دیگر ziman_biology را ندارد."""
    src = (_HERE.parent / "wiring.py").read_text("utf-8", errors="replace")
    # فقط نحوِ import/call را ممنوع می‌کنیم؛ نامِ ماژول در comment توضیحی مجاز است.
    assert "from ziman_biology import" not in src, "importِ phantom هنوز زنده است"
    assert "biology_beat(" not in src, "callِ مردهٔ biology_beat هنوز زنده است"
    assert "import ziman_biology" not in src, "importِ phantom هنوز زنده است"


def test_ziman_beat_no_biology_alert_and_shape() -> None:
    """موردِ ۲ (F2): ziman_beat هیچ alertِ biology نمی‌زند؛ خروجی biology=None حفظ شد."""
    d = _tmp()
    _isolate_halt(d)
    cap = _CaptureAlert()
    _prev_alert = opslib.alert
    _prev_state = dict(wiring._ZIMAN_STATE)
    _prev_flag = _set_flag("OCTOPUS_WIRE_ZIMAN", "1")
    _prev_every = _set_flag("CHRONO_ZIMAN_EVERY_N_BEATS", "1")   # هر beat اجرا شود
    try:
        opslib.alert = cap
        wiring._ZIMAN_STATE["state_path"] = d / "ORGANISM-STATE.ziman"
        out = wiring.ziman_beat(leg=_StubZimanLeg(), beat=1, doctor=object())
        assert out is not None, "beat باید نتیجه بدهد (flag روشن، leg موجود)"
        assert "biology" in out, "کلیدِ biology باید حفظ شود (شکلِ خروجی بایت‌به‌بایت)"
        assert out["biology"] is None, "biology باید None باشد (مثلِ رفتارِ قبلی)"
        assert out["organ"] == "ZIMAN"
        # هیچ alertِ مربوط به biology/ziman_biology نباید ساطع شده باشد:
        bio_alerts = [c for c in cap.calls if "biology" in c.lower()]
        assert not bio_alerts, f"alertِ biology نباید باشد؛ دیده شد: {bio_alerts}"
        # فایلِ state هم باید به tmp نوشته شده باشد (اثباتِ عبور از مسیرِ کامل)
        assert (d / "ORGANISM-STATE.ziman").exists()
    finally:
        opslib.alert = _prev_alert
        wiring._ZIMAN_STATE.clear()
        wiring._ZIMAN_STATE.update(_prev_state)
        _set_flag("OCTOPUS_WIRE_ZIMAN", _prev_flag)
        _set_flag("CHRONO_ZIMAN_EVERY_N_BEATS", _prev_every)


# ─── F3 ─────────────────────────────────────────────────────────────────────

def test_scheduler_seed_beat_noop_when_flag_off() -> None:
    """موردِ ۳ (F3): flag خاموش → None و producer صدا نمی‌شود (بایت‌به‌بایت)."""
    d = _tmp()
    _isolate_halt(d)
    _prev_flag = _set_flag("OCTOPUS_WIRE_SCHEDULER", None)   # صریحاً خاموش (پیش‌فرض)
    try:
        doc, pm = _StubDoctor(), _StubPacemaker()
        out = wiring.scheduler_seed_beat(doctor=doc, pacemaker=pm, beat=5)
        assert out is None, "flag خاموش باید None بدهد"
        assert pm.scheduled == [], "flag خاموش نباید هیچ schedule بزند (no regression)"
    finally:
        _set_flag("OCTOPUS_WIRE_SCHEDULER", _prev_flag)


def test_scheduler_seed_beat_calls_producer_when_on() -> None:
    """موردِ ۴ (F3): flag روشن → producer فقط RFCهای submitted را schedule می‌کند."""
    d = _tmp()
    _isolate_halt(d)
    _prev_flag = _set_flag("OCTOPUS_WIRE_SCHEDULER", "1")
    try:
        doc, pm = _StubDoctor(), _StubPacemaker()
        out = wiring.scheduler_seed_beat(doctor=doc, pacemaker=pm, beat=5)
        assert out is not None and out.get("seeded") is True, out
        assert out["beat"] == 5 and out["propose_only"] is True
        # فقط rfc-1 (submitted) باید schedule شده باشد، نه rfc-2 (closed):
        assert len(pm.scheduled) == 1, pm.scheduled
        assert pm.scheduled[0]["task_ref"] == "rfc-1"
        assert pm.scheduled[0]["kind"] == "rfc-followup"
    finally:
        _set_flag("OCTOPUS_WIRE_SCHEDULER", _prev_flag)


def test_scheduler_seed_beat_kill_switch_first() -> None:
    """موردِ ۵ (F3): STOP-ORGANISM مقدم است — حتی با flag روشن، None و صفر schedule."""
    d = _tmp()
    _isolate_halt(d)
    (d / "STOP-ORGANISM").write_text("x", "utf-8")
    _prev_flag = _set_flag("OCTOPUS_WIRE_SCHEDULER", "1")
    try:
        doc, pm = _StubDoctor(), _StubPacemaker()
        out = wiring.scheduler_seed_beat(doctor=doc, pacemaker=pm, beat=5)
        assert out is None, "kill-switch باید None بدهد"
        assert pm.scheduled == [], "kill-switch نباید هیچ schedule بزند"
    finally:
        _set_flag("OCTOPUS_WIRE_SCHEDULER", _prev_flag)


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items())
              if k.startswith("test_") and callable(v)]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_wiring_cleanup: {len(_tests)}/{len(_tests)} سبز")
