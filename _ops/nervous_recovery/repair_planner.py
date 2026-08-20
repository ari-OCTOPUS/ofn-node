# -*- coding: utf-8 -*-
"""Repair planner — DAG of bounded patches. Does not apply them."""
from __future__ import annotations

from typing import Any

# Rail A closes WAVE0_PARTIAL. Rail B is isolated. Rail C waits for WAVE0_PASS.
RAIL_A = [
    {"id": "A-receipt-v2", "depends_on": [], "applies": False,
     "desc": "Force receipt envelope v2; legacy adapter never fabricates task_id"},
    {"id": "A-test-discovery", "depends_on": [], "applies": False,
     "desc": "CI fails when discovered-registered > 0; do not silently edit run_all"},
    {"id": "A-capability-ast", "depends_on": [], "applies": False,
     "desc": "AST/YAML/JSON/TOML parser replaces regex inventory"},
    {"id": "A-memory-10-cycles", "depends_on": ["A-receipt-v2"], "applies": False,
     "desc": "10 consecutive healthy memory cycles; no Wave 1 activation here"},
    {"id": "A-controlled-restart", "depends_on": ["A-receipt-v2"], "applies": False,
     "owner_required": True,
     "desc": "After producers emit task_id, owner-approved restart of daemon/live/cortex"},
]
RAIL_B = [
    {"id": "S-B01", "depends_on": [], "applies": False, "owner_required": True,
     "desc": "Fugu quota honesty → DEGRADED_LOCAL_ONLY; no silent 1.5B fallback"},
    {"id": "S-B02", "depends_on": ["S-B01"], "applies": False, "owner_required": True,
     "desc": "FX-pin before cognitive expansion"},
    {"id": "S-B06", "depends_on": [], "applies": False, "owner_required": True,
     "desc": "RUN-ORGANISM.bat loop P1 — restart/watchdog tests first"},
    {"id": "S-D01", "depends_on": [], "applies": False,
     "desc": "doctor-pulse mission timeout → quarantine → replaceable mission"},
    {"id": "S-B05", "depends_on": [], "applies": False,
     "desc": "brain_core parity without baseline → NO_BASELINE, stop fake validation"},
]
RAIL_C = [
    {"id": "C-cal-improve", "depends_on": ["WAVE0_PASS"], "applies": False,
     "desc": "calibration-latest → improve.py (Brier, n, freshness, CI)"},
    {"id": "C-self-knowledge-ema", "depends_on": ["WAVE0_PASS"], "applies": False,
     "desc": "replace constant 0.4 with receipt-backed EMA"},
    {"id": "C-self-insight-shadow", "depends_on": ["WAVE0_PASS"], "applies": False,
     "desc": "weekly shadow self_insight evidence-only"},
    {"id": "C-cockpit-tiers", "depends_on": ["WAVE0_PASS"], "applies": False,
     "desc": "register self-knowledge-latest in cockpit _TIERS"},
]


def dag() -> dict[str, Any]:
    return {
        "schema": "repair-planner/1",
        "applies_patches": False,
        "wave1_unlocked": False,
        "rails": {"A": RAIL_A, "B": RAIL_B, "C": RAIL_C},
    }
