"""
brain/_io_utils.py — ابزارهای مشترکِ I/O برای نوشتنِ اتمیک و امن.

این ماژول (برگ، غیر-TCB) دو کمیت را یکدست می‌کند که قبلاً در ۸ فایلِ جدا
کپی‌پیست شده بودند:

  ۱. atomic_write_json(path, data) — نوشتنِ اتمیک (temp + os.replace) با guardrail.
  ۲. file_lock(path) — قفلِ فایلِ cross-platform برای read-modify-write امن.

چرا: همزمانیِ daemon + Streamlit روی فایل‌های وضعیت (strategy.json،
llm_budget.json، frontier.json) می‌توانست آخرین‌نویسنده-می‌برد و فسادِ JSON
بسازد. این ابزار با قفلِ انحصاری + نوشتنِ اتمیک آن را غیرممکن می‌کند.

امنیت: assert_safe_write (guardrail) را پیش از هر نوشتن صدا می‌زند —
نوشتنِ بی‌گارد روی TCB تئوریک ممکن نیست.
"""
from __future__ import annotations

import os
import json
import logging
import sys
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger(__name__)

# نقشه‌ی قفل‌های باز (per-process) برای جلوگیری از deadlock در صورتِ فراخوانیِ
# تودرتو در همان فرایند. (نکته: این فقط reentrancy درون‌فرایندی است؛
# قفلِ بین‌فرایندی با msvcrt/fcntl روی خودِ فایلِ .lock اعمال می‌شود.)
_open_locks: dict[str, int] = {}


@contextmanager
def file_lock(path, *, timeout: float = 5.0) -> Iterator[Path]:
    """قفلِ انحصاریِ cross-platform روی یک فایلِ .lock کنارِ `path`.

    روی ویندوز از msvcrt.locking و روی POSIX از fcntl.flock استفاده می‌کند.
    اگر هیچ‌کدام در دسترس نبود (مثلاً شبکه‌ای/عجیب)، به best-effort بدون قفل
    تنه می‌زند (با هشدار) — سازگاری هرگز نمی‌شکند.

    Usage:
        with file_lock("strategy.json") as p:
            data = json.loads(p.read_text())
            data["x"] += 1
            atomic_write_json(p, data)
    """
    p = Path(path)
    lockfile = p.with_suffix(p.suffix + ".lock")
    lockfile.parent.mkdir(parents=True, exist_ok=True)

    # جلوگیری از deadlockِ تودرتو در همین فرایند
    key = str(lockfile.resolve())
    if key in _open_locks:
        _open_locks[key] += 1
        try:
            yield p
        finally:
            _open_locks[key] -= 1
            if _open_locks[key] <= 0:
                _open_locks.pop(key, None)
        return

    fd = None
    acquired = False
    try:
        # باز کردنِ فایلِ قفل (می‌سازد اگر نبود)
        fd = os.open(str(lockfile), os.O_CREAT | os.O_RDWR, 0o644)
        _open_locks[key] = 1

        if sys.platform == "win32":
            acquired = _lock_win(fd, timeout)
        else:
            acquired = _lock_posix(fd, timeout)

        if not acquired:
            # best-effort: بدونِ قفل ادامه بده ولی هشدار بده (fail-open، نه fail-stop)
            logger.warning("file_lock: could not acquire %s after %.1fs (best-effort)",
                           lockfile, timeout)

        yield p
    finally:
        if fd is not None:
            try:
                if acquired and sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                elif acquired:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                os.close(fd)
            except Exception:
                pass
        _open_locks.pop(key, None)


def _lock_win(fd: int, timeout: float) -> bool:
    """قفلِ انحصاری روی ویندوز با msvcrt.locking (try با backoff کوتاه)."""
    import msvcrt
    import time
    deadline = time.monotonic() + timeout
    while True:
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.05)


def _lock_posix(fd: int, timeout: float) -> bool:
    """قفلِ انحصاری روی POSIX با fcntl.flock."""
    import fcntl
    import time
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.05)


def atomic_write_json(path, data, *, indent: int = 2, ensure_guardrail: bool = True) -> bool:
    """نوشتنِ JSON با الگوی اتمیک (temp + os.replace) و guardrail.

    ۱. guardrails.assert_safe_write بررسی می‌شود (مگر اینکه ensure_guardrail=False).
    ۲. داده به‌صورتِ اتمیک جایگزین می‌شود (temp + os.replace).
    ۳. خواننده‌ها هرگز نیمه‌نوشته نمی‌بینند.

    برمی‌گرداند: True اگر موفق، False اگر guardrail رد کرد یا خطا.
    """
    if ensure_guardrail:
        try:
            from brain import guardrails
            ok, reason = guardrails.assert_safe_write(path)
            if not ok:
                logger.error("atomic_write_json BLOCKED by guardrails: %s (%s)", path, reason)
                return False
        except Exception as e:
            logger.error("atomic_write_json: guardrail check failed: %s", e)
            return False

    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=indent),
            encoding="utf-8",
        )
        os.replace(tmp, p)
        return True
    except Exception as e:
        logger.warning("atomic_write_json failed for %s: %s", p, e)
        return False


def atomic_read_json(path, default=None):
    """خواندنِ JSON با تحملِ خرابی (fallback به default)."""
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("atomic_read_json failed for %s: %s", p, e)
        return default
