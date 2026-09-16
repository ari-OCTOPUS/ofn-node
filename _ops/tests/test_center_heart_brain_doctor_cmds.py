"""test_center_heart_brain_doctor_cmds.py — /heart /brain /doctor روی باتِ زنده.

نقشهٔ ۱۲-BRAIN-HEART-CONTROL-PANEL-MAP-2026-08-05 (یافتهٔ G7): این سه فرمان
فقط در بات B (`approval_channel`) بودند؛ بات A (`center.py`، زنده) اصلاً
نمی‌شناختشان. این سه متد (`_heart_cmd`/`_brain_cmd`/`_doctor_cmd`) و ثبتشان
در `handlers`/`_CENTER_SLASH` را قفل می‌کند. صفر شبکه، صفر نوشتن خارج از
temp harness.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("center-hbd")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib   # noqa: E402
import center   # noqa: E402


def _mk_center():
    return center.Center(client=None, clock=None, render_mod=None)


def _write(rel: str, data) -> Path:
    p = opslib.STATE_DIR / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    return p


# ── ثبت ────────────────────────────────────────────────────────────────────
def t_all_three_are_in_center_slash():
    for cmd in ("/heart", "/brain", "/doctor"):
        assert cmd in center._CENTER_SLASH, f"{cmd} در _CENTER_SLASH نیست"


def t_all_three_have_handler_methods():
    c = _mk_center()
    for name in ("_heart_cmd", "_brain_cmd", "_doctor_cmd"):
        assert callable(getattr(c, name, None)), f"{name} وجود ندارد"


# ── /doctor (از opslib.STATE_DIR می‌خواند — این یکی واقعاً ایزوله می‌شود) ────
def t_doctor_fail_soft_on_missing_file():
    """اول از همه، پیش از آنکه تستِ دیگری rfcs.json بنویسد."""
    p = opslib.STATE_DIR / "doctor" / "rfcs.json"
    if p.exists():
        p.unlink()
    out = _mk_center()._doctor_cmd()
    assert "خطا" in out, out
    assert "🩺" in out


def t_doctor_counts_pending_rfcs():
    _write("doctor/rfcs.json", {"rfcs": [
        {"id": "r1", "status": "submitted", "title": "الف"},
        {"id": "r2", "status": "submitted", "title": "ب"},
        {"id": "r3", "status": "applied", "title": "ج"},
        {"id": "r4", "status": "stale-input", "title": "د"},
    ]})
    out = _mk_center()._doctor_cmd()
    assert "2 RFC معطل از 4" in out, out
    assert "r1" in out and "r2" in out
    assert "r3" not in out and "r4" not in out  # فقط pending


def t_doctor_warns_when_stress_maxed():
    _write("doctor/rfcs.json", {"rfcs": [
        {"id": f"r{i}", "status": "submitted", "title": f"t{i}"} for i in range(7)
    ]})
    out = _mk_center()._doctor_cmd()
    assert "استرسِ دکتر روی سقف" in out, out


def t_doctor_no_warning_under_threshold():
    _write("doctor/rfcs.json", {"rfcs": [
        {"id": "r1", "status": "submitted", "title": "الف"},
    ]})
    out = _mk_center()._doctor_cmd()
    assert "استرسِ دکتر روی سقف" not in out, out


# ── /brain، /heart ────────────────────────────────────────────────────────
# ⚠️ `miniapp_state._OPS = Path(__file__).resolve().parent.parent` — از
# `OPS_DIR` env تبعیت نمی‌کند، پیش از این تستْ همینطور بود (`_brain_daemon`/
# `_4D_ROOT` هم همین‌طورند). یعنی `_cortex_state()`/`_arbiter_vitals`/
# `_cardiac_vitals` همیشه از **درختِ زندهٔ واقعی** می‌خوانند، نه از harness
# ِ ایزوله‌شدهٔ این تست. اصلاحِ خودِ ماژول (ایزوله‌کردنِ `_OPS`) دیفِ بزرگ‌تری
# روی فایلِ ۱۳۰KBِ پرترافیک است — خارج از دامنهٔ این پَس. این تست فقط
# fail-soft/شکلِ خروجی را قفل می‌کند، نه محتوای دقیق (که همیشه زنده است).
def t_brain_never_raises_and_has_expected_shape():
    out = _mk_center()._brain_cmd()
    assert isinstance(out, str) and out
    assert "🧠" in out
    assert "cortex" in out or "در دسترس نیست" in out


def t_heart_never_raises_with_no_state():
    out = _mk_center()._heart_cmd()
    assert isinstance(out, str) and out
    assert "🫀" in out


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_center_heart_brain_doctor_cmds: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
