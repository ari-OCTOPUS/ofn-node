#!/usr/bin/env python3
"""test_backup_visibility.py — WP2 داشبورد-حقیقت: de-mask بک‌آپ (OBS-02) + رویت‌پذیریِ
اهرم‌های فعال‌سازی و توقفِ سراسری (DSH-02).

پوشش:
  * opslib.gitwrite_failed(): None بدونِ پرچم؛ دلیل با پرچمِ برافراشته (BOMِ ویندوز هم).
  * opslib.backup_health(): پرچمِ GITWRITE-FAILED همیشه غالب است — حتی اگر germline lag
    تازه (سبز) باشد، خروجی ناسالم می‌شود (رفعِ سبزِ کاذبِ OBS-02).
  * opslib.armed_activation_flags(): آینهٔ ACTIVATION-*.flag ِ برافراشته.
  * opslib.halt_reason(): سطحِ نمایشِ توقفِ سراسری — fallback به halted()، و pickupِ
    master_halted (HALT-ALL) وقتی موجود باشد.
  * dashboard.server هوکِ خودکفا: _gitwrite_failed / _halt_reason (مسیرها tmp).

$0 آفلاین: harness مسیرهای opslib را به مینی-vaultِ موقت تزریق می‌کند؛ تست هیچ‌چیز روی
مسیرهای زنده نمی‌نویسد. standalone: python -X utf8 test_backup_visibility.py
"""
import os
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness
ENV = harness.setup("backup-visibility")   # OPS_DIR/ARCHITECT/... → vaultِ موقت

import opslib


def _fresh_offbox() -> Path:
    """offboxِ موقت با مانیفستِ تازه → germline_lag_hours ≈ 0 (سبز اگر پرچمی نباشد)."""
    ob = Path(tempfile.mkdtemp(prefix="offbox-"))
    (ob / "last_backup_manifest.json").write_text("{}", "utf-8")
    return ob


def _write_flag(text: str) -> None:
    opslib.GITWRITE_FAILED.parent.mkdir(parents=True, exist_ok=True)
    opslib.GITWRITE_FAILED.write_text(text, "utf-8")


def _clear_flag() -> None:
    try:
        opslib.GITWRITE_FAILED.unlink()
    except OSError:
        pass


# ── gitwrite_failed ─────────────────────────────────────────────────────────────

def t_gitwrite_none_without_flag():
    _clear_flag()
    assert opslib.gitwrite_failed() is None, "بدونِ پرچم باید None باشد"


def t_gitwrite_reason_with_flag():
    _write_flag("GITWRITE-FAILED 2026-07-13 : git index.lock held\nخطِ دوم")
    r = opslib.gitwrite_failed()
    _clear_flag()
    assert r is not None, "پرچمِ برافراشته باید دلیل بدهد"
    assert "GITWRITE-FAILED" in r, f"دلیل نامعتبر: {r!r}"
    assert "\n" not in r, "باید تک‌خطی باشد"


def t_gitwrite_handles_bom():
    """محتوای واقعیِ فایل با BOMِ ویندوز شروع می‌شود — نباید دلیل را خراب کند."""
    _write_flag("﻿GITWRITE-FAILED 2026-07-13_155006 : lock held")
    r = opslib.gitwrite_failed()
    _clear_flag()
    assert r and r.startswith("GITWRITE-FAILED"), f"BOM پاک نشد: {r!r}"


def t_gitwrite_raised_but_empty_still_fails():
    """پرچمِ برافراشته ولی خالی → همچنان یک دلیلِ پیش‌فرض (هرگز None/سبز)."""
    _write_flag("")
    r = opslib.gitwrite_failed()
    _clear_flag()
    assert r is not None, "پرچمِ خالی نباید پنهان شود"


# ── backup_health ───────────────────────────────────────────────────────────────

def t_backup_health_ok_when_fresh_no_flag():
    _clear_flag()
    ob = _fresh_offbox()
    h = opslib.backup_health(offbox=ob)
    assert h["healthy"] is True, f"lag تازه بدونِ پرچم باید سالم باشد: {h}"
    assert h["level"] == "ok"
    assert h["gitwrite_failed"] is None


def t_backup_health_flag_dominates_fresh_mtime():
    """قلبِ OBS-02: mtimeِ تازه (سبز) + پرچمِ FAILED → همچنان ناسالم."""
    ob = _fresh_offbox()
    # پیش‌شرط: بدونِ پرچم همین offbox سالم است
    assert opslib.backup_health(offbox=ob)["healthy"] is True
    _write_flag("﻿GITWRITE-FAILED : job keeps appending FAIL to a log")
    h = opslib.backup_health(offbox=ob)
    _clear_flag()
    assert h["healthy"] is False, f"پرچمِ FAILED باید غالب باشد ولو mtime تازه: {h}"
    assert h["level"] == "err"
    assert h["gitwrite_failed"] is not None
    assert "GITWRITE-FAILED" in h["reason"]


