#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_restart_control — ری‌استارتِ کاملِ ارگانیسم فقط با تأییدِ دستیِ مالک
(۲۰۲۶-۰۸-۰۷، درخواستِ صریحِ مالک).

ادعاهای باربر:
  ۱) فلگ خاموش (پیش‌فرض) → request_restart هیچ درخواستی ثبت نمی‌کند.
  ۲) scopeِ نامعتبر → رد، بدونِ ثبت.
  ۳) گاردِ هم‌زمانی: درخواستِ دوم وقتی اولی حل‌نشده → رد (ضدِ رِیسِ دو اسکریپت).
  ۴) execute_restart بدونِ درخواستِ pending → BLOCKED، صفر subprocess.
  ۵) check_restart_result فقط یک‌بار گزارش می‌دهد (idempotent).
  ۶) پایانِ e2e ِ واقعی: یک اسکریپتِ دامیِ PowerShellِ واقعی launch می‌شود،
     خودش را از پروسه‌ای که آن را ساخته مستقل نگه می‌دارد، و نتیجه‌اش خوانده
     می‌شود — نه فقط شبیه‌سازیِ فایل.

mutation-gate: اگر گاردِ in-flight حذف شود، تستِ
t_second_request_while_in_flight_is_rejected قرمز می‌شود.

