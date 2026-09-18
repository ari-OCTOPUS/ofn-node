#!/usr/bin/env python3
"""action_executor.py — اجرای عمومی کارهای پیش‌بینی‌نشده (WHY-SLOW-250 / U-WORK v1)

مسئله: کارت‌هایی که از قبل typed tool ندارند، فقط «تأیید ثبت شد» می‌گرفتند و
هیچ کاری نمی‌کردند. این ماژول همان شکاف را می‌بندد: یک پیشنهاد، یک `action`
با type مشخص می‌آورد؛ اگر type در allowlist باشد اجرا می‌شود (با pre-image،
رسید، rollback). هر چیز بیرون allowlist = `ACTION_NOT_ALLOWED` + پیشنهاد
درخواست کلاس جدید از مالک. هیچ secret چاپ نمی‌شود؛ هیچ اثر بیرونی بدون رأی
مالک اجرا نمی‌شود.

allowlist v1: write_file · append_jsonl · run_script · send_email_batch · none
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path("/home/ari/ofn")
ALLOWED_ROOTS = [ROOT / "state"]
RECEIPTS = ROOT / "state/revenue-drive/receipts.jsonl"
MAX_BYTES = 200_000
RUN_TIMEOUT = 60

REDMIND = ("red_external", "money", "public", "customer")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _receipt(kind, **kw):
    row = {"schema": "octopus.action-exec.v1", "at": now(), "kind": kind, **kw}
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def _safe_path(raw) -> pathlib.Path:
    """path must resolve INSIDE an allowed root; no traversal, no symlink escape."""
    p = pathlib.Path(str(raw))
    if not p.is_absolute():
        p = ROOT / p
    rp = p.resolve()
    if not any(str(rp).startswith(str(r.resolve()) + os.sep) or rp == r.resolve()
               for r in ALLOWED_ROOTS):
        raise PermissionError("PATH_OUTSIDE_ALLOWED_ROOTS:%s" % raw)
    return rp


def shadow(action: dict) -> dict:
    """بدون هیچ نوشتن: فقط می‌گوید چه اتفاقی می‌افتد + اعتبارسنجی."""
    t = str(action.get("type") or "")
    a = action.get("args") or {}
    try:
        if t in ("write_file", "append_jsonl"):
            p = _safe_path(a.get("path"))
            exists = p.exists()
            before = _sha(p) if exists else None
            body = str(a.get("content") or a.get("line") or "")
            return {"type": t, "would": "write" if t == "write_file" else "append",
                    "path": str(p), "exists": exists, "preimage_sha256": before,
                    "bytes": len(body.encode("utf-8")),
                    "valid": len(body.encode("utf-8")) <= MAX_BYTES,
                    "reason": "" if len(body.encode("utf-8")) <= MAX_BYTES else "TOO_BIG"}
        if t == "run_script":
            p = _safe_path(a.get("path"))
            if not p.exists():
                return {"type": t, "valid": False, "reason": "SCRIPT_NOT_FOUND", "path": str(p)}
            r = subprocess.run([sys.executable, "-m", "py_compile", str(p)],
                               capture_output=True, text=True, timeout=30)
            return {"type": t, "valid": r.returncode == 0, "path": str(p),
                    "compile_ok": r.returncode == 0, "stderr": (r.stderr or "")[:200]}
        if t == "send_email_batch":
            n = len(a.get("packets") or [])
            return {"type": t, "valid": n > 0, "packets": n,
                    "note": "needs an owner tap naming email (two-step release)"}
        if t == "none":
            return {"type": t, "valid": True, "note": "record-only"}
        return {"type": t or "?", "valid": False, "reason": "ACTION_NOT_ALLOWED",
                "allowed": ["write_file", "append_jsonl", "run_script",
                            "send_email_batch", "none"]}
    except Exception as exc:  # noqa: BLE001
        return {"type": t or "?", "valid": False, "reason": "%s:%s" % (type(exc).__name__, exc)}


def execute(action: dict, via: str = "unknown", card_id: str = None,
            risk: str = "internal_green") -> dict:
    """اجرا با pre-image + رسید + rollback. اثر بیرونی فقط از مسیر رأی مالک."""
    a = action.get("args") or {}
    t = str(action.get("type") or "")
    if via != "owner_card" and risk in REDMIND:
        _receipt("ACTION_REFUSED_NEEDS_OWNER", type=t, risk=risk, via=via)
        return {"ok": False, "reason": "RED_BOUNDARY_NEEDS_OWNER_TAP",
                "note": "این نوع اثر فقط با تپ کارت مالک اجرا می‌شود"}
    try:
        if t == "none" or not t:
            _receipt("ACTION_NONE", via=via, card=card_id)
            return {"ok": True, "action": "none", "note": "ثبت شد (بدون اقدام)"}

        if t in ("write_file", "append_jsonl"):
            p = _safe_path(a.get("path"))
            p.parent.mkdir(parents=True, exist_ok=True)
            pre = None
            if p.exists():
                pre = p.with_name(p.name + ".pre-action-" + now().replace(":", ""))
                pre.write_bytes(p.read_bytes())
            before = _sha(p) if p.exists() else None
            body = str(a.get("content") or a.get("line") or "")
            if len(body.encode("utf-8")) > MAX_BYTES:
                return {"ok": False, "reason": "TOO_BIG"}
            mode = "a" if t == "append_jsonl" else "w"
            with p.open(mode, encoding="utf-8") as fh:
                if t == "append_jsonl":
                    fh.write(body.rstrip("\n") + "\n")
                else:
                    fh.write(body)
            _receipt("ACTION_EXECUTED", type=t, path=str(p), via=via, card=card_id,
                     preimage=str(pre) if pre else None, sha_before=before,
                     sha_after=_sha(p))
            return {"ok": True, "action": t, "path": str(p),
                    "preimage": str(pre) if pre else None,
                    "rollback": ("cp %s %s" % (pre, p)) if pre else ("os.remove(%s)" % p),
                    "note": "✅ اجرا شد (%s) با رسید و rollback" % t}

        if t == "run_script":
            p = _safe_path(a.get("path"))
            if not p.exists():
                return {"ok": False, "reason": "SCRIPT_NOT_FOUND"}
            args = [str(x) for x in (a.get("argv") or [])]
            r = subprocess.run([sys.executable, str(p)] + args, capture_output=True,
                               text=True, timeout=RUN_TIMEOUT, cwd=str(ROOT))
            out = (r.stdout or "")[-1500:]
            err = (r.stderr or "")[-600:]
            _receipt("ACTION_EXECUTED", type=t, path=str(p), via=via, card=card_id,
                     rc=r.returncode, stdout=out[-400:], stderr=err[-200:])
            return {"ok": r.returncode == 0, "action": t, "rc": r.returncode,
                    "stdout": out, "stderr": err,
                    "note": ("✅ اسکریپت اجرا شد (rc=%s)" % r.returncode) if r.returncode == 0
                            else ("⚠️ اسکریپت با rc=%s تمام شد (خروجی در رسید)" % r.returncode)}

        if t == "send_email_batch":
            if via != "owner_card" or not a.get("email_authorized"):
                _receipt("ACTION_REFUSED", type=t, reason="NEEDS_OWNER_EMAIL_AUTH", via=via)
                return {"ok": False, "reason": "NEEDS_OWNER_EMAIL_AUTH",
                        "note": "ارسال ایمیل فقط با تپ کارت مالک (رأی دو مرحله‌ای)"}
            sys.path.insert(0, str(ROOT / "state/revenue-drive"))
            import money_tools  # noqa: E402
            res = money_tools.execute_money_batch(packets=a.get("packets") or [],
                                                  email_authorized=True)
            n = len(res.get("email_sent") or [])
            return {"ok": bool(n), "action": t, **res,
                    "note": ("✅ %d ایمیل ارسال شد (رسید ثبت شد)" % n) if n
                            else ("⚠️ ارسال نشد — دلیل: %s"
                                  % str(res.get("blocked_on") or res.get("failed") or "?")[:200])}

        _receipt("ACTION_NOT_ALLOWED", type=t, via=via, card=card_id)
        return {"ok": False, "reason": "ACTION_NOT_ALLOWED", "type": t,
                "note": ("⛔ این نوع کار هنوز در allowlist نیست. برای افزودن، یک کارت "
                         "«کلاس جدید» لازم است تا مالک یک‌بار تأیید کند.")}

    except Exception as exc:  # noqa: BLE001
        _receipt("ACTION_FAILED", type=t, via=via, card=card_id,
                 error="%s:%s" % (type(exc).__name__, str(exc)[:200]))
        return {"ok": False, "reason": "%s:%s" % (type(exc).__name__, str(exc)[:200]),
                "note": "⚠️ اجرا نشد؛ خطا در رسید ثبت شد (شکست حفظ می‌شود)"}
