#!/usr/bin/env python3
"""Item 20 — dark_capabilities.scan() must be TTL-cached (render was ~7.8s each)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))


def _tiny_root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="dark-cap-"))
    (root / "a.py").write_text(
        "import os\nX = os.environ.get('OCTOPUS_TEST_FLAG', '0')\n", encoding="utf-8")
    return root


def t_a_scan_is_cached_within_ttl():
    import dark_capabilities as dc
    root = _tiny_root()
    dc._CACHE.update(ts=0.0, result=None)
    calls = []
    orig = dc._flags_read_by

    def spy(f):
        calls.append(f)
        return orig(f)

    dc._flags_read_by = spy
    try:
        r1 = dc.scan(root)
        n1 = len(calls)
        r2 = dc.scan(root)
        n2 = len(calls)
    finally:
        dc._flags_read_by = orig
    assert isinstance(r1, dict) and r2 is r1, "cache must return the same result"
    assert n2 == n1, f"scan re-ran: calls {n1} -> {n2}"


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
    print(f"\ntest_dark_capabilities_cache: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
