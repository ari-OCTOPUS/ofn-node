#!/usr/bin/env python3
"""test_improve_refractory.py — گاردِ cooldown/refractory ِ auto-apply واقعاً اجراشدنی
(رفعِ ORPH-IMPROVE-AUTOSTATE، 2026-07-14).

اثباتِ باگ+فیکس:
  * پیش از این improve.refractory_open() به improve-auto-state.json نگاه می‌کرد ولی
    last_auto_ts هرگز نوشته نمی‌شد → همیشه «first» → cooldown هرگز اعمال نمی‌شد.
  * حالا وقتی maybe_auto_apply واقعاً یک knob اعمال می‌کند، last_auto_ts اتمیک ثبت می‌شود.
  * درنتیجه اعمالِ بعدیِ درونِ پنجرهٔ REFRACTORY_H مسدود، و پس از پنجره آزاد می‌شود.
  * fail-soft: خطای نوشتن حلقه را نمی‌کشد؛ کلیدهای موجودِ state حفظ می‌شوند.

صفر نوشتن روی مسیرهای زنده: همهٔ pathها به tmp مونکی‌پچ می‌شوند.
اجرا: python -X utf8 test_improve_refractory.py
"""
from __future__ import annotations

import datetime as _dt
import pathlib
import sys
import tempfile
import types

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent / "budget", _HERE.parent / "cortex", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import opslib  # noqa: E402
import improve  # noqa: E402


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="improve-refr-"))


def _isolate(d: pathlib.Path) -> None:
    """همهٔ مسیرهای نوشتنیِ improve/opslib را به tmp ببر — هیچ فایلِ زنده لمس نمی‌شود."""
    improve.AUTO_STATE_PATH = d / "improve-auto-state.json"
    improve.ACT_AUTO = d / "ACTIVATION-SELF-IMPROVE-AUTO.flag"
    opslib.ALERTS_MD = d / "alerts.md"


def _fake_auto_approve(applied_titles: list[str]) -> None:
    """ماژولِ auto_approve را در sys.modules جایگزین کن تا run() قابل‌کنترل باشد."""
    m = types.ModuleType("auto_approve")
    m.run = lambda cand: {"applied": [{"title": t} for t in applied_titles]}  # type: ignore[attr-defined]
    sys.modules["auto_approve"] = m


def test_persist_writes_last_auto_ts() -> None:
    """اصلِ فیکس: _persist_auto_ts یک POSIX float به state می‌نویسد (اتمیک)."""
    d = _tmp()
    _isolate(d)
    assert not improve.AUTO_STATE_PATH.exists()
    ts = _dt.datetime.now().timestamp()
    improve._persist_auto_ts(ts)
    assert improve.AUTO_STATE_PATH.exists()
    st = improve._read(improve.AUTO_STATE_PATH) or {}
    assert abs(float(st["last_auto_ts"]) - ts) < 1.0, st
    assert "last_auto_iso" in st


def test_persist_preserves_existing_keys() -> None:
    """کلیدهای موجودِ state نباید پاک شوند (merge، نه overwrite)."""
    d = _tmp()
    _isolate(d)
    with opslib.LockedJson(improve.AUTO_STATE_PATH) as lj:
        lj.write({"keep_me": 42, "last_auto_ts": 0.0})
    improve._persist_auto_ts(_dt.datetime.now().timestamp())
    st = improve._read(improve.AUTO_STATE_PATH) or {}
    assert st.get("keep_me") == 42, st
    assert float(st["last_auto_ts"]) > 0.0


def test_refractory_blocks_after_apply_then_opens() -> None:
    """چرخهٔ کامل: قبل از هر apply باز → بعد از apply بسته → پس از پنجره باز."""
    d = _tmp()
    _isolate(d)
    # ۱) هیچ state = «first» = باز
    ok, why = improve.refractory_open()
    assert ok and why == "first", (ok, why)

    # ۲) یک auto-apply واقعی را شبیه‌سازی کن (مسیرِ کاملِ maybe_auto_apply)
    improve.ACT_AUTO.write_text("owner", "utf-8")                  # پرچمِ فعال‌سازی
    improve.observability_ok = lambda: (True, "fresh")            # مشاهدهٔ زنده
    _fake_auto_approve(["CORTEX_THINK_EVERY_N tune"])            # run() یک knob اعمال می‌کند
    proposals = [{"id": "p1", "title": "CORTEX_THINK_EVERY_N tune",
                  "auto_applicable": True, "status": "proposed"}]
    applied = improve.maybe_auto_apply(proposals)
    assert applied == ["p1"], applied
    assert proposals[0]["status"] == "auto-applied"

    # ۳) last_auto_ts حالا نوشته شده → refractory بسته است (درونِ پنجره)
    st = improve._read(improve.AUTO_STATE_PATH) or {}
    assert float(st["last_auto_ts"]) > 0.0, "last_auto_ts نوشته نشد — گارد بی‌اثر می‌ماند"
    ok, why = improve.refractory_open()
    assert not ok and why.startswith("refractory"), (ok, why)

    # ۴) یک apply ِ دوم درونِ پنجره باید مسدود شود (gate عملاً کار می‌کند)
    proposals2 = [{"id": "p2", "title": "CORTEX_THINK_EVERY_N tune",
                   "auto_applicable": True, "status": "proposed"}]
    applied2 = improve.maybe_auto_apply(proposals2)
    assert applied2 == [], applied2
    assert proposals2[0]["status"] == "proposed"                  # هیچ اعمالی رخ نداد

    # ۵) عقب‌بردنِ مُهر فراتر از پنجره → دوباره باز
    old = _dt.datetime.now().timestamp() - (improve.REFRACTORY_H + 1) * 3600.0
    with opslib.LockedJson(improve.AUTO_STATE_PATH) as lj:
        s = lj.read() or {}
        s["last_auto_ts"] = old
        lj.write(s)
    ok, why = improve.refractory_open()
    assert ok and why == "open", (ok, why)


def test_no_apply_does_not_stamp() -> None:
    """اگر auto_approve چیزی اعمال نکند، مُهر نباید ثبت شود (فقط apply واقعی)."""
    d = _tmp()
    _isolate(d)
    improve.ACT_AUTO.write_text("owner", "utf-8")
    improve.observability_ok = lambda: (True, "fresh")
    _fake_auto_approve([])                                        # هیچ applyی
    proposals = [{"id": "p1", "title": "CORTEX_THINK_EVERY_N tune",
                  "auto_applicable": True, "status": "proposed"}]
    applied = improve.maybe_auto_apply(proposals)
    assert applied == [], applied
    assert not improve.AUTO_STATE_PATH.exists(), "بدونِ apply نباید state ساخته شود"


def test_flag_off_is_byte_identical_noop() -> None:
    """پرچمِ فعال‌سازی خاموش = رفتارِ قبلی: هیچ apply، هیچ نوشتنِ state."""
    d = _tmp()
    _isolate(d)  # ACT_AUTO ساخته نمی‌شود → وجود ندارد
    assert not improve.ACT_AUTO.exists()
    proposals = [{"id": "p1", "title": "CORTEX_THINK_EVERY_N tune",
                  "auto_applicable": True, "status": "proposed"}]
    applied = improve.maybe_auto_apply(proposals)
    assert applied == [], applied
    assert not improve.AUTO_STATE_PATH.exists()


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_improve_refractory: {len(_tests)}/{len(_tests)} سبز")
