"""state.py — اسکیمای MINING-STATE.json + load/save اتمیک و fail-soft.

این اسکیما جایگزینِ مسیرِ منجمد/شکستهٔ ``org['mining']`` است (رجوع: تناقضِ C13 و طرحِ B3).
هدف: یک منبعِ حقیقتِ runtime که leg و تلگرام هر دو از آن بخوانند.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def empty_state() -> dict:
    """اسکیمای canonical — همه‌چیز خالی/نامعلوم (honest by default)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "generated": _now(),
        "phase": "P0",
        "fleet": {"nodes": [], "electricity_price_kwh": None, "solar": False},
        "coins": {"candidates": []},
        "verdicts": [],
        "blockers": [],
    }


def load_state(path) -> dict | None:
    """خواندنِ state؛ در نبود/خرابی → None (fail-soft، بدونِ crash)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def save_state(path, state: dict) -> bool:
    """نوشتنِ اتمیک؛ در مسیرِ غیرقابل‌نوشت fail-soft → False (نامتغیرِ سندباکس)."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, str(p))
        return True
    except OSError:
        return False
