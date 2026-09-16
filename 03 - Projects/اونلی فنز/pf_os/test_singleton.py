#!/usr/bin/env python3
"""test_singleton.py — تست‌های قفلِ تک‌نمونه برای pf_os.

تست‌ها: acquire، re-acquire same pid، block different pid، stale takeover،
release، ExclusiveHTTPServer bind، check_port_taken.
"""
from __future__ import annotations

import os
import socket
import sys
import time
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from pf_os import singleton as S  # noqa: E402
from pf_os import config  # noqa: E402


class TestPIDLock(unittest.TestCase):

    def setUp(self):
        config.ensure_pf_state()
        # تمیز کردنِ هر lock باقی‌مانده از تست‌های قبلی
        for name in ("test_a", "test_b", "test_stale"):
            p = S._lockfile(name)
            try:
                p.unlink()
            except OSError:
                pass

    def tearDown(self):
        for name in ("test_a", "test_b", "test_stale"):
            p = S._lockfile(name)
            try:
                p.unlink()
            except OSError:
                pass

    def test_acquire_returns_lock(self):
        lock = S.acquire_pid_lock("test_a")
        self.assertIsNotNone(lock)
        self.assertEqual(lock.name, "test_a")
        self.assertTrue(lock.path.exists())

    def test_re_acquire_same_pid_overwrites(self):
        """همان pid باید بتواند دوباره lock بگیرد (restart در همان process)."""
        lock1 = S.acquire_pid_lock("test_a")
        self.assertIsNotNone(lock1)
        lock2 = S.acquire_pid_lock("test_a")
        self.assertIsNotNone(lock2)

    def test_block_different_fresh_pid(self):
        """pid متفاوت با lock تازه نباید بتواند بگیرد."""
        p = S._lockfile("test_b")
        other_pid = 999999  # احتمالاً مرده، ولی mtime تازه
        p.write_text(f"{other_pid}:{int(time.time())}", encoding="utf-8")
        lock = S.acquire_pid_lock("test_b")
        self.assertIsNone(lock, "different fresh PID must be blocked")

    def test_stale_takeover(self):
        """lock قدیمی (>120s) باید قابلِ takeover باشد."""
        p = S._lockfile("test_stale")
        p.write_text(f"999999:{int(time.time())-200}", encoding="utf-8")
        # شبیه‌سازی mtime قدیمی (الگوی واقعی: process کرش کرده، فایل قدیمی مانده)
        old = time.time() - 200
        os.utime(p, (old, old))
        lock = S.acquire_pid_lock("test_stale")
        self.assertIsNotNone(lock, "stale lock must be takeable")

    def test_release_removes_lockfile(self):
        lock = S.acquire_pid_lock("test_a")
        S.release_pid_lock(lock)
        self.assertFalse(lock.path.exists())

    def test_release_idempotent(self):
        """release دوباره نباید شکست بخورد."""
        lock = S.acquire_pid_lock("test_a")
        S.release_pid_lock(lock)
        S.release_pid_lock(lock)  # نباید exception
        S.release_pid_lock(None)  # نباید exception

    def test_release_doesnt_touch_other_pid(self):
        """release نباید lockِ pid دیگر را پاک کند (ضدِ stale-takeover)."""
        p = S._lockfile("test_a")
        other_pid = 999999
        p.write_text(f"{other_pid}:{int(time.time())}", encoding="utf-8")
        fake_lock = S.PIDLock(name="test_a", path=p, pid=os.getpid())
        S.release_pid_lock(fake_lock)
        # فایل باید همچنان باشد چون pid در lock != fake_lock.pid
        self.assertTrue(p.exists())


class TestExclusiveHTTPServer(unittest.TestCase):
    """تستِ bindِ انحصاری — مهم‌ترین نامتغیرِ singleton."""

    def test_first_bind_succeeds(self):
        # یک port آزاد پیدا کن
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        import http.server
        srv = S.ExclusiveHTTPServer(
            ("127.0.0.1", port),
            http.server.BaseHTTPRequestHandler)
        try:
            srv.server_close()
        except Exception:
            pass
        # اگر بدون exception ساخت، یعنی bind موفق بود
        self.assertIsNotNone(srv)

    def test_port_taken_detection(self):
        """check_port_taken باید port در حالِ استفاده را True برگرداند."""
        # bind یک port موقت
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        port = sock.getsockname()[1]
        try:
            self.assertTrue(S.check_port_taken(port))
        finally:
            sock.close()

    def test_port_free_returns_false(self):
        """یک port قطعاً آزاد باید False برگرداند."""
        # port 1 معمولاً قابل-bind نیست ولی check_port_taken False می‌دهد چون connect fail می‌شود
        self.assertFalse(S.check_port_taken(1, "127.0.0.1"))


if __name__ == "__main__":
    unittest.main()
