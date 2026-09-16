#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runner.py — اجرای کاندید در «جعبهٔ کار» (policy sandbox) — فاز ۳ MEGA-FINISH-ALL-v1.

محافظ‌ها (همه fail-closed؛ نبودِ اطمینان = اجرا نکن):
  1. پیش‌اسکن الگوی ممنوع (شبکه، زیرپروسس، پوسته، دستکاری env، مسیر مطلق) → BLOCKED.
  2. محیطِ scrubbed: فقط allowlistِ متغیرها؛ هیچ TOKEN/KEY/SECRET/PASS به کاندید نمی‌رسد.
  3. اجرا با `python -I -P -u` (isolated + safe path) در cwd=workspace اختصاصی.
  4. stdin بسته؛ timeout با کشت کامل درخت پروسه؛ خروجی محدودشده.
  5. پس‌اجرا: اسکن فایل‌های workspace — هر فایل بیرون از workspace = رویداد امنیتی.

صداقت مرزی (رکورد می‌شود، نه پنهان):
  ویندوز namespace/mount/network-namespace ندارد؛ پس `isolation_verdict.level` =
  policy_workspace_env_timeout است و `os_namespace_isolation=False` — یعنی این
  «آزمایشگاه سختِ OS-level» نیست و نباید ادعا شود (LAB-DOCTOR-CONTRACT gate 3:
  BLOCKED_NOT_VERIFIED تا تست‌های منفیِ OS-level). برای mutationها همین قرارداد
  سیاستی + صفر credential + صفر شبکهٔ واقعی، تنها چیزی است که امروز ادعا می‌کنیم.

stdlib-only · fail-soft (هیچ استثنا بیرون نمی‌رود).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA = "lab-runner.v1"
GRADE = "MEASURED"

ALLOWED_ENV = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP",
               "PYTHONIOENCODING", "SYSTEMDRIVE", "PROCESSOR_ARCHITECTURE")
SECRET_PATTERNS = ("token", "secret", "password", "pass", "cred", "api_key",
                   "authorization", "private_key")

_BANNED_SUBSTR = (
    "import socket", "from socket", "import http", "urllib", "requests",
    "httpx", "import ssl", "websocket", "grpc", "aiohttp",
    "os.system", "os.popen", "subprocess", "os.startfile", "ctypes",
    "winreg", "multiprocessing", "popen", "os.environ", "getenv",
    "powershell", "cmd.exe", "/bin/sh", "/bin/bash", "invoke-",
    "shutil.rmtree", "shutil.move", "os.remove", "os.unlink", "os.chdir",
    "pickle.loads", "eval(", "exec(",
)
_ABS_PATH_RE = re.compile(r'''["'](?:[A-Za-z]:[\\/]|/|\\\\)|["']~''')


def _scan(source: str) -> list:
    """پیش‌اسکن: لیست رویدادهای امنیتی؛ خالی = پاک."""
    events = []
    for pat in _BANNED_SUBSTR:
        if pat in source.lower():
            events.append({"kind": "banned-pattern", "pattern": pat})
    for m in _ABS_PATH_RE.finditer(source):
        events.append({"kind": "absolute-path-literal", "sample": m.group(0)[:40]})
    return events


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True, timeout=10)
        else:
            os.killpg(os.getpgid(proc.pid), 9)
    except Exception:  # noqa: BLE001
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass


class SandboxRunner:
    def __init__(self, workspace_root: Path | None = None, cleanup: bool = False):
        if workspace_root is None:
            workspace_root = Path(__file__).resolve().parent.parent / "state" / "lab" / "workspaces"
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.cleanup = cleanup

    def run(self, source: str, name: str = "candidate", timeout_s: float = 10.0,
            extra_files: dict | None = None) -> dict:
        """اجرای یک کاندید. هیچ استثنا بیرون نمیرود؛ شکست = dict با ok=False.

        extra_files: {نام_فایل: محتوا} که پیش از اجرا داخل workspace نوشته میشوند
        (فیکسچرها/ماژولِ واقعیِ کاندید برای اجرای real-code در جعبه)."""
        started = time.time()
        src_hash = hashlib.sha256(str(source).encode("utf-8", "replace")).hexdigest()[:24]
        ws = self.workspace_root / f"{name}-{int(time.time() * 1000)}"
        events: list = []
        try:
            events = _scan(str(source))
            if events:
                return {"schema": SCHEMA, "grade": GRADE, "ok": False, "blocked": True,
                        "security_events": events, "source_hash": src_hash,
                        "name": name, "workspace": str(ws),
                        "isolation_verdict": self._verdict(), "elapsed_s": time.time() - started}
            ws.mkdir(parents=True, exist_ok=True)
            (ws / "main.py").write_text(str(source), encoding="utf-8")
            for fname, content in (extra_files or {}).items():
                (ws / fname).write_text(str(content), encoding="utf-8")
            env = {k: os.environ.get(k) for k in ALLOWED_ENV if os.environ.get(k) is not None}
            cmd = [sys.executable, "-I", "-P", "-u", "main.py"]
            proc = subprocess.Popen(cmd, cwd=str(ws), env=env, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, encoding="utf-8", errors="replace")
            timed_out = False
            try:
                out, err = proc.communicate(timeout=float(timeout_s))
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_tree(proc)
                try:
                    out, err = proc.communicate(timeout=5)
                except Exception:  # noqa: BLE001
                    out, err = "", "killed-after-timeout"
            # پس‌اجرا: هر فایلی که خارج از workspace resolve شود = رویداد امنیتی
            for f in ws.rglob("*"):
                try:
                    if not f.resolve().is_relative_to(ws.resolve()):
                        events.append({"kind": "file-outside-workspace", "path": str(f)})
                except Exception:  # noqa: BLE001
                    pass
            return {
                "schema": SCHEMA, "grade": GRADE, "ok": True, "blocked": False,
                "exit_code": proc.returncode, "timeout": timed_out,
                "stdout_tail": (out or "")[-500:], "stderr_tail": (err or "")[-300:],
                "security_events": events, "source_hash": src_hash,
                "name": name, "workspace": str(ws),
                "files_created": [str(f.relative_to(ws)) for f in ws.rglob("*") if f.is_file()],
                "isolation_verdict": self._verdict(), "elapsed_s": round(time.time() - started, 3),
            }
        except Exception as e:  # noqa: BLE001
            return {"schema": SCHEMA, "grade": GRADE, "ok": False, "blocked": True,
                    "error": f"{type(e).__name__}: {str(e)[:200]}",
                    "security_events": events, "source_hash": src_hash,
                    "name": name, "elapsed_s": round(time.time() - started, 3),
                    "isolation_verdict": self._verdict()}
        finally:
            if self.cleanup:
                try:
                    import shutil
                    shutil.rmtree(ws, ignore_errors=True)
                except Exception:  # noqa: BLE001
                    pass

    @staticmethod
    def _verdict() -> dict:
        return {
            "level": "policy_workspace_env_timeout",
            "os_namespace_isolation": False,
            "note": ("Windows: بدون mount/network-namespace؛ محافظ = پیشاسکن الگو + "
                     "scrub محیط + workspace اختصاصی + timeout با کشت درخت + پساسکن. "
                     "سطح OS تأییدنشده — LAB-DOCTOR-CONTRACT gate3 همچنان NOT_VERIFIED."),
        }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-file", required=True)
    ap.add_argument("--name", default="candidate")
    ap.add_argument("--timeout", type=float, default=10.0)
    args = ap.parse_args()
    src = Path(args.source_file).read_text("utf-8")
    print(json.dumps(SandboxRunner().run(src, name=args.name, timeout_s=args.timeout),
                     ensure_ascii=False, indent=1))