def t_backup_health_err_when_no_artifact():
    _clear_flag()
    ob = Path(tempfile.mkdtemp(prefix="offbox-empty-"))   # هیچ مصنوعی
    h = opslib.backup_health(offbox=ob)
    assert h["healthy"] is False and h["level"] == "err", f"نبودِ مصنوع = err: {h}"


# ── armed_activation_flags ──────────────────────────────────────────────────────

def t_activation_flags_empty_then_armed():
    # پاک‌سازیِ هر پرچمِ ساخته‌شده
    for p in opslib.OPS.glob("ACTIVATION-*.flag"):
        p.unlink()
    assert opslib.armed_activation_flags() == [], "شروع باید خالی باشد"
    (opslib.OPS / "ACTIVATION-DEBATE.flag").write_text("owner", "utf-8")
    (opslib.OPS / "ACTIVATION-GO-LIVE.flag").write_text("owner", "utf-8")
    got = opslib.armed_activation_flags()
    for p in opslib.OPS.glob("ACTIVATION-*.flag"):
        p.unlink()
    assert got == ["ACTIVATION-DEBATE.flag", "ACTIVATION-GO-LIVE.flag"], got


# ── halt_reason (سطحِ نمایشِ توقفِ سراسری) ─────────────────────────────────────────

def t_halt_reason_none_when_clear():
    d = Path(tempfile.mkdtemp(prefix="halt-reason-"))
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
    assert opslib.halt_reason() is None, "بدونِ توقف باید None باشد"


def t_halt_reason_reflects_architect_stop():
    """halt_reason via master_halted: STOP معمار → 'STOP(architect)' (مسیرِ واقعیِ worktree؛
    master_halted همیشه موجود است — دیگر با del مصنوعی حذف نمی‌شود)."""
    d = Path(tempfile.mkdtemp(prefix="halt-reason-"))
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
    opslib.STOP_ARCHITECT.write_text("stop", "utf-8")
    assert opslib.halt_reason() == "STOP(architect)", f"halt_reason نادرست: {opslib.halt_reason()!r}"


def t_halt_reason_reflects_master_halted_haltall():
    """HALT-ALL (مرزِ سختِ سراسری، پنیک) روی halt_reason سطح می‌آید (مقدم بر STOP معمار)."""
    d = Path(tempfile.mkdtemp(prefix="halt-reason-"))
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
    opslib.HALT_ALL.write_text("panic", "utf-8")
    assert opslib.halt_reason() == "HALT-ALL", "HALT-ALL باید سطح بیاید"


# ── هوکِ خودکفای dashboard/server.py (مسیرها → tmp، ایزوله) ───────────────────────

def t_dashboard_selfcontained_hooks():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "dash_srv_probe", _HERE.parent / "dashboard" / "server.py")
    ds = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ds)
    with tempfile.TemporaryDirectory() as td:
        ds.GITWRITE_FAILED = Path(td) / "backup" / "GITWRITE-FAILED.flag"
        ds.HALT_ALL = Path(td) / "HALT-ALL"
        ds.STOP_ARCHITECT = Path(td) / "STOP"
        assert ds._gitwrite_failed() is None
        assert ds._halt_reason() is None
        ds.GITWRITE_FAILED.parent.mkdir(parents=True, exist_ok=True)
        ds.GITWRITE_FAILED.write_text("﻿GITWRITE-FAILED : boom", "utf-8")
        assert (ds._gitwrite_failed() or "").startswith("GITWRITE-FAILED")
        ds.HALT_ALL.write_text("halt", "utf-8")
        assert ds._halt_reason() == "HALT-ALL"


if __name__ == "__main__":
    failed = harness.run([
        ("gitwrite_failed None بدونِ پرچم", t_gitwrite_none_without_flag),
        ("gitwrite_failed دلیل با پرچم", t_gitwrite_reason_with_flag),
        ("gitwrite_failed BOM را پاک می‌کند", t_gitwrite_handles_bom),
        ("پرچمِ خالی هم قرمز می‌شود", t_gitwrite_raised_but_empty_still_fails),
        ("backup_health سالم وقتی تازه+بی‌پرچم", t_backup_health_ok_when_fresh_no_flag),
        ("OBS-02: پرچم غالب بر mtimeِ تازه", t_backup_health_flag_dominates_fresh_mtime),
        ("backup_health err بدونِ مصنوع", t_backup_health_err_when_no_artifact),
        ("armed_activation_flags آینه", t_activation_flags_empty_then_armed),
        ("halt_reason None وقتی پاک", t_halt_reason_none_when_clear),
        ("halt_reason STOP معمار via master_halted", t_halt_reason_reflects_architect_stop),
        ("halt_reason HALT-ALL از master_halted", t_halt_reason_reflects_master_halted_haltall),
        ("هوکِ خودکفای dashboard", t_dashboard_selfcontained_hooks),
    ])
    sys.exit(1 if failed else 0)
