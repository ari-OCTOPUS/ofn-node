#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runner_apply_gate.py — DW-01 / قدم ۵۲: فلگ مسلح ولی ماژول apply نبود.

این gate فقط وضعیت را صادق گزارش می‌کند. هیچ apply واقعی ندارد.
OCTOPUS_WIRE_RUNNER_APPLY=1 → armed_inert (نه «قابلیت کامل»).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_HERE / "state"))) / "runner-apply-status.json"


def flag_on() -> bool:
    return str(os.environ.get("OCTOPUS_WIRE_RUNNER_APPLY", "0")).strip().lower() in (
        "1", "true", "yes", "on",
    )


def status() -> dict:
    return {
        "schema": "runner-apply-gate.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "flag_on": flag_on(),
        "apply_module_present": False,
        "state": "armed_inert" if flag_on() else "disarmed",
        "may_authorize": False,
        "external_effect": False,
        "note": "هیچ caller تولیدی apply ندارد — فلگ روشن ≠ اجرا",
    }


def persist() -> dict:
    st = status()
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        tmp = OUT.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(OUT)
        st["persisted"] = True
    except OSError:
        st["persisted"] = False
    return st
