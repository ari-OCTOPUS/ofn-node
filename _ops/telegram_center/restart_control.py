#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""restart_control.py — ری‌استارتِ کاملِ ارگانیسم، فقط با تأییدِ دستیِ مالک از
تلگرام (۲۰۲۶-۰۸-۰۷، درخواستِ صریحِ مالک).

معماری (سه فاز، چون خودِ اسکریپت می‌تواند پروسه‌ای را بکشد که این را صدا زده):
  request_restart(scope)  → درخواست را با approval_store ثبت کن. **صفر اجرا.**
  execute_restart(scope)  → فقط بعد از تأییدِ مالک (ap:ok) صدا زده می‌شود؛ یک
                            پروسهٔ کاملاً جداشدهٔ PowerShell را launch می‌کند
                            (RESTART-ALL.ps1 یا RESTART-PROCESS.ps1 <limb>) و
                            بلافاصله برمی‌گردد — منتظرِ اتمام نمی‌ماند، چون اگر
                            scope شاملِ center/organism باشد، همین پروسه‌ای که
                            الان دارد این تابع را اجرا می‌کند ممکن است وسطِ کار
                            کشته شود.
  check_restart_result()  → از beat ِ دوره‌ایِ center.py صدا زده می‌شود (نه
                            organism، چون آن هم می‌تواند وسطِ scope=all بمیرد).
                            لاگِ اسکریپت را می‌خواند؛ اگر خطِ پایانیِ
                            RESULT:/OK:/WARNING: پیدا شد و هنوز گزارش نشده،
                            یک‌بار برمی‌گرداند و marker را reported می‌کند.

قاعدهٔ سخت: پشتِ `OCTOPUS_WIRE_RESTART_CONTROL` (پیش‌فرض خاموش). اجرای واقعی
(execute_restart) **فقط** بعد از یک approval_store approve واقعی صدا زده
می‌شود — این ماژول خودش هرگز تصمیم نمی‌گیرد کِی ری‌استارت شود، فقط اجرا می‌کند
وقتی چیزِ دیگری (center.py's callback handler) تأیید را دیده.

گاردِ هم‌زمانی: در هر لحظه فقط یک درخواستِ ری‌استارتِ حل‌نشده مجاز است — یک
دومی قبل از این‌که اولی گزارش شود رد می‌شود، تا دو اسکریپتِ PowerShell روی هم
race نکنند.

$0 · stdlib-only (subprocess) · fail-soft در check/report، fail-closed در گارد.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/telegram_center
_OPS = _HERE.parent                                # _ops

if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_RESTART_CONTROL"

VALID_SCOPES = ("all", "organism", "center", "cortex", "live", "gateway")

_STATE_DIR = opslib.STATE_DIR / "telegram" / "restart_control"
_REQUEST_PATH = _STATE_DIR / "request.json"
_LOG_DIR = _STATE_DIR / "logs"

_RESTART_ALL_PS1 = opslib.OPS / "RESTART-ALL.ps1"
_RESTART_PROCESS_PS1 = opslib.OPS / "RESTART-PROCESS.ps1"


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _load_request() -> "dict | None":
    try:
        if not _REQUEST_PATH.exists():
            return None
        d = json.loads(_REQUEST_PATH.read_text("utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _save_request(d: dict) -> bool:
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _REQUEST_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, _REQUEST_PATH)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _clear_request() -> None:
    try:
        _REQUEST_PATH.unlink()
    except OSError:
        pass


def cancel_request() -> None:
    """لغوِ صریحِ درخواستِ حل‌نشده — از callback handler روی ap:no صدا زده
    می‌شود تا مالک بتواند فوراً /restart دیگری بزند (وگرنه گاردِ هم‌زمانی تا
    ابد رد شده می‌ماند). fail-soft — هرگز raise."""
    _clear_request()


def is_restart_in_flight() -> bool:
    """یک درخواستِ حل‌نشده (submitted یا executing، هنوز reported نشده) هست؟"""
    rec = _load_request()
    return bool(rec and not rec.get("reported"))


def request_restart(scope: str, *, job_id: str = "", requested_by: str = "") -> dict:
    """فقط ثبتِ نیت — **هیچ اجرایی این‌جا رخ نمی‌دهد**. خروجی:
    `{"ok": bool, "reason"?}`. scope باید یکی از VALID_SCOPES باشد."""
    if not flag_on():
        return {"ok": False, "reason": "flag-off"}
    scope = str(scope or "").strip().lower()
    if scope not in VALID_SCOPES:
        return {"ok": False, "reason": "invalid_scope"}
    if is_restart_in_flight():
        return {"ok": False, "reason": "already_in_flight"}
    rec = {"scope": scope, "job_id": str(job_id or ""),
           "requested_by": str(requested_by or ""),
           "requested_at": opslib.now_iso(), "status": "submitted",
           "reported": False}
    if not _save_request(rec):
        return {"ok": False, "reason": "store_failed"}
    return {"ok": True}


def execute_restart(scope: "str | None" = None) -> dict:
    """فقط بعد از approval_store.approve صدا زده شود. یک پروسهٔ کاملاً جداشدهٔ
    PowerShell را launch می‌کند و **بدونِ انتظار** برمی‌گردد — چون این تماس
    ممکن است از داخلِ همان پروسه‌ای بیاید که scope شاملِ ری‌استارتِ خودش است.

    `scope=None` یعنی از خودِ request.json بخوان (مسیرِ معمولی از callback
    handler). خروجی: `{"ok": bool, "log_path"?, "reason"?}`."""
    rec = _load_request()
    if rec is None:
        return {"ok": False, "reason": "no_pending_request"}
    scope = str(scope or rec.get("scope") or "").strip().lower()
    if scope not in VALID_SCOPES:
        return {"ok": False, "reason": "invalid_scope"}

    if scope == "all":
        if not _RESTART_ALL_PS1.exists():
            return {"ok": False, "reason": "restart_all_script_missing"}
        args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(_RESTART_ALL_PS1)]
    else:
        if not _RESTART_PROCESS_PS1.exists():
            return {"ok": False, "reason": "restart_process_script_missing"}
        args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(_RESTART_PROCESS_PS1), scope]

    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = _LOG_DIR / f"{rec.get('job_id') or 'restart'}-{int(time.time())}.log"
        with open(log_path, "wb") as logf:
            # ۲۰۲۶-۰۸-۰۷ — اندازه‌گیریِ زنده: DETACHED_PROCESS ضبطِ stdout را
            # بی‌صدا می‌شکند (لاگ همیشه خالی می‌ماند) چون RESTART-ALL.ps1/
            # RESTART-PROCESS.ps1 با Write-Host می‌نویسند که بدونِ کنسول جایی
            # ندارد بنویسد. CREATE_NEW_PROCESS_GROUP تنها به‌تنهایی تست شد و
            # ضبط را درست نگه می‌دارد. نیازی به قطعِ کاملِ رابطهٔ parent/child
            # هم نیست: روی ویندوز، برخلافِ POSIX، مرگِ پروسهٔ مادر به‌طورِ
            # پیش‌فرض فرزند را نمی‌کشد مگر Job Object با kill-on-close صریحاً
            # ست شده باشد — subprocess.Popen ِ ساده چنین Jobی نمی‌سازد.
            creationflags = 0
            if sys.platform == "win32":
                creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            proc = subprocess.Popen(
                args, stdout=logf, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, close_fds=True,
                creationflags=creationflags)
    except OSError as e:
        return {"ok": False, "reason": f"launch_failed:{type(e).__name__}"}

    rec["status"] = "executing"
    rec["pid"] = proc.pid
    rec["log_path"] = str(log_path)
    rec["executing_at"] = opslib.now_iso()
    _save_request(rec)
    return {"ok": True, "log_path": str(log_path), "pid": proc.pid}


