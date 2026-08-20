# -*- coding: utf-8 -*-
"""Observe existing memory-read ticks. Does not activate Wave 1 or new writers."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
MEM = _OPS / "state" / "pulse" / "memory-read-latest.json"
OUT = _OPS.parent / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20" / "memory-continuity.jsonl"


def _beat(sample: dict):
    return sample.get("beat")


def once() -> dict | None:
    if not MEM.exists():
        return None
    try:
        return json.loads(MEM.read_text(encoding="utf-8"))
    except ValueError:
        return None


def append_unique(sample: dict) -> bool:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            try:
                seen.add(_beat(json.loads(line)))
            except ValueError:
                continue
    b = _beat(sample)
    if b in seen:
        return False
    rec = dict(sample)
            rec["cycle_receipt"] = f"memory-obs:{b}:{rec['observed_at']}"
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return True


if __name__ == "__main__":
    # Poll until 12 unique beats or 40 minutes.
    deadline = time.time() + 40 * 60
    last = None
    while time.time() < deadline:
        s = once()
        if s and _beat(s) != last:
            if append_unique(s):
                last = _beat(s)
                print("appended beat", last, s.get("readback"), s.get("memory_reads_per_cycle"))
        time.sleep(20)
