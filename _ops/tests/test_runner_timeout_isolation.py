#!/usr/bin/env python3
"""Lane E — a per-file timeout must not leave remaining suites unexecuted."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))


def _load_run_all():
    spec = importlib.util.spec_from_file_location("run_all_under_test", _HERE / "run_all.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def t_a_timeout_is_isolated_and_returns_timed_out():
    m = _load_run_all()
    cmd = [sys.executable, "-c", "import time; time.sleep(30)"]
    res = m._run_one(cmd, str(_HERE), timeout=1, env=None)
    assert res["status"] == "TIMED_OUT", res
    assert res["exit"] is None
    assert "TIMED_OUT" in res["stderr"]


def t_b_after_timeout_the_next_suite_still_runs():
    m = _load_run_all()
    slow = [sys.executable, "-c", "import time; time.sleep(30)"]
    fast = [sys.executable, "-c", "print('fast-ok')"]
    first = m._run_one(slow, str(_HERE), timeout=1, env=None)
    second = m._run_one(fast, str(_HERE), timeout=5, env=None)
    assert first["status"] == "TIMED_OUT"
    assert second["status"] == "PASS", second
    assert "fast-ok" in second["stdout"]


def t_c_slow_timeout_map_contains_capability_registry():
    m = _load_run_all()
    assert m.DEFAULT_TIMEOUT == 300
    assert m.SLOW_TIMEOUTS.get("test_capability_registry.py", 0) >= 900


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_runner_timeout_isolation: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