_TERMINAL_MARKERS = ("RESULT: OK", "RESULT: FAILED", "OK: organism running",
                     "OK: restarted with fresh code.", "OK: gateway restarted",
                     "WARNING:", "TIMEOUT:", "ERROR:")


def check_restart_result() -> "dict | None":
    """از beat ِ center.py صدا زده شود. اگر درخواستِ در حالِ اجرا به یک خطِ
    پایانی رسیده و هنوز گزارش نشده، **یک‌بار** نتیجه را برمی‌گرداند و
    marker را reported=True می‌کند. وگرنه None (fail-soft کامل — هرگز raise)."""
    try:
        rec = _load_request()
        if rec is None or rec.get("reported") or rec.get("status") != "executing":
            return None
        log_path = rec.get("log_path")
        if not log_path or not Path(log_path).exists():
            return None
        text = Path(log_path).read_text("utf-8", errors="replace")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        terminal = None
        for ln in reversed(lines):
            if any(marker in ln for marker in _TERMINAL_MARKERS):
                terminal = ln
                break
        if terminal is None:
            return None
        rec["reported"] = True
        rec["result_line"] = terminal
        rec["completed_at"] = opslib.now_iso()
        _save_request(rec)
        ok = terminal.startswith("RESULT: OK") or terminal.startswith("OK:")
        return {"scope": rec.get("scope"), "ok": ok, "result_line": terminal,
                "job_id": rec.get("job_id")}
    except Exception:  # noqa: BLE001 — beat هرگز نباید بترکد
        return None


def beat(center=None) -> dict:
    """یک تیک: اگر ری‌استارتی تازه به خطِ پایانی رسیده، به مالک خبر بده.
    از center.py صدا زده می‌شود (نه organism — آن هم می‌تواند وسطِ scope=all
    بمیرد)، هم‌الگوی event_bridge.beat/doctor_link.beat: fail-soft کامل،
    وابسته به client ِ همان center، بدونِ pollerِ نو."""
    out = {"reported": False}
    if not flag_on():
        out["reason"] = "flag-off"
        return out
    try:
        result = check_restart_result()
    except Exception:  # noqa: BLE001
        result = None
    if result is None:
        return out
    client = getattr(center, "_client", None)
    if client is None:
        out["reason"] = "no-client"
        return out
    icon = "✅" if result.get("ok") else "⚠️"
    scope = str(result.get("scope") or "؟")
    line = str(result.get("result_line") or "")[:200]
    text = f"{icon} ری‌استارتِ <code>{scope}</code> تمام شد.\n<code>{line}</code>"
    try:
        route_send = getattr(center, "_route_send", None)
        if callable(route_send):
            route_send("center-alert", text)
        else:
            client.send(text, chat_id=getattr(client, "owner_chat_id", None))
        out["reported"] = True
    except Exception:  # noqa: BLE001
        pass
    return out


if __name__ == "__main__":   # pragma: no cover — نمای دستیِ اپراتور
    print(json.dumps({"flag": FLAG, "enabled": flag_on(),
                      "in_flight": is_restart_in_flight(),
                      "request": _load_request()}, ensure_ascii=False, indent=1))
