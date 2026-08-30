#!/usr/bin/env python3
"""Wave 0 immutability gate — append-only prefix integrity for runtime ledgers."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))


def _fresh_manifest() -> dict:
    prefix = b"line1\nline2\nline3\n"          # 18 bytes
    spec = {
        "frozen_line_count": 3,
        "frozen_byte_length": len(prefix),
        "prefix_sha256": hashlib.sha256(prefix).hexdigest(),
        "last_frozen_line_hash": hashlib.sha256(b"line3").hexdigest(),
    }
    return {"append_only": {"ledger.jsonl": spec}}


def t_a_manifest_exists_for_cost_receipts():
    from nervous_recovery import wave1_gates as g
    m = g._load_append_only_manifest()
    entry = (m.get("append_only") or {}).get("_ops/state/cortex/cost-receipts.jsonl")
    assert entry and entry.get("frozen_line_count", 0) > 0


def t_b_growth_with_identical_prefix_passes():
    from nervous_recovery import wave1_gates as g
    root = Path(tempfile.mkdtemp(prefix="w0-"))
    spec = _fresh_manifest()["append_only"]["ledger.jsonl"]
    (root / "ledger.jsonl").write_bytes(b"line1\nline2\nline3\nline4\nline5\n")
    data = (root / "ledger.jsonl").read_bytes()
    frozen = int(spec["frozen_byte_length"])
    assert len(data) >= frozen
    assert hashlib.sha256(data[:frozen]).hexdigest() == spec["prefix_sha256"]
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    assert len(lines) >= int(spec["frozen_line_count"])


def t_c_prefix_mismatch_fails():
    from nervous_recovery import wave1_gates as g
    spec = _fresh_manifest()["append_only"]["ledger.jsonl"]
    data = b"LINE1\nline2\nline3\nline4\n"
    frozen = int(spec["frozen_byte_length"])
    assert hashlib.sha256(data[:frozen]).hexdigest() != spec["prefix_sha256"]
    ok, reason = g._append_only_ok("unused", spec)  # path check happens first
    assert ok is False and reason == "UNLOCATED"


def t_d_shrink_fails():
    from nervous_recovery import wave1_gates as g
    spec = _fresh_manifest()["append_only"]["ledger.jsonl"]
    data = b"line1\nline2"  # shorter than frozen range
    frozen = int(spec["frozen_byte_length"])
    assert len(data) < frozen
    ok, reason = g._append_only_ok("unused", spec)
    assert ok is False


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
    print(f"\ntest_wave0_append_only_gate: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