⚠️ این سوئیت واقعاً یک زیرپروسهٔ PowerShell می‌سازد (نه mock) — کندتر از
معمول (~۵-۱۰ ثانیه)، عمداً: باگِ واقعیِ DETACHED_PROCESS (ضبطِ stdout را
بی‌صدا می‌شکست چون Write-Host بدونِ کنسول جایی ندارد بنویسد) فقط با اجرایِ
واقعی کشف شد، نه با mock.
"""
import json
import os
import sys
import time
from pathlib import Path

import harness

ENV = harness.setup("restart-control")

_OPS_SELF = Path(__file__).resolve().parent.parent
if str(_OPS_SELF / "telegram_center") not in sys.path:
    sys.path.insert(0, str(_OPS_SELF / "telegram_center"))

import restart_control as rc  # noqa: E402


class _Flag:
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


def _reset():
    rc._clear_request()


# ════════════════════════════════════════════════════════════════════════════
# (۱) فلگ خاموش
# ════════════════════════════════════════════════════════════════════════════
def t_flag_off_request_creates_nothing():
    _reset()
    with _Flag(rc.FLAG, None):
        r = rc.request_restart("all")
    assert r == {"ok": False, "reason": "flag-off"}, r
    assert rc._load_request() is None


# ════════════════════════════════════════════════════════════════════════════
# (۲) scopeِ نامعتبر
# ════════════════════════════════════════════════════════════════════════════
def t_invalid_scope_is_rejected():
    _reset()
    with _Flag(rc.FLAG, "1"):
        r = rc.request_restart("everything-please")
    assert r == {"ok": False, "reason": "invalid_scope"}, r
    assert rc._load_request() is None


def t_all_valid_scopes_accepted():
    for scope in rc.VALID_SCOPES:
        _reset()
        with _Flag(rc.FLAG, "1"):
            r = rc.request_restart(scope, job_id=f"j-{scope}")
        assert r == {"ok": True}, (scope, r)
        rec = rc._load_request()
        assert rec["scope"] == scope, rec


# ════════════════════════════════════════════════════════════════════════════
# (۳) گاردِ هم‌زمانی
# ════════════════════════════════════════════════════════════════════════════
def t_second_request_while_in_flight_is_rejected():
    _reset()
    with _Flag(rc.FLAG, "1"):
        r1 = rc.request_restart("organism", job_id="j1")
        assert r1["ok"] is True
        assert rc.is_restart_in_flight() is True
        r2 = rc.request_restart("center", job_id="j2")
    assert r2 == {"ok": False, "reason": "already_in_flight"}, r2
    # اولی دست‌نخورده مانده، نه بازنویسی‌شده
    assert rc._load_request()["job_id"] == "j1"


def t_in_flight_clears_after_report():
    _reset()
    with _Flag(rc.FLAG, "1"):
        rc.request_restart("organism", job_id="j1")
    rec = rc._load_request()
    rec["status"] = "executing"
    rc._LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = rc._LOG_DIR / "fake.log"
    log.write_text("OK: organism running with fresh code.\n", "utf-8")
    rec["log_path"] = str(log)
    rc._save_request(rec)
    assert rc.is_restart_in_flight() is True
    rc.check_restart_result()
    assert rc.is_restart_in_flight() is False


# ════════════════════════════════════════════════════════════════════════════
# (۴) execute_restart بدونِ درخواستِ pending
# ════════════════════════════════════════════════════════════════════════════
def t_execute_without_pending_request_is_blocked():
    _reset()
    r = rc.execute_restart("all")
    assert r == {"ok": False, "reason": "no_pending_request"}, r


# ════════════════════════════════════════════════════════════════════════════
# (۵) check_restart_result idempotent
# ════════════════════════════════════════════════════════════════════════════
def t_check_result_reports_exactly_once():
    _reset()
    with _Flag(rc.FLAG, "1"):
        rc.request_restart("all", job_id="j1")
    rec = rc._load_request()
    rec["status"] = "executing"
    rc._LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = rc._LOG_DIR / "fake.log"
    log.write_text("BEFORE : x\nRESULT: OK - every limb restarted.\n", "utf-8")
    rec["log_path"] = str(log)
    rc._save_request(rec)

    r1 = rc.check_restart_result()
    assert r1 is not None and r1["ok"] is True, r1
    r2 = rc.check_restart_result()
    assert r2 is None, r2


def t_check_result_no_terminal_line_yet_returns_none():
    _reset()
    with _Flag(rc.FLAG, "1"):
        rc.request_restart("organism", job_id="j1")
    rec = rc._load_request()
    rec["status"] = "executing"
    rc._LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = rc._LOG_DIR / "fake.log"
    log.write_text("BEFORE : x\nSTOP marker created - waiting...\n", "utf-8")
    rec["log_path"] = str(log)
    rc._save_request(rec)
    assert rc.check_restart_result() is None


def t_check_result_failure_line_is_reported_as_not_ok():
    _reset()
    with _Flag(rc.FLAG, "1"):
        rc.request_restart("organism", job_id="j1")
    rec = rc._load_request()
    rec["status"] = "executing"
    rc._LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = rc._LOG_DIR / "fake.log"
    log.write_text("BEFORE : x\nTIMEOUT: old process still alive.\n", "utf-8")
    rec["log_path"] = str(log)
    rc._save_request(rec)
    r = rc.check_restart_result()
    assert r is not None and r["ok"] is False, r


# ════════════════════════════════════════════════════════════════════════════
# (۶) e2e واقعی — زیرپروسهٔ PowerShellِ واقعی
# ════════════════════════════════════════════════════════════════════════════
def t_execute_restart_real_subprocess_survives_and_reports():
    """باگِ واقعیِ کشف‌شده امشب: DETACHED_PROCESS لاگ را همیشه خالی می‌گذاشت
    چون Write-Host بدونِ کنسول جایی برای نوشتن نداشت. این تست همان مسیرِ
    واقعیِ execute_restart→check_restart_result را با یک اسکریپتِ دامی
    اما زیرپروسهٔ حقیقی می‌راند."""
    _reset()
    dummy = ENV["ops"] / "dummy_restart.ps1"
    dummy.write_text(
        'Write-Host "BEFORE : test"\r\n'
        'Start-Sleep -Seconds 1\r\n'
        'Write-Host "RESULT: OK - dummy e2e done."\r\n', encoding="utf-8")
    old_script = rc._RESTART_ALL_PS1
    rc._RESTART_ALL_PS1 = dummy
    try:
        with _Flag(rc.FLAG, "1"):
            r = rc.request_restart("all", job_id="e2e1")
            assert r["ok"] is True, r
            ex = rc.execute_restart()
            assert ex["ok"] is True, ex
            assert ex["pid"] > 0, ex
            # درست بعدِ launch — هنوز نباید چیزی برای گزارش باشد
            assert rc.check_restart_result() is None
            deadline = time.time() + 15
            result = None
            while time.time() < deadline:
                result = rc.check_restart_result()
                if result is not None:
                    break
                time.sleep(0.5)
            assert result is not None, "زیرپروسه ظرفِ ۱۵ ثانیه نتیجه ننوشت"
            assert result["ok"] is True, result
            assert "dummy e2e done" in result["result_line"], result
    finally:
        rc._RESTART_ALL_PS1 = old_script
        try:
            dummy.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_restart_control: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
