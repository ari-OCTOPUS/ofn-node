# -*- coding: utf-8 -*-
"""Memory continuity: 10 consecutive healthy cycles. Does not activate Wave 1."""
from __future__ import annotations

import json
from datetime import datetime, timezone
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

    Unique increasing `beat` identities are required when present. Integer
    gaps do not reset the streak: live organism beat is not unit-increment.
    A non-increasing beat or an unhealthy sample resets.
    """
    n = 0
    prev_beat = None
    for s in reversed(samples):
        if not cycle_healthy(s):
            break
        b = s.get("beat")
        if prev_beat is not None and b is not None:
            try:
                if int(b) >= int(prev_beat):
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


def cycle_receipt(sample: dict) -> str | None:
    existing = sample.get("cycle_receipt")
    if existing:
        return str(existing)
    if sample.get("observed_at") is None or sample.get("beat") is None:
        return None
    return f"memory-obs:{sample.get('beat')}:{sample.get('observed_at')}"


def audit(latest: dict | None, history_jsonl: Path | None = None) -> dict[str, Any]:
    samples = load_samples(history_jsonl) if history_jsonl else []
    samples = [s for s in samples if s.get("observed_at")]
    if latest:
        if not samples or samples[-1].get("beat") != latest.get("beat"):
            extra = dict(latest)
            extra.setdefault(
                "observed_at",
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            samples = samples + [extra]
    streak = consecutive_healthy(samples)
    trailing = samples[-streak:] if streak else []
    receipts = [cycle_receipt(s) for s in trailing]
    beats = [s.get("beat") for s in trailing]
    return {
        "schema": "memory-continuity/2",
        "samples": len(samples),
        "consecutive_healthy": streak,
        "threshold": THRESHOLD,
        "gate_met": streak >= THRESHOLD,
        "latest_healthy": cycle_healthy(latest) if latest else False,
        "unique_cycle_identities": len(set(filter(None, receipts))) == len(trailing) and streak > 0,
        "trailing_beats": beats,
        "trailing_cycle_receipts": receipts,
        "heartbeat": {
            "status": (latest or {}).get("status"),
            "readback": (latest or {}).get("readback"),
            "executable": (latest or {}).get("executable"),
            "reads_per_cycle": (latest or {}).get("memory_reads_per_cycle"),
        },
        "note": "Wave 1 memory-read activation remains locked until WAVE0_PASS",
    }
