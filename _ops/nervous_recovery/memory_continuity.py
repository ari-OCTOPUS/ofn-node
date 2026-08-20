# -*- coding: utf-8 -*-
"""Memory continuity: 10 consecutive healthy cycles. Does not activate Wave 1."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

THRESHOLD = 10


def cycle_healthy(sample: dict) -> bool:
    reads = sample.get("memory_reads_per_cycle")
    try:
        n = int(reads)
    except (TypeError, ValueError):
        return False
    return (
        n >= 3
        and str(sample.get("readback") or "") == "read_ok"
        and str(sample.get("status") or "").upper() in ("OK", "PASS")
        and sample.get("executable") is not True
    )


def consecutive_healthy(samples: list[dict]) -> int:
    """Count trailing consecutive healthy samples (not a sum of reads).

    If `beat` is present, a skipped beat identity resets the streak.
    """
    n = 0
    prev_beat = None
    for s in reversed(samples):
        if not cycle_healthy(s):
            break
        b = s.get("beat")
        if prev_beat is not None and b is not None:
            try:
                if int(prev_beat) != int(b) + 1:
                    break
            except (TypeError, ValueError):
                break
        n += 1
        prev_beat = b
    return n


def load_samples(jsonl: Path) -> list[dict]:
    rows: list[dict] = []
    if not jsonl.exists():
        return rows
    with jsonl.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def append_sample(jsonl: Path, sample: dict) -> None:
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    with jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")


def audit(latest: dict | None, history_jsonl: Path | None = None) -> dict[str, Any]:
    samples = load_samples(history_jsonl) if history_jsonl else []
    if latest:
        if not samples or samples[-1].get("beat") != latest.get("beat"):
            samples = samples + [latest]
    streak = consecutive_healthy(samples)
    return {
        "schema": "memory-continuity/1",
        "samples": len(samples),
        "consecutive_healthy": streak,
        "threshold": THRESHOLD,
        "gate_met": streak >= THRESHOLD,
        "latest_healthy": cycle_healthy(latest) if latest else False,
        "note": "Wave 1 memory-read activation remains locked until WAVE0_PASS",
    }
