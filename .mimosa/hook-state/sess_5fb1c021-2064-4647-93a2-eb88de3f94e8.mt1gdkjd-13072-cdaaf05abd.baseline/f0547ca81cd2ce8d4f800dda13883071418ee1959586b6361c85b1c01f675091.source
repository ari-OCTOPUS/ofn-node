#!/usr/bin/env python3
"""test_accounting_leg_beat_signal.py — فیکسِ خودآگاهیِ کاذبِ پای Accounting (۲۰۲۶-۰۸-۰۷).

قبل از این فیکس: accounting_status() فقط mtimeِ xlsxِ محلی را می‌سنجید — یعنی حتی وقتی
pipelineِ واقعیِ PocketSmith/ledger_core (پشتِ OCTOPUS_WIRE_ACCT_BEAT) زنده بود و
سایدکارِ wiring.acct_beat (ORGANISM-STATE.accounting) را تازه می‌نوشت، اگر مالک چند
هفته xlsx دستی export نکرده بود، live=False/age_daysِ بزرگ گزارش می‌شد — دروغِ
خودآگاهی: مهم‌ترین پای بیزنس مرده گزارش می‌شد درحالی‌که موتورِ واقعی کنارش می‌چرخید.

این فایل اثبات می‌کند:
  * سیگنالِ acct-beatِ تازه → live=True با age_daysِ کم، حتی وقتی xlsx کهنه/غایب است.
  * fail-soft در هر دو جهت: نبود/کهنگیِ سایدکار هرگز رفتارِ قدیمیِ فقط-xlsx را
    نمی‌شکند (fallback صادق)؛ کهنگیِ هر دو سیگنال → live=False صادقانه (نه override کور).
  * قراردادِ خروجی {leg,live,signal,note}+age_days دست‌نخورده می‌ماند.
  * صفر crash روی سایدکارِ خراب/مسیرِ غیرِ فایل (fail-soft، هرگز exception).

صفر نوشتن روی مسیرِ زنده: هم ACCT_DIR هم ACCT_BEAT_SIDECAR به tmp مونکی‌پچ می‌شوند
(الگویِ «هر مسیرِ تحتِ آزمون را ایزوله کن» — سایدکارِ زندهٔ ارگانیسم هرگز خوانده نمی‌شود).
اجرا: python -X utf8 test_accounting_leg_beat_signal.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import time

_HERE = pathlib.Path(__file__).resolve().parent
_LEGS = _HERE.parent / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))

import accounting_leg   # noqa: E402

_CORE_KEYS = {"leg", "live", "signal", "note"}
_DAY_S = 86400.0


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="acctbeat-sig-test-"))


def _backdate(p: pathlib.Path, days: float) -> None:
    ts = time.time() - days * _DAY_S
    os.utime(p, (ts, ts))


def _assert_contract(d: dict) -> None:
    assert isinstance(d, dict), "dict لازم است"
    assert _CORE_KEYS <= set(d.keys()), f"کلیدهای هسته ناقص: {set(d.keys())}"
    assert "age_days" in d, "کلیدِ age_days لازم است"
    assert d["age_days"] is None or isinstance(d["age_days"], (int, float)), \
        f"age_days باید عدد یا None باشد: {d['age_days']!r}"
    assert d["leg"] == "accounting" and isinstance(d["live"], bool)
    assert isinstance(d["signal"], str) and d["signal"]
    assert isinstance(d["note"], str) and d["note"]


def _sidecar(days_old: float | None, root: pathlib.Path) -> pathlib.Path:
    """سایدکارِ acct_beatِ ساختگی — همان شکلِ wiring.acct_beat (فقط شمار، صفر PII).
    days_old=None → فایل اصلاً ساخته نمی‌شود (سیگنال غایب)."""
    p = root / "ORGANISM-STATE.accounting"
    if days_old is None:
        return p
    p.write_text(json.dumps({"synced": False, "memory_active": 1, "pending_review": 2,
                             "beat": 1, "updated_at": "x"}, ensure_ascii=False), "utf-8")
    if days_old > 0:
        _backdate(p, days_old)
    return p


# ── سیگنالِ نو: acct-beatِ تازه غالب می‌شود ──────────────────────────────────────

def t_fresh_beat_overrides_stale_xlsx() -> None:
    """xlsx کهنه (مثلِ ادعای گزارش‌شدهٔ age_days=612.8) + سایدکارِ acct_beat تازه →
    live=True و age_days کم (سیگنالِ pipelineِ واقعی برنده می‌شود)."""
    root = _tmp()
    adir = root / "acct"
    adir.mkdir(parents=True)
    old_wb = adir / "old.xlsx"
    old_wb.write_bytes(b"never-read")
    _backdate(old_wb, 612.8)
    accounting_leg.ACCT_DIR = adir
    accounting_leg.ACCT_BEAT_SIDECAR = _sidecar(0.05, root)   # ~۱٫۲ ساعت پیش
    r = accounting_leg.accounting_status()
    _assert_contract(r)
    assert r["live"] is True, r
    assert r["age_days"] is not None and r["age_days"] <= 0.2, r["age_days"]
    assert "acct-beat" in r["signal"] and "workbooks=1" in r["signal"], r["signal"]


def t_fresh_beat_live_with_no_xlsx_dir_at_all() -> None:
    """پوشهٔ Accounting اصلاً وجود ندارد ولی ضربان تازه است → live=True (نه no-data)."""
    root = _tmp()
    accounting_leg.ACCT_DIR = root / "no-such-acct-dir"
    accounting_leg.ACCT_BEAT_SIDECAR = _sidecar(0.1, root)
    r = accounting_leg.accounting_status()
    _assert_contract(r)
    assert r["live"] is True and r["signal"] == "acct-beat", r
    assert r["age_days"] is not None and r["age_days"] <= 0.2, r["age_days"]


def t_fresh_beat_live_with_acct_dir_present_but_empty() -> None:
    """پوشه هست ولی بدونِ workbook (empty) + ضربان تازه → live=True."""
    root = _tmp()
    adir = root / "acct"
    adir.mkdir(parents=True)
    accounting_leg.ACCT_DIR = adir
    accounting_leg.ACCT_BEAT_SIDECAR = _sidecar(0.1, root)
    r = accounting_leg.accounting_status()
    _assert_contract(r)
    assert r["live"] is True and "acct-beat" in r["signal"], r


# ── fail-soft: نبودِ سیگنالِ نو رفتارِ قدیمی را نمی‌شکند ─────────────────────────

def t_old_behavior_fresh_xlsx_no_beat_sidecar() -> None:
    """سایدکار اصلاً وجود ندارد (never wired/flag off) → دقیقاً رفتارِ قدیمیِ فقط-xlsx.
    signal باید بایت‌به‌بایت 'workbooks=N' بماند (بدونِ پسوند) — رگرسیون‌گارد."""
    root = _tmp()
    adir = root / "acct"
    adir.mkdir(parents=True)
    for nm in ("a.xlsx", "b.xlsx"):
        (adir / nm).write_bytes(b"never-read")
    accounting_leg.ACCT_DIR = adir
    accounting_leg.ACCT_BEAT_SIDECAR = _sidecar(None, root)   # هرگز نوشته نشده
    r = accounting_leg.accounting_status()
    _assert_contract(r)
    assert r["live"] is True and r["signal"] == "workbooks=2", r
    assert r["age_days"] is not None and r["age_days"] <= 0.1, r["age_days"]


def t_old_behavior_stale_xlsx_no_beat_sidecar_stays_dead() -> None:
    """سایدکار غایب + xlsx کهنه → همچنان live=False (فیکس نباید false-positive بسازد)."""
    root = _tmp()
    adir = root / "acct"
    adir.mkdir(parents=True)
    old_wb = adir / "old.xlsx"
    old_wb.write_bytes(b"never-read")
    _backdate(old_wb, 60)
    accounting_leg.ACCT_DIR = adir
    accounting_leg.ACCT_BEAT_SIDECAR = _sidecar(None, root)
    r = accounting_leg.accounting_status()
    _assert_contract(r)
    assert r["live"] is False, r
    assert 59.8 <= r["age_days"] <= 60.2, r["age_days"]
    assert r["signal"] == "workbooks=1", r["signal"]


def t_stale_beat_sidecar_does_not_grant_liveness() -> None:
    """سایدکار *هست* ولی خودش کهنه (>آستانه) + xlsx هم کهنه → live=False صادقانه
    (کهنگیِ هر دو سیگنال هرگز به True جعلی override نمی‌شود)."""
    root = _tmp()
    adir = root / "acct"
    adir.mkdir(parents=True)
    old_wb = adir / "old.xlsx"
    old_wb.write_bytes(b"never-read")
    _backdate(old_wb, 60)
    accounting_leg.ACCT_DIR = adir
    accounting_leg.ACCT_BEAT_SIDECAR = _sidecar(10.0, root)   # فراتر از ACCT_BEAT_MAX_AGE_DAYS
    r = accounting_leg.accounting_status()
    _assert_contract(r)
    assert r["live"] is False, r
    assert "acct-beat" not in r["signal"], r["signal"]


def t_beat_sidecar_missing_file_but_dir_exists_is_fail_soft() -> None:
    """سایدکار در مسیرِ نامعتبر (پوشه‌ای که هرگز فایل نشده) → age_days=None، بدونِ crash."""
    root = _tmp()
    adir = root / "acct"
    adir.mkdir(parents=True)
    (adir / "fresh.xlsx").write_bytes(b"never-read")
    accounting_leg.ACCT_DIR = adir
    accounting_leg.ACCT_BEAT_SIDECAR = root / "ghost" / "ORGANISM-STATE.accounting"  # نبود
    r = accounting_leg.accounting_status()
    _assert_contract(r)
    assert r["live"] is True and r["signal"] == "workbooks=1", r   # فقط xlsxِ تازه تصمیم گرفت


def t_beat_sidecar_path_is_a_directory_never_crashes() -> None:
    """سایدکار به یک پوشه اشاره می‌کند (نه فایل) — stat خطا می‌دهد ولی هرگز crash."""
    root = _tmp()
    adir = root / "acct"
    adir.mkdir(parents=True)
    old_wb = adir / "old.xlsx"
    old_wb.write_bytes(b"never-read")
    _backdate(old_wb, 60)
    weird = root / "weird-sidecar-dir"
    weird.mkdir(parents=True)
    accounting_leg.ACCT_DIR = adir
    accounting_leg.ACCT_BEAT_SIDECAR = weird   # مسیر پوشه است نه فایل، ولی stat می‌شود نه crash
    r = accounting_leg.accounting_status()     # نباید exception بیندازد
    _assert_contract(r)
    assert isinstance(r["live"], bool)


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    _failed = 0
    for _t in _tests:
        try:
            _t()
            print(f"  ✓ {_t.__name__}")
        except AssertionError as _e:
            _failed += 1
            print(f"  ✗ {_t.__name__}: {_e}")
    if _failed:
        print(f"❌ test_accounting_leg_beat_signal: {_failed}/{len(_tests)} قرمز")
        sys.exit(1)
    print(f"✅ test_accounting_leg_beat_signal: {len(_tests)}/{len(_tests)} سبز")
