#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collab_digest.py — monitoring digest from live_snapshot (WP-E5).

flag: OCTOPUS_WIRE_COLLAB_DIGEST=0 (default OFF)
No scheduler, no send, no restart.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

SCHEMA = "CollabDigest.v1"


def _is_enabled() -> bool:
    return os.environ.get("OCTOPUS_WIRE_COLLAB_DIGEST", "0") == "1"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def build_digest(*, snapshot: dict | None = None) -> dict:
    """Build a monitoring-first digest from live_snapshot.

    Args:
        snapshot: pre-fetched snapshot dict (for testability).
                  If None, reads live_snapshot.snapshot().

    Returns digest with verified_changes, blockers, low_risk, critical, interrupt_affordance.
    """
    if snapshot is None:
        try:
            from control_plane import live_snapshot
            snapshot = live_snapshot.snapshot()
        except Exception as e:  # noqa: BLE001
            return {
                "schema": SCHEMA,
                "ts": _utc_iso(),
                "status": "UNKNOWN",
                "reason": f"snapshot read failed: {type(e).__name__}",
                "blockers": ["snapshot-unavailable"],
            }

    blockers = []
    verified_changes = []
    low_risk = []
    critical = []

    # Extract blockers from snapshot health section
    health = snapshot.get("health") or {}
    if isinstance(health, dict):
        for key, val in health.items():
            if isinstance(val, str) and val:
                blockers.append(f"{key}: {val}")
            elif isinstance(val, dict):
                blk = val.get("blockers") or val.get("blocker")
                if blk:
                    blockers.append(f"{key}: {blk}")

    # Extract verified changes from organism section
    org = snapshot.get("organism") or {}
    if isinstance(org, dict):
        beat = org.get("beat")
        if beat is not None:
            verified_changes.append(f"organism beat={beat}")
        halted = org.get("halted")
        frozen = org.get("frozen")
        if halted or frozen:
            critical.append(f"organism {'halted' if halted else 'frozen'}")

    # Extract from flags section
    flags = snapshot.get("flags") or {}
    if isinstance(flags, dict):
        n_armed = sum(1 for v in flags.values() if str(v) == "1")
        verified_changes.append(f"{n_armed} flags armed")

    # Interrupt affordance: only if critical items exist
    interrupt = bool(critical)

    return {
        "schema": SCHEMA,
        "ts": _utc_iso(),
        "status": "CRITICAL" if critical else ("ALERT" if blockers else "OK"),
        "verified_changes": verified_changes,
        "blockers": blockers,
        "low_risk_completed": low_risk,
        "critical": critical,
        "interrupt_affordance": interrupt,
        "note": "Monitoring-first digest. Interrupt = proposal only, never auto-action.",
    }


if __name__ == "__main__":
    import json
    d = build_digest()
    print(json.dumps(d, ensure_ascii=False, indent=2))
