#!/usr/bin/env python3
"""singleton.py — قفلِ تک‌نمونه برای pf_os (همراه با Saba bot و آینده‌ی API).

دو لایه‌ی دفاعی (طبقِ الگوی _ops/organism.py:107-115 و _ops/wiring.py:1200):

  1. PIDLockfile — مبتنی بر فایل .lock (الگوی cursor/lock wiring.py).
     دو process هم‌زمان نمی‌توانند یک pf_os/Saba را run کنند. lock advisory است
     (PID-based)، پس اگر process کرش کرد، بعد از ۱۲۰ ثانیه stale می‌شود.

  2. ExclusiveHTTPServer — برای فاز ۴ (API). روی پورتِ انحصاری bind می‌کند.

استفاده در run_saba.py:
    from pf_os.singleton import acquire_pid_lock, release_pid_lock
    pid_lock = acquire_pid_lock("saba")
    if pid_lock is None:
        print("🔴 قبلاً در حالِ اجراست (PID در lock file). خروج.")
        return 1
    try:
        ... run bot ...
    finally:
        release_pid_lock(pid_lock)

$0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import os
import socket
import time
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from . import config

STALE_SECONDS = 120  # اگر lock قدیمی‌تر از این بود، stale محسوب می‌شود


@dataclass
class PIDLock:
    name: str
    path: Path
    pid: int


def _lockfile(name: str) -> Path:
    """مسیرِ lock file برای یک singletonِ نام‌گذاری‌شده."""
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in name)[:40]
    return Path(config.PF_STATE) / f"{safe}.lock"


def _is_stale(path: Path) -> bool:
    """آیا lock فایل stale است (process مرده یا خیلی قدیمی)؟"""
    try:
        age = time.time() - path.stat().st_mtime
        return age > STALE_SECONDS
    except OSError:
        return True


def acquire_pid_lock(name: str) -> Optional[PIDLock]:
    """تلاش برای گرفتنِ lock تک‌نمونه. برمی‌گرداند PIDLock یا None اگر قبلاً گرفته شده.

    race-safe نیست ۱۰۰٪ (نوتیس: advisory)، ولی برای جلوگیری از ۹۵٪ مواردِ double-run
    کافیست. الگوی مشابه wiring.py:1200 (advisory PID lock).
    """
    config.ensure_pf_state()
    p = _lockfile(name)
    my_pid = os.getpid()
    if p.exists():
        try:
            prev = p.read_text(encoding="utf-8").strip()
            prev_pid = prev.split(":", 1)[0] if ":" in prev else prev
            if prev_pid and prev_pid != str(my_pid) and not _is_stale(p):
                return None  # locked by other
        except (OSError, ValueError):
            pass  # corrupt — overwrite
    try:
        p.write_text(f"{my_pid}:{int(time.time())}", encoding="utf-8")
    except OSError:
        return None
    return PIDLock(name=name, path=p, pid=my_pid)


def release_pid_lock(lock: PIDLock) -> None:
    """آزاد کردنِ lock. فقط اگر PID ما در آن است (ضدِ stale-takeover)."""
    if lock is None:
        return
    try:
        prev = lock.path.read_text(encoding="utf-8").strip()
        prev_pid = prev.split(":", 1)[0] if ":" in prev else prev
        if prev_pid == str(lock.pid):
            lock.path.unlink()
    except OSError:
        pass


# ═════════════════════════════════════════════════════════════════════════════
# ExclusiveHTTPServer — برای فاز ۴ (REST API). کپیِ وفادارِ organism.py:107-115
# ═════════════════════════════════════════════════════════════════════════════

class ExclusiveHTTPServer(ThreadingHTTPServer):
    """سرورِ HTTP با bindِ انحصاری — جلویِ double-run روی همان port.

    طبقِ الگوی _ops/organism.py:107-115: http.server پیش‌فرض SO_REUSEADDR دارد
    و double-bind را ساکت می‌سازد. این کلاس آن را انحصاری می‌کند.
    """
    allow_reuse_address = False
    daemon_threads = True

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            # ویندوز: انحصاریِ سخت. هر bindِ دوم = OSError.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        elif hasattr(socket, "SO_REUSEADDR"):
            # POSIX: حداقل reuse را خاموش کن (بهتر از هیچ)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        super().server_bind()


def check_port_taken(port: int, host: str = "127.0.0.1") -> bool:
    """آیا port قبلاً گرفته شده؟ برای pre-flight check قبل از bind."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        result = s.connect_ex((host, port)) == 0
        s.close()
        return result
    except OSError:
        return False
