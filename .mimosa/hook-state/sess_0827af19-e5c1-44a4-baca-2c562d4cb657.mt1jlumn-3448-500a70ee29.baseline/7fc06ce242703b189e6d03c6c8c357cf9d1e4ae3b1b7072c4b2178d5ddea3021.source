#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_beat.py — fail-soft tick hook for seed/* (DW-02).

organism هر N beat صدا می‌زند. هیچ اثر بیرونی. فقط گزارش در state/seed/.
پشت فلگ‌های موجود SEED_ASSEMBLER / EVOLUTION_GATE.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SEED = _HERE / "seed"
STATE = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_HERE / "state"))) / "seed"
OUT = STATE / "beat-latest.json"


def _flag(name: str) -> bool:
    return str(os.environ.get(name, "0")).strip().lower() in ("1", "true", "yes", "on")


def tick(beat: int = 0) -> dict:
    """هر ۱۷ beat: snapshot reader؛ هر ۲۳ beat: evolution health. fail-soft."""
    out: dict = {
        "schema": "seed-beat.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "beat": int(beat or 0),
        "may_authorize": False,
        "external_effect": False,
    }
    if str(_SEED) not in sys.path:
        sys.path.insert(0, str(_SEED))
    b = int(beat or 0)
    try:
        if _flag("OCTOPUS_WIRE_SEED_ASSEMBLER") and b % 17 == 0:
            import octopus_reader as _or  # noqa: WPS433
            snap = _or.read_snapshot()
            out["assembler"] = {
                "status": (snap or {}).get("status") if isinstance(snap, dict) else "ok",
                "keys": list(snap.keys())[:8] if isinstance(snap, dict) else [],
            }
    except Exception as exc:  # noqa: BLE001
        out["assembler"] = {"error": type(exc).__name__}
    try:
        if _flag("OCTOPUS_WIRE_EVOLUTION_GATE") and b % 23 == 0:
            from evolution_gate import health_metrics  # noqa: WPS433
            out["evolution"] = health_metrics()
    except Exception as exc:  # noqa: BLE001
        out["evolution"] = {"error": type(exc).__name__}
    try:
        STATE.mkdir(parents=True, exist_ok=True)
        tmp = OUT.with_suffix(".tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(OUT)
        out["persisted"] = True
    except OSError:
        out["persisted"] = False
    return out
