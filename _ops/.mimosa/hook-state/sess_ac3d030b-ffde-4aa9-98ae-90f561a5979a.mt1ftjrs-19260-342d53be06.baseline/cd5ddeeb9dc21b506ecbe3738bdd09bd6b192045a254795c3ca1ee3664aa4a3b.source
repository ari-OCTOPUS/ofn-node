#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""money_caps_snapshot.py — ماتریس سقف خرج برای MiniApp (قدم ۵/۷).

read-only · may_authorize=false · هیچ claim جعلی.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
STATE = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_HERE / "state")))


def snapshot() -> dict:
    until = str(os.environ.get("OCTOPUS_SPEND_CAP_UNTIL") or "").strip()
    usd = str(os.environ.get("OCTOPUS_SPEND_CAP_USD") or "").strip()
    today = date.today().isoformat()
    window_active = False
    days_left = None
    try:
        if until:
            d_until = datetime.strptime(until[:10], "%Y-%m-%d").date()
            days_left = (d_until - date.today()).days
            window_active = days_left >= 0 and bool(usd)
    except ValueError:
        window_active = False

    spend = None
    try:
        import sys
        scripts = str(_HERE.parent / "04 - Architect System" / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        import budget_gate as bg  # noqa: WPS433
        if hasattr(bg, "spend_cap_now"):
            spend = bg.spend_cap_now(30.0, 1.5, 500.0, today=today)
    except Exception as exc:  # noqa: BLE001
        spend = {"error": type(exc).__name__}

    flags = {
        "VALUE_LEDGER": os.environ.get("OCTOPUS_WIRE_VALUE_LEDGER", "0"),
        "MONEY_FSM": os.environ.get("OCTOPUS_ENFORCE_MONEY_FSM", "0"),
        "UNCAPPED": os.environ.get("OCTOPUS_INITIATIVE_UNCAPPED", "0"),
        "LIVE_ENABLED": (STATE / "LIVE-ENABLED.flag").exists(),
    }
    fitness = {}
    try:
        fp = STATE / "fitness-latest.json"
        if fp.is_file():
            fitness = json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        fitness = {}

    claimed = None
    try:
        claimed = ((fitness.get("attribution") or {}).get("claimed")
                   if isinstance(fitness, dict) else None)
        if claimed is None and isinstance(fitness, dict):
            claimed = fitness.get("claimed")
    except Exception:
        claimed = None

    return {
        "schema": "money-caps.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "may_authorize": False,
        "external_effect": False,
        "monthly_default_aud": 30,
        "daily_aud": 2,
        "disaster_aud": 500,
        "window": {
            "usd": usd or None,
            "until": until or None,
            "active": window_active,
            "days_left": days_left,
            "note": "پس از until سقف AU$30 خودکار برمی‌گردد مگر رأی تازه",
        },
        "spend_cap_now": spend,
        "flags_armed": flags,
        "armed_ne_productive": True,
        "claimed": claimed,
        "claimed_is_income": False,
        "blocker": "lead 667951 SET_ASIDE by owner 2026-08-12 — need new real lead for claimed; see lead-set-aside/",
        "sot": "_ops/docs/MONEY-CLAIM-VS-CONFIRM.md",
    }
