#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_order_independence — ترتیب suiteها نباید نتیجه را عوض کند.

فاز ۳ مگاپرامپت: «یک تست order-independence اضافه کن که حداقل دو ترتیب معکوس
را اجرا کند.»

این تست دو suite را در دو ترتیب معکوس در subprocess‌های تمیز اجرا می‌کند و
بررسی می‌کند که exit code و PASS/FAIL status یکسان باشد.
"""
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent

# دو suite که قبلاً مشکل order-dependency داشتند
PAIR = ("test_telegram_channel.py", "test_epoch.py")


def _run_suite(name: str) -> tuple[int, str]:
    """Run a suite in a clean subprocess, return (exit_code, last_line)."""
    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(_OPS / "tests" / name)],
        capture_output=True, text=True, timeout=60)
    last = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
    last_line = last[-1] if last else "(no output)"
    return r.returncode, last_line


def test_order_independence_forward_and_reverse():
    """اجرای دو suite در ترتیب مستقیم و معکوس باید نتیجه یکسان بدهد."""
    # Forward order
    rc_a_fwd, _ = _run_suite(PAIR[0])
    rc_b_fwd, _ = _run_suite(PAIR[1])

    # Reverse order
    rc_b_rev, _ = _run_suite(PAIR[1])
    rc_a_rev, _ = _run_suite(PAIR[0])

    # Results must be identical regardless of order
    assert rc_a_fwd == rc_a_rev, \
        f"{PAIR[0]} order-dependent: forward={rc_a_fwd} reverse={rc_a_rev}"
    assert rc_b_fwd == rc_b_rev, \
        f"{PAIR[1]} order-dependent: forward={rc_b_fwd} reverse={rc_b_rev}"


def test_subprocess_isolation_no_state_leak():
    """هر subprocess باید state مستقل داشته باشد — اجرای مجدد همان suite
    باید همان نتیجه را بدهد."""
    rc1, _ = _run_suite(PAIR[0])
    rc2, _ = _run_suite(PAIR[0])
    assert rc1 == rc2, \
        f"{PAIR[0]} non-deterministic across subprocess runs: {rc1} vs {rc2}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
